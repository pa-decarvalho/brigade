"""Run a tool on the project's files that match glob patterns.

brigade-owned: updated by mise run brigade:update, do not edit.
Usage: brigade_files.py PATTERN... [--contains TEXT] -- COMMAND...
Runs COMMAND with the matching files as its last arguments, and passes (exit 0) when
none match, for tools that fail or wait on stdin without files. Patterns are recursive
globs from the project root (**/*.sh), which skip hidden folders (.mise-data, .venv...)
unless a pattern names one (.github/workflows/*.yml). --contains keeps the files that
hold TEXT (CloudFormation templates among other YAML and JSON files).
"""

import argparse
import glob
import os
import subprocess
import sys


def main() -> int:
    args = sys.argv[1:]
    if "--" not in args:
        print(__doc__, file=sys.stderr)
        return 2
    split = args.index("--")
    parser = argparse.ArgumentParser(prog="brigade_files.py")
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--contains")
    options = parser.parse_args(args[:split])
    command = args[split + 1 :]
    # dict: no duplicates when patterns overlap, in the patterns' order.
    files = list(
        dict.fromkeys(
            path
            for pattern in options.patterns
            for path in sorted(glob.glob(pattern, recursive=True))
            if os.path.isfile(path)
        )
    )
    if options.contains:
        files = [path for path in files if holds(path, options.contains)]
    if not files:
        return 0
    return subprocess.call([*command, *files])


def holds(path: str, text: str) -> bool:
    with open(path, encoding="utf-8", errors="replace") as file:
        return text in file.read()


if __name__ == "__main__":
    sys.exit(main())
