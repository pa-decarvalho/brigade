"""Check that `mise run brigade:update` moves a project from the latest release to HEAD.

For each ctt.toml variant, like a user with an existing project: create the project
with the variant's post tasks (all but `mise ...`), apply the template at the latest
tag on top of it, commit, update to HEAD (uncommitted changes included), fail on
conflicts, check the answers file is at its current path, then run the stages of the variant.
"""

import os
import subprocess
import tempfile
import tomllib
from pathlib import Path

COPIER = ["uvx", "copier@9.19.1"]
GIT = ["git", "-c", "user.name=brigade", "-c", "user.email=brigade@localhost"]

repo = Path.cwd()
tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True, check=True).stdout.strip()
variants = tomllib.loads((repo / "ctt.toml").read_text())["output"]


def read_questions(tag: str) -> str:
    """Every Copier question file at this tag, whatever their layout."""
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", tag, ".copier"], capture_output=True, text=True, check=True).stdout.split("\n")
    files = [name for name in names if name.endswith(".yml") and not name.endswith("settings.yml")]
    return "\n".join(subprocess.run(["git", "show", f"{tag}:{name}"], capture_output=True, text=True, check=True).stdout for name in files)


# Questions of the latest release, to skip variants it cannot generate yet (e.g. a new question or choice).
released_questions = read_questions(tag)
current_questions = "\n".join(path.read_text() for path in (repo / ".copier").rglob("*.yml") if path.name != "settings.yml")


def is_choice(value: object, questions: str) -> bool:
    """Whether a value appears as a choice: "- value", "label: value" or "value: value" under a label."""
    return f"- {value}\n" in questions or f": {value}\n" in questions


def is_new(key: str, value: object) -> bool:
    """Whether the release lacks this question, or one of its choices. Free text (e.g. a URL) is not a choice."""
    if f"\n{key}:" not in "\n" + released_questions:
        return True
    values = value if isinstance(value, list) else [value]
    return any(is_choice(v, current_questions) and not is_choice(v, released_questions) for v in values)


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
        new = [f"{k}={v}" for k, v in data.items() if not k.startswith("_") and is_new(k, v)]
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
        run(*GIT, "add", "-A")
        run(*GIT, "commit", "-qm", f"brigade {tag}")
        run("mise", "run", "brigade:update", "--defaults", "--vcs-ref", "HEAD")

        files = [p for p in project.rglob("*") if p.is_file() and not {".venv", ".git"} & set(p.parts)]
        conflicts = [p for p in files if p.suffix == ".rej" or "<<<<<<< " in p.read_text(errors="ignore")]
        if conflicts:
            raise SystemExit(f"{name}: update conflicts in {[str(p.relative_to(project)) for p in conflicts]}")
        if not (project / answers_file).is_file():
            raise SystemExit(f"{name}: no {answers_file} after the update")
        for task in data.get("_post_tasks", []):
            if task[:2] == ["mise", "run"] and not task[2].startswith("brigade:"):
                run(*task)
