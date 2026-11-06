"""Run the generated CI of each ctt.toml variant locally, in Docker.

Runs after test:ctt, on the projects it rendered into .ctt/src/.ctt/: act for GitHub and
Gitea/Forgejo workflows, gitlab-ci-local for GitLab pipelines. Needs a running Docker.
"""

import os
import subprocess
import tomllib
from pathlib import Path

RUNNERS = {
    "github": ["act", "pull_request", "-P", "ubuntu-latest=catthehacker/ubuntu:act-24.04"],
    "gitlab": ["gitlab-ci-local"],
    "gitea": ["act", "pull_request", "-W", ".gitea/workflows", "-P", "ubuntu-latest=catthehacker/ubuntu:act-24.04"],
}
GIT = ["git", "-c", "user.name=brigade", "-c", "user.email=brigade@localhost"]

env = dict(os.environ)
# Docker Desktop on macOS does not use the default socket.
desktop_socket = Path.home() / ".docker/run/docker.sock"
if "DOCKER_HOST" not in env and desktop_socket.exists():
    env["DOCKER_HOST"] = f"unix://{desktop_socket}"
if subprocess.run(["docker", "info"], env=env, capture_output=True).returncode:
    raise SystemExit("test:ci needs a running Docker")

repo = Path.cwd()
variants = tomllib.loads((repo / "ctt.toml").read_text())["output"]
for key, data in variants.items():
    runner = RUNNERS.get(data.get("ci"))
    if not runner:
        continue
    project = repo / ".ctt/src" / key
    print(f"--- {Path(key).name}: {data['ci']} CI", flush=True)
    if "GITHUB_TOKEN" in env and runner[0] == "act":
        runner = [*runner, "-s", "GITHUB_TOKEN"]
    # ctt removes .git; both runners need a repository.
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], [*GIT, "commit", "-q", "--allow-empty", "-m", "ci"], runner):
        subprocess.run(cmd, cwd=project, env=env, check=True)
