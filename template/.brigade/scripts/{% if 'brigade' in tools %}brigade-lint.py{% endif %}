"""brigade:lint: fail when a brigade-owned file differs from the template.

brigade-owned: updated by mise run brigade:update, do not edit.
Renders the template at the version of .brigade/copier/answers.yml into a temporary
folder, then compares each rendered file with the project's: data.yml differs when
edited answers are not applied yet. Also tells when a newer brigade release is out
(a notice, not a failure).
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ANSWERS = ".brigade/copier/answers.yml"
DATA = ".brigade/copier/data.yml"


def read(path: pathlib.Path) -> bytes:
    # Windows checkouts may have CRLF line endings.
    return path.read_bytes().replace(b"\r\n", b"\n")


def main() -> int:
    answers = pathlib.Path(ANSWERS)
    if not answers.is_file():
        if pathlib.Path(".brigade/answers.yml").is_file():
            print(
                f"brigade:lint: move .brigade/answers.yml to {ANSWERS} (brigade 0.13)"
            )
            return 1
        print(f"brigade:lint: no {ANSWERS}, skipped")
        return 0
    text = answers.read_text(encoding="utf-8")

    def answer(key: str) -> str:
        match = re.search(rf"^{key}: *(.+)$", text, re.MULTILINE)
        if not match:
            sys.exit(f"brigade:lint: no {key} in {ANSWERS}")
        return match.group(1).strip().strip("'\"")

    src = answer("_src_path")
    # A local template (brigade's own tests) is rendered as it is now, as Copier did.
    ref = "HEAD" if pathlib.Path(src).is_dir() else answer("_commit")
    # Copier clones the template with git: drop this repository's git variables, which
    # a git hook sets (a relative GIT_INDEX_FILE breaks the clone).
    local = subprocess.run(
        ["git", "rev-parse", "--local-env-vars"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    env = {k: v for k, v in os.environ.items() if k not in local}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                shutil.which("copier") or "copier",
                "copy",
                "--vcs-ref",
                ref,
                "--data-file",
                ANSWERS,
                "--defaults",
                "--quiet",
                src,
                tmp,
            ],
            check=True,
            env=env,
        )
        rendered = pathlib.Path(tmp)
        problems = []
        for path in sorted(rendered.rglob("*")):
            name = path.relative_to(rendered).as_posix()
            if not path.is_file() or name == ANSWERS:
                continue
            mine = pathlib.Path(name)
            if not mine.is_file():
                problems.append(f"  {name}: missing")
            elif read(mine) != read(path):
                problems.append(
                    f"  {name}: {'not applied' if name == DATA else 'edited'}"
                )
    if problems:
        print(f"brigade:lint: brigade-owned files differ from the template ({ref}):")
        print("\n".join(problems))
        print(
            "Run mise run brigade:update to restore them, or drop the brigade tool to allow edits."
        )
        return 1
    print(f"brigade:lint: brigade-owned files match the template ({ref})")
    if ref != "HEAD":
        notify_update(env)
    return 0


def notify_update(env: dict[str, str]) -> None:
    result = subprocess.run(
        [
            shutil.which("copier") or "copier",
            "check-update",
            "--answers-file",
            ANSWERS,
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    try:
        status = json.loads(result.stdout)
    except ValueError:
        return  # a notice only: never fail the lint for it
    if status.get("update_available"):
        print(
            f"brigade:lint: brigade {status['latest_version']} is out (this project:"
            f" {status['current_version']}): run mise run brigade:update"
        )


if __name__ == "__main__":
    sys.exit(main())
