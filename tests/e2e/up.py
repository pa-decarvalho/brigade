"""The local forges and what they need: up, reset, down, clean.

tests/fixtures/<server>/compose.yml: the forge and its runner, Nexus (publish),
k3s (profile cluster) and an SSH server (profile ssh); phases.py runs them.
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # brigade's checkout
FIXTURES = ROOT / "tests" / "fixtures"
STATE = ROOT / ".forges"
# brigade at its tags (the tests' templates): outside the checkout, whose
# linters would read them; mounted in the jobs too (BRIGADE_TEMPLATES).
TEMPLATES = Path("/tmp/brigade-forges").resolve()
WORK = TEMPLATES / "projects"  # the test projects (phases.Scenario)
# The admin, its password, and the API as seen from this machine.
USER = {"gitea": "brigade", "forgejo": "brigade", "gitlab": "root"}
URL = {
    "gitea": "http://localhost:3001",
    "forgejo": "http://localhost:3002",
    "gitlab": "http://localhost:8929",
}
PASSWORD = "brigade-local-forges-1"
RUNNER_SECRET = "0123456789abcdef0123456789abcdef01234567"  # forgejo/compose.yml, a dummy  # gitleaks:allow
# Nexus (tests/fixtures/compose.yml) from this machine, its deploy user and
# password, and its repositories by name (their format), emptied before each test.
NEXUS = "http://localhost:8099"
DEPLOY = ("deploy", "brigade-deploy-1")
REPOSITORIES = {
    "pypi": {},
    "npm": {},
    "docker": {
        "docker": {"v1Enabled": False, "forceBasicAuth": False, "httpPort": 5000}
    },
    "maven": {"maven": {"versionPolicy": "RELEASE", "layoutPolicy": "STRICT"}},
}


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


def nexus(method: str, path: str, body=None, auth=("admin", PASSWORD)):
    """A call to Nexus as admin (a str body as text); its JSON, None when empty
    or absent (404). Retried on 401 and 429: a new admin password takes a moment."""
    text = isinstance(body, str)
    data = None if body is None else (body if text else json.dumps(body)).encode()
    request = urllib.request.Request(f"{NEXUS}{path}", data=data, method=method)
    request.add_header("Content-Type", "text/plain" if text else "application/json")
    if auth:
        basic = base64.b64encode(":".join(auth).encode()).decode()
        request.add_header("Authorization", f"Basic {basic}")
    for attempt in range(30):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                answer = response.read()
            return json.loads(answer) if answer else None
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code not in (401, 429) or attempt == 29:
                sys.exit(f"nexus {method} {path}: {error.code} {error.read()[:500]!r}")
            time.sleep(2)


def reset_registries(server: str) -> dict:
    """Nexus set up on first use, its repositories emptied (each run publishes
    demo's 0.1.0 again); the deploys' secrets, for projects.Project.secrets."""
    compose(server, "up", "-d", "--wait", "nexus")  # a forge up before Nexus
    api = "/service/rest/v1"
    # Only a new Nexus has it (a setup cut short: down, then up again).
    initial = compose(
        server,
        "exec",
        "-T",
        "nexus",
        "sh",
        "-c",
        "cat /nexus-data/admin.password || true",
    ).strip()
    if initial:
        change = f"{api}/security/users/admin/change-password"
        nexus("PUT", change, PASSWORD, auth=("admin", initial))
        nexus(
            "POST",
            f"{api}/system/eula",
            {**nexus("GET", f"{api}/system/eula"), "accepted": True},
        )
        anonymous = {
            "enabled": True,
            "userId": "anonymous",
            "realmName": "NexusAuthorizingRealm",
        }
        nexus("PUT", f"{api}/security/anonymous", anonymous)  # the deployed checks
        realms = ["NexusAuthenticatingRealm", "NpmToken", "DockerToken"]
        nexus("PUT", f"{api}/security/realms/active", realms)
        role = {
            "id": "deploy",
            "name": "deploy",
            "description": "Deploys",
            "privileges": ["nx-repository-view-*-*-*"],
            "roles": [],
        }
        nexus("POST", f"{api}/security/roles", role)
        user = {
            "userId": DEPLOY[0],
            "firstName": "deploy",
            "lastName": "deploy",
            "emailAddress": "deploy@example.com",
            "password": DEPLOY[1],
            "status": "active",
            "roles": ["deploy"],
        }
        nexus("POST", f"{api}/security/users", user)
    storage = {
        "blobStoreName": "default",
        "strictContentTypeValidation": True,
        "writePolicy": "allow_once",
    }
    for name, settings in REPOSITORIES.items():
        nexus("DELETE", f"{api}/repositories/{name}")
        repository = {"name": name, "online": True, "storage": storage, **settings}
        nexus("POST", f"{api}/repositories/{name}/hosted", repository)
    login = {"name": DEPLOY[0], "password": DEPLOY[1]}
    npm = nexus(
        "PUT", f"/repository/npm/-/user/org.couchdb.user:{DEPLOY[0]}", login, auth=None
    )
    return {
        "deploy_user": DEPLOY[0],
        "deploy_password": DEPLOY[1],
        "npm_token": npm["token"],
    }


# The namespaces the tests' deploys install into (projects.Project.cluster).
NAMESPACES = ("dev", "prod")


def kubectl(server: str, *args: str) -> str:
    """kubectl in the cluster; its stdout."""
    return compose(server, "exec", "-T", "k3s", "kubectl", *args)


def reset_cluster(server: str) -> str:
    """k3s started, the tests' namespaces deleted; its kubeconfig as the jobs
    reach it (https://k3s:6443), for projects.Project.secrets ("{kubeconfig}")."""
    compose(server, "--profile", "cluster", "up", "-d", "--wait", "k3s")
    kubectl(server, "delete", "namespace", *NAMESPACES, "--ignore-not-found")
    config = compose(server, "exec", "-T", "k3s", "cat", "/etc/rancher/k3s/k3s.yaml")
    return config.replace("https://127.0.0.1:6443", "https://k3s:6443")


def reset_ssh_target(server: str) -> str:
    """The SSH server started, its key replaced and /srv emptied; the private
    key, for projects.Project.secrets ("{ssh_private_key}")."""
    compose(server, "--profile", "ssh", "up", "-d", "--wait", "ssh-target")
    with tempfile.TemporaryDirectory() as tmp:
        key = Path(tmp, "key")
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "brigade-e2e"]
            + ["-f", str(key)],
            check=True,
        )
        script = (
            "cat > /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys"
            " && rm -rf /srv/*"
        )
        compose(
            server,
            "exec",
            "-T",
            "ssh-target",
            "sh",
            "-c",
            script,
            stdin=Path(f"{key}.pub").read_text(),
        )
        return key.read_text()


def ssh_target(server: str, *command: str) -> str:
    """A command on the SSH server; its stdout."""
    return compose(server, "exec", "-T", "ssh-target", *command)


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
    """The forge and its data: its containers, network and volumes. Images and
    what the jobs left stay for the next run (clean removes them)."""
    compose(
        server,
        *("--profile", "runner", "--profile", "cluster", "--profile", "ssh"),
        *("down", "--volumes", "--remove-orphans"),
    )
    (STATE / f"{server}.json").unlink(missing_ok=True)


def clean() -> None:
    """The big cleanup, after every forge (all): brigade's clones, then all
    Docker no longer uses, Docker-wide: stopped containers (the jobs'), unused
    images, networks, build cache and every unused volume (the runners')."""
    shutil.rmtree(TEMPLATES, ignore_errors=True)
    docker("system", "prune", "--all", "--force")
    docker("volume", "prune", "--all", "--force")
