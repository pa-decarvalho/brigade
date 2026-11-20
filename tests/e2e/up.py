"""A local forge for the end-to-end tests: up, run, test, down.

Usage: up.py <forge> <action> [type...], forge gitea, forgejo, gitlab or
github (a ci: github project on Gitea, the same server), as mise's <forge>:<action>
tasks run it:
- up: starts tests/fixtures/<server>/compose.yml, waits until it answers,
    creates the admin and a token, registers the runner, writes
    .forges/<server>.json; reuses a forge that is up;
- run: the tests on it, all or the given ids of projects.CASES;
- down: removes the forge and its data, then everything Docker no longer
    uses, Docker-wide (containers, images, networks, build cache, volumes);
- test: up, run, then down, even when the tests fail.
The tests call ensure() themselves: run starts a forge that is not up.
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from projects import CASES

ROOT = Path(__file__).resolve().parents[2]  # brigade's checkout
FIXTURES = ROOT / "tests" / "fixtures"
STATE = ROOT / ".forges"
# brigade at its tags (the tests' templates): outside the checkout, whose
# linters would read them; mounted in the jobs too (BRIGADE_TEMPLATES).
TEMPLATES = Path("/tmp/brigade-forges").resolve()
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
    token, runner = shell(server, "gitlab", script, stdin=ruby).split()
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
    )  # fmt: skip
    compose(server, "up", "-d", "gitlab-runner")
    return token


def docker(*args: str) -> list[str]:
    """A docker command's output, as words; failures ignored (nothing to clean)."""
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=False
    )
    return result.stdout.split()


def down(server: str) -> None:
    """The forge and its data, then all Docker no longer uses (a dev machine:
    images are pulled again when needed)."""
    compose(server, "--profile", "runner", "down", "--volumes", "--remove-orphans")
    (STATE / f"{server}.json").unlink(missing_ok=True)
    shutil.rmtree(TEMPLATES, ignore_errors=True)
    # Stopped containers (the jobs'), unused images, networks, build cache, then
    # every unused volume, named ones included (the runners' caches).
    docker("system", "prune", "--all", "--force")
    docker("volume", "prune", "--all", "--force")


def run(forge: str, types: list[str]) -> int:
    """pytest on the forge, for the given test ids (all when none); its exit code."""
    unknown = set(types) - set(CASES)
    if unknown:
        sys.exit(f"unknown types {sorted(unknown)}: {', '.join(CASES)}")
    test = ROOT / "tests/e2e/test_projects.py"
    targets = [f"{test}::test_project[{t}]" for t in types] or [str(test)]
    pytest = [
        "uv",
        "run",
        "--no-project",
        "--python",
        "3.14",
        "--with",
        "pytest==9.2.0",
    ]
    pytest += ["pytest", *targets, "--forge", forge, "-p", "no:cacheprovider", "-v"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.call(pytest, cwd=ROOT, env=env)


FORGES = {"gitea": "gitea", "github": "gitea", "forgejo": "forgejo", "gitlab": "gitlab"}
ACTIONS = ("up", "run", "down", "test")


def main(args: list[str]) -> int:
    if len(args) < 2 or args[0] not in FORGES or args[1] not in ACTIONS:
        sys.exit(f"usage: up.py <{'|'.join(FORGES)}> <{'|'.join(ACTIONS)}> [type...]")
    forge, action, types = args[0], args[1], args[2:]
    server = FORGES[forge]
    if action == "up":
        found = ensure(server)
        print(f"{found['url']}: {found['user']} / {PASSWORD}")
        return 0
    if action == "run":
        return run(forge, types)
    if action == "down":
        down(server)
        return 0
    ensure(server)
    try:
        return run(forge, types)
    finally:
        down(server)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
