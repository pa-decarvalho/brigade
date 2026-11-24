"""brigade:add and brigade:remove: edit the tools answer, then run brigade:update.

brigade-owned: updated by mise run brigade:update, do not edit.
Usage: brigade_tools.py add|remove, the tools in mise's usage_tool variable. Edits
the tools list of .brigade/copier/data.yml as brigade writes it (tools:, then one
quoted tool per line), then runs mise run brigade:update. Copier checks the names
(an unknown tool, or one the CI refuses, fails the update): on failure, data.yml is
put back as it was.
"""

import json
import os
import pathlib
import shlex
import subprocess
import sys

DATA = pathlib.Path(".brigade/copier/data.yml")


def main() -> int:
    action = sys.argv[1]
    names = shlex.split(os.environ.get("usage_tool", ""))
    text = DATA.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        start = lines.index("tools:") + 1
    except ValueError:
        start = None
    if start is None and "tools: []" not in lines:
        print(
            f"brigade:{action}: no tools list in {DATA} as brigade writes it;"
            " edit it by hand, then run mise run brigade:update",
            file=sys.stderr,
        )
        return 1
    if start is None:
        start = lines.index("tools: []") + 1
        lines[start - 1] = "tools:"
    end = start
    while end < len(lines) and lines[end].startswith("  - "):
        end += 1
    tools = [json.loads(line[4:]) for line in lines[start:end]]
    if action == "add":
        new = tools + [n for n in dict.fromkeys(names) if n not in tools]
    else:
        new = [t for t in tools if t not in names]
    same = [n for n in names if (n in tools) == (action == "add")]
    if same:
        state = "already there" if action == "add" else "not there"
        print(f"brigade:{action}: {', '.join(same)}: {state}")
    if new == tools:
        print(f"brigade:{action}: tools: {', '.join(tools)}")
        return 0
    block = [f"  - {json.dumps(t)}" for t in new] if new else []
    lines[start - 1 : end] = ["tools:", *block] if new else ["tools: []"]
    DATA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    code = subprocess.call(["mise", "run", "brigade:update"])
    if code:
        DATA.write_text(text, encoding="utf-8")
        print(f"brigade:{action}: failed, {DATA} put back as before", file=sys.stderr)
        new = tools
    print(f"brigade:{action}: tools: {', '.join(new)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
