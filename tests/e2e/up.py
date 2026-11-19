"""Start a local forge with its runner, and the admin token the tests use.

Usage: up.py <gitea|forgejo|gitlab>, or up.py down: removes them all with
their data, then everything Docker no longer uses (docker system prune). Starts tests/fixtures/<forge>/compose.yml, waits until it
answers, creates the admin and a token, registers the runner, and writes
.forges/<forge>.json. Run again, it reuses a forge that is up. The tests call
ensure() themselves: running up.py is only needed to open a forge's UI.
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # brigade's checkout
FIXTURES = ROOT / "tests" / "fixtures"
STATE = ROOT / ".forges"
# brigade at its tags (the tests' templates): outside the checkout, whose
# linters would read them; mounted in the jobs too (BRIGADE_TEMPLATES).
TEMPLATES = Path("/tmp/brigade-forges").resolve()
SERVERS = ("gitea", "forgejo", "gitlab")
# The admin, its password, and the API as seen from this machine.
USER = {"gitea": "brigade", "forgejo": "brigade", "gitlab": "root"}
URL = {
    "gitea": "http://localhost:3001",
    "forgejo": "http://localhost:3002",
    "gitlab": "http://localhost:8929",
}
PASSWORD = "brigade-local-forges-1"
RUNNER_SECRET = "0123456789abcdef0123456789abcdef01234567"  # forgejo/compose.yml, a dummy  # gitleaks:allow


def compose(server: str, *args: str, stdin: str | None = None) -> str:
    """docker compose on the server's file; its stdout."""
    command = ["docker", "compose", "-f", str(FIXTURES / server / "compose.yml")]
    result = subprocess.run(
        [*command, *args],
        input=stdin,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "BRIGADE_SRC": str(ROOT),
            "BRIGADE_TEMPLATES": str(TEMPLATES),
        },
        check=False,
    )
    if result.returncode:
        sys.exit(f"docker compose {' '.join(args)}:\n{result.stderr[-2000:]}")
    return result.stdout


def shell(server: str, service: str, script: str, user: str = "root", stdin=None):
    """A shell script in a running service; its stdout's last line."""
    out = compose(
        server, "exec", "-T", "-u", user, service, "sh", "-c", script, stdin=stdin
    )
    return out.strip().splitlines()[-1]


def works(server: str, token: str) -> bool:
    """The token still opens the API (the forge is up, its data kept)."""
    header = {"gitlab": "PRIVATE-TOKEN"}.get(server, "Authorization")
    value = token if server == "gitlab" else f"token {token}"
    root = "/api/v4" if server == "gitlab" else "/api/v1"
    request = urllib.request.Request(
        f"{URL[server]}{root}/user", headers={header: value}
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            return True
    except OSError:
        return False


def ensure(server: str) -> dict:
    """The forge up, with its runner; returns {url, user, token}."""
    TEMPLATES.mkdir(exist_ok=True)
    saved = STATE / f"{server}.json"
    if saved.exists():
        forge = json.loads(saved.read_text())
        if works(server, forge["token"]):
            # Seeded: the runner recreated, for changes to its config (compose
            # does not see them); GitLab's is registered in seed() only.
            if server != "gitlab":
                compose(server, "up", "-d", "--force-recreate", f"{server}-runner")
            return forge
    print(f"starting {server} (GitLab: a few minutes)...", flush=True)
    compose(server, "up", "-d", "--wait")
    forge = {"url": URL[server], "user": USER[server], "token": seed(server)}
    STATE.mkdir(exist_ok=True)
    saved.write_text(json.dumps(forge))
    return forge


def reset_registries(server: str) -> None:
    """Empty registries: new containers, new anonymous volumes (their images')."""
    registries = ["pypi", "verdaccio", "registry"]
    compose(
        server,
        "up",
        "-d",
        "--wait",
        "--force-recreate",
        "--renew-anon-volumes",
        *registries,
    )


def seed(server: str) -> str:
    """The admin's token; the runner registered and started."""
    if server in ("gitea", "forgejo"):
        token = shell(
            server,
            server,
            f"{server} admin user create --admin --username {USER[server]}"
            f" --password {PASSWORD} --email brigade@example.com"
            " --must-change-password=false >/dev/null 2>&1;"
            f" {server} admin user generate-access-token --username {USER[server]}"
            ' --token-name "tests-$(date +%s)" --scopes all --raw',
            user="git",
        )
        if server == "forgejo":
            shell(
                server,
                server,
                f"forgejo forgejo-cli actions register --name local --secret"
                f" {RUNNER_SECRET} >/dev/null; echo ok",
                user="git",
            )
            compose(server, "up", "-d", "forgejo-runner")
        return token  # gitea's runner registers itself (compose.yml)
    # GitLab: a token for root, and an instance runner with docker.
    ruby = """
u = User.find_by_username('root')
t = u.personal_access_tokens.create!(
    name: "tests-#{Time.now.to_i}", expires_at: 30.days.from_now,
    scopes: [:api, :read_repository, :write_repository])
r = Ci::Runners::CreateRunnerService.new(user: u, params: {
    runner_type: 'instance_type', run_untagged: true, description: 'local'
}).execute.payload[:runner]
puts "#{t.token} #{r.token}"
"""
    script = "cat > /tmp/seed.rb && gitlab-rails runner /tmp/seed.rb"
    token, runner = shell(server, "gitlab-app", script, stdin=ruby).split()
    # One runner: those of earlier seeds, still in the volume, would take jobs.
    compose(server, "run", "--rm", "gitlab-runner", "unregister", "--all-runners")
    compose(
        server, "run", "--rm", "gitlab-runner", "register", "--non-interactive",
        "--url", "http://gitlab", "--token", runner, "--executor", "docker",
        "--docker-image", "alpine:3.22", "--docker-network-mode", "brigade-forges",
        "--clone-url", "http://gitlab",
        "--docker-volumes", f"{ROOT}:{ROOT}:ro",
        "--docker-volumes", f"{TEMPLATES}:{TEMPLATES}:ro",
        "--docker-volumes", "/var/run/docker.sock:/var/run/docker.sock",
        "--docker-volumes", "brigade-forges_gitlab-certs:/certs:ro",
        "--env", "SSL_CERT_FILE=/certs/bundle.pem",
    )  # fmt: skip
    compose(server, "up", "-d", "gitlab-runner")
    return token


def docker(*args: str) -> list[str]:
    """A docker command's output, as words; failures ignored (nothing to clean)."""
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=False
    )
    return result.stdout.split()


def down() -> None:
    """The forges and their data, then all Docker no longer uses (a dev machine:
    images are pulled again when needed)."""
    for server in SERVERS:
        compose(server, "--profile", "runner", "down", "--volumes", "--remove-orphans")
        (STATE / f"{server}.json").unlink(missing_ok=True)
    # Stopped containers (the jobs'), unused images, networks, build cache and
    # anonymous volumes; then the forges' volumes a job container still held.
    docker("system", "prune", "--all", "--force", "--volumes")
    if volumes := docker("volume", "ls", "-q", "--filter", "name=brigade-forges_"):
        docker("volume", "rm", "-f", *volumes)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["down"]:
        down()
    elif len(args) == 1 and args[0] in SERVERS:
        forge = ensure(args[0])
        print(f"{forge['url']}: {forge['user']} / {PASSWORD}")
    else:
        sys.exit(f"usage: up.py <{'|'.join(SERVERS)}|down>")
