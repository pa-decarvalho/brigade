"""brigade:update: run copier update with the answers of .brigade/copier/data.yml.

brigade-owned: updated by mise run brigade:update, do not edit.
Usage: brigade-update.py uvx copier@<version> update ... (from mise.toml, which pins
Copier), then the task's extra arguments. Copier refuses a dirty tree: when data.yml
is the only change, its edits are set aside in a temporary file, data.yml is
restored, and Copier reads the edits from there. Then brigade-data.py writes all the
answers back to data.yml, so the edits and the update end up in one diff. On
failure, the edits are put back.
"""

import pathlib
import subprocess
import sys
import tempfile

DATA = ".brigade/copier/data.yml"


def main() -> int:
    command = sys.argv[1:]
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if [line[3:] for line in status] != [DATA]:
        # Clean, or other changes too: Copier says so.
        return update(command, DATA)
    data = pathlib.Path(DATA)
    edited = data.read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        aside = pathlib.Path(tmp, "data.yml")
        aside.write_bytes(edited)
        subprocess.run(["git", "checkout", "HEAD", "--", DATA], check=True)
        code = update(command, str(aside))
    if code:
        data.write_bytes(edited)
        print(f"brigade:update: failed, {DATA} keeps your edits", file=sys.stderr)
    return code


def update(command: list[str], data: str) -> int:
    code = subprocess.call([*command, "--data-file", data])
    if code:
        return code
    # PyYAML from the same Copier: uvx --from copier@<version> python.
    return subprocess.call(
        ["uvx", "--from", command[1], "python", ".brigade/scripts/brigade-data.py"]
    )


if __name__ == "__main__":
    sys.exit(main())
