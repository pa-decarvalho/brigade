"""brigade:update: run copier update with the answers of .brigade/copier/data.yml.

brigade-owned: updated by mise run brigade:update, do not edit.
Usage: brigade_update.py uvx copier@<version> update ... (from mise.toml, which pins
Copier), then the task's extra arguments. Copier refuses a dirty tree: when data.yml
is the only change, its edits are set aside in .git/brigade-data.yml, data.yml is
restored, and Copier reads the edits from there. Then brigade_data.py writes all the
answers back to data.yml, so the edits and the update end up in one diff, and mise
-C .brigade lock writes the tools' pins and checksums to .brigade/mise.lock, and,
outside CI, the forge CLI's check (gh, glab or tea) lists missing settings. On
failure or Ctrl+C, the edits are put back; after a killed run, the next run puts
them back first.
"""

import os
import pathlib
import subprocess
import sys

DATA = ".brigade/copier/data.yml"


def main() -> int:
    command = sys.argv[1:]
    data = pathlib.Path(DATA)
    # In .git/: out of the work tree, which Copier needs clean, and kept if killed.
    aside = pathlib.Path(git("rev-parse", "--git-path", "brigade-data.yml").strip())
    if aside.exists():
        if DATA in changes():
            print(
                f"brigade:update: {aside} holds the {DATA} edits of an interrupted"
                f" run, and {DATA} has new edits: merge them, then delete {aside}",
                file=sys.stderr,
            )
            return 1
        data.write_bytes(aside.read_bytes())
        aside.unlink()
        print(f"brigade:update: {DATA} edits of an interrupted run put back")
    if changes() != [DATA]:
        # Clean, or other changes too: Copier says so.
        return update(command, DATA)
    aside.write_bytes(data.read_bytes())
    git("checkout", "HEAD", "--", DATA)
    code = 1
    try:
        code = update(command, str(aside))
    finally:
        if code:
            data.write_bytes(aside.read_bytes())
            print(f"brigade:update: failed, {DATA} keeps your edits", file=sys.stderr)
        aside.unlink()
    return code


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def changes() -> list[str]:
    status = git("status", "--porcelain", "--untracked-files=all", "--", ".")
    return [line[3:] for line in status.splitlines()]


def update(command: list[str], data: str) -> int:
    code = subprocess.call([*command, "--data-file", data])
    if code:
        return code
    # PyYAML from the same Copier: uvx --from copier@<version> python.
    code = subprocess.call(
        ["uvx", "--from", command[1], "python", ".brigade/scripts/brigade_data.py"]
    )
    if code:
        return code
    # The tools' new pins and checksums, in .brigade/mise.lock: not a failure of
    # the update (offline, conflict markers left by Copier...). From .brigade/: from
    # the root, mise locks only the project's mise.toml when there is one.
    if subprocess.call(["mise", "-C", ".brigade", "lock"]):
        print(
            "brigade:update: mise -C .brigade lock failed, run it again",
            file=sys.stderr,
        )
    check()
    return 0


def check() -> None:
    """Run the forge CLI's check, as a notice: an update can add a tool that needs
    a repository setting. Locally only (CI's token cannot read them all)."""
    if os.environ.get("CI"):
        return
    for cli in ("gh", "glab", "tea"):
        if pathlib.Path(f".brigade/conf.d/{cli}-brigade.toml").exists():
            print(
                f"brigade:update: the repository's settings ({cli}:check):", flush=True
            )
            subprocess.call(["mise", "run", "--quiet", f"{cli}:check"])


if __name__ == "__main__":
    sys.exit(main())
