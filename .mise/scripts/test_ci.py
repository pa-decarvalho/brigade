"""Run the generated CI of each ctt.toml variant locally, in Docker.

Runs after ctt:test, on the projects it rendered into .ctt/, with each project's
own brigade:ci-local task. Needs a running Docker.
"""

import os
import subprocess
import tomllib
from pathlib import Path

GIT = ["git", "-c", "user.name=brigade", "-c", "user.email=brigade@localhost"]

env = dict(os.environ)
# Docker Desktop on macOS does not use the default socket.
desktop_socket = Path.home() / ".docker/run/docker.sock"
if "DOCKER_HOST" not in env and desktop_socket.exists():
    env["DOCKER_HOST"] = f"unix://{desktop_socket}"
if subprocess.run(["docker", "info"], env=env, capture_output=True).returncode:
    raise SystemExit("ci:test needs a running Docker")

repo = Path.cwd()
variants = tomllib.loads((repo / "ctt.toml").read_text())["output"]
for key, data in variants.items():
    project = repo / key
    if "ci-local" not in data.get("tools", []):
        continue
    print(f"--- {Path(key).name}: {data['ci']} CI", flush=True)
    runner = ["mise", "run", "brigade:ci-local"]
    if "GITHUB_TOKEN" in env and data["ci"] != "gitlab":
        runner += ["--", "-s", "GITHUB_TOKEN"]
    # ctt removes .git; both runners need a repository.
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], [*GIT, "commit", "-q", "--allow-empty", "-m", "ci"], runner):
        subprocess.run(cmd, cwd=project, env=env, check=True)
