"""forges:test: start a local forge, seed it, run the end-to-end tests on it.

Usage: run.py <forge>... (gitea, github, forgejo, gitlab, or all). Each forge
starts alone (its compose profile), gets an admin token and a registered
runner, then the workstation container runs pytest with it; the note lands in
.forges/. With several forges, each one is stopped before the next starts.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FORGES = ["gitea", "github", "forgejo", "gitlab"]
SERVER = {"gitea": "gitea", "github": "gitea", "forgejo": "forgejo", "gitlab": "gitlab"}


def compose(
    profile: str, *args: str, capture: bool = False, stdin: str | None = None
) -> str:
    command = ["docker", "compose", "--profile", profile, *args]
    result = subprocess.run(
        command, cwd=HERE, check=True, text=True, capture_output=capture, input=stdin
    )
    return result.stdout if capture else ""


def exec_(
    profile: str, service: str, script: str, user: str = "root", stdin: str = ""
) -> str:
    """A shell script in a running service; its stdout's last line."""
    out = compose(
        profile, "exec", "-T", "-u", user, service, "sh", "-c", script,
        capture=True, stdin=stdin,
    )  # fmt: skip
    return out.strip().splitlines()[-1]


def seed(forge: str) -> str:
    """An admin token, and the forge's runner up; returns the token."""
    server = SERVER[forge]
    if server in ("gitea", "forgejo"):
        cli = server
        token = exec_(
            forge,
            server,
            f"{cli} admin user create --admin --username brigade --password"
            " brigade-local-forges --email brigade@example.com"
            " --must-change-password=false >/dev/null 2>&1;"
            f" {cli} admin user generate-access-token --username brigade"
            ' --token-name "run-$(date +%s)" --scopes all --raw',
            user="git",
        )
        if server == "forgejo":
            # The runner's secret, known before it starts (compose.yml).
            exec_(
                forge,
                server,
                "forgejo forgejo-cli actions register --name local --secret"
                " 0123456789abcdef0123456789abcdef01234567 >/dev/null; echo ok",
                user="git",
            )
        compose(forge, "up", "-d", f"{server}-runner")
        return token
    # GitLab: a token for root, and an instance runner registered with docker.
    ruby = """
u = User.find_by_username('root')
t = u.personal_access_tokens.create!(
    name: "run-#{Time.now.to_i}", expires_at: 30.days.from_now,
    scopes: [:api, :read_repository, :write_repository])
r = Ci::Runners::CreateRunnerService.new(user: u, params: {
    runner_type: 'instance_type', run_untagged: true, description: 'local'
}).execute.payload[:runner]
puts "#{t.token} #{r.token}"
"""
    script = "cat > /tmp/seed.rb && gitlab-rails runner /tmp/seed.rb"
    token, runner = exec_(forge, "gitlab-app", script, stdin=ruby).split()
    # One runner: those of earlier runs, still in the volume, would take jobs.
    compose(forge, "run", "--rm", "gitlab-runner", "unregister", "--all-runners")
    # The jobs trust compose.yml's local CA, for Releasaurus's https://gitlab.
    compose(
        forge, "run", "--rm", "gitlab-runner", "register", "--non-interactive",
        "--url", "http://gitlab", "--token", runner, "--executor", "docker",
        "--docker-image", "alpine:3.22", "--docker-network-mode", "brigade-forges",
        "--clone-url", "http://gitlab",
        "--docker-volumes", "brigade-forges_gitlab-certs:/certs:ro",
        "--env", "SSL_CERT_FILE=/certs/bundle.pem",
    )  # fmt: skip
    compose(forge, "up", "-d", "gitlab-runner")
    return token


def test(forge: str) -> int:
    print(f"== {forge}", flush=True)
    (HERE / "../../.forges").mkdir(exist_ok=True)
    compose(forge, "up", "-d", "--wait", SERVER[forge], "pypi")
    token = seed(forge)
    pytest = [
        "mise", "x", "uv@0.13.9", "--", "uv", "run", "--no-project", "--python", "3.14",
        "--with", "pytest==9.2.0", "pytest", "/brigade/tests/forges", "--forge", forge,
        "-p", "no:cacheprovider", "-v", "-s",
    ]  # fmt: skip
    command = ["docker", "compose", "--profile", forge, "run", "--rm"]
    command += ["-e", f"FORGE_TOKEN={token}", "workstation", *pytest]
    return subprocess.call(command, cwd=HERE)


def main() -> int:
    forges = FORGES if sys.argv[1:] == ["all"] else sys.argv[1:]
    unknown = set(forges) - set(FORGES)
    if not forges or unknown:
        print(f"usage: forges:test -- <{'|'.join(FORGES)}|all>...", file=sys.stderr)
        return 2
    codes = []
    for index, forge in enumerate(forges):
        codes.append(test(forge))
        if index < len(forges) - 1:
            compose(forge, "stop")
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())
