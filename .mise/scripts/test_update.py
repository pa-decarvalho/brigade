"""Check that `mise run brigade:update` moves a project from the latest release to HEAD.

For each ctt.toml variant, like a user with an existing project: create the project
with the variant's post tasks (all but `mise ...`), apply the template at the latest
tag on top of it, commit, update to HEAD (uncommitted changes included), fail on
conflicts, check the answers file is at its current path and that a user-owned CI file
(_skip_if_exists) keeps the user's content, then run the project's lint and test stages.
"""

import os
import subprocess
import tempfile
import tomllib
from pathlib import Path

COPIER = ["uvx", "copier@9.19.1"]
GIT = ["git", "-c", "user.name=brigade", "-c", "user.email=brigade@localhost"]
# A user-owned file per CI platform, with content the update must keep.
USER_FILES = {
    "github": (".github/ci.toml", '# user edit\n[[lint]]\ntask = "lint"\n'),
    "gitea": (".gitea/ci.toml", '# user edit\n[[lint]]\ntask = "lint"\n'),
    "gitlab": (".gitlab/ci/custom.yml", "---\n# user edit\n.custom: {}\n"),
}

repo = Path.cwd()
tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True, check=True).stdout.strip()
variants = tomllib.loads((repo / "ctt.toml").read_text())["output"]
# Questions of the latest release, to skip variants it cannot generate yet (e.g. a new project type).
released_questions = subprocess.run(["git", "show", f"{tag}:.copier/questions.yml"], capture_output=True, text=True, check=True).stdout
# The update must move the answers file to its current name (it was renamed after 0.3.0).
settings = (repo / ".copier/settings.yml").read_text().splitlines()
answers_file = next(line.split(":", 1)[1].strip() for line in settings if line.startswith("_answers_file:"))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp).resolve()
    # Isolate generated projects from this repo's mise config.
    env = {**os.environ, "MISE_TRUSTED_CONFIG_PATHS": str(root), "MISE_CEILING_PATHS": str(root)}
    for key, data in variants.items():
        name = Path(key).name
        project = root / name
        new = [f"{k}={v}" for k, v in data.items() if not k.startswith("_") and f"- {v}\n" not in released_questions]
        if new:
            print(f"--- {name}: skipped, {', '.join(new)} not in {tag}", flush=True)
            continue
        print(f"--- {name}: {tag} -> HEAD", flush=True)

        def run(*cmd: str) -> None:
            subprocess.run(cmd, cwd=project, env=env, check=True)

        project.mkdir()
        for task in data.get("_post_tasks", []):
            if task[0] != "mise":
                run(*task)
        answers = [arg for k, v in data.items() if not k.startswith("_") for arg in ("--data", f"{k}={v}")]
        run(*COPIER, "copy", "--defaults", "--vcs-ref", tag, *answers, str(repo), ".")
        user_file = USER_FILES.get(data.get("ci"))
        if user_file:
            (project / user_file[0]).parent.mkdir(parents=True, exist_ok=True)
            (project / user_file[0]).write_text(user_file[1])
        run(*GIT, "add", "-A")
        run(*GIT, "commit", "-qm", f"brigade {tag}")
        run("mise", "run", "brigade:update", "--defaults", "--vcs-ref", "HEAD")

        files = [p for p in project.rglob("*") if p.is_file() and not {".venv", ".git"} & set(p.parts)]
        conflicts = [p for p in files if p.suffix == ".rej" or "<<<<<<< " in p.read_text(errors="ignore")]
        if conflicts:
            raise SystemExit(f"{name}: update conflicts in {[str(p.relative_to(project)) for p in conflicts]}")
        if not (project / answers_file).is_file():
            raise SystemExit(f"{name}: no {answers_file} after the update")
        if user_file and (project / user_file[0]).read_text() != user_file[1]:
            raise SystemExit(f"{name}: brigade:update changed the user-owned {user_file[0]}")
        run("mise", "run", "lint")
        run("mise", "run", "test")
