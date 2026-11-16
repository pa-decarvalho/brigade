"""Write all the answers to .brigade/copier/data.yml (run by brigade_update.py).

brigade-owned: updated by mise run brigade:update, do not edit.
Runs after copier update, in Copier's environment (PyYAML), so that data.yml holds
every answer, new questions included, in the format of copier/data.yml.jinja: JSON
values (double quotes), lists and mappings (jobs) as YAML blocks, keys sorted.
"""

import importlib
import json
import pathlib

# PyYAML is in Copier's env, not the project's: imported at run time, so that
# type checkers do not look for it (found or not, depending on the machine).
yaml = importlib.import_module("yaml")

FOLDER = pathlib.Path(".brigade/copier")


def entry(key: str, value: object, indent: int) -> list[str]:
    """The lines of one key: a JSON value, or a block for a list or a mapping."""
    pad = " " * indent
    if isinstance(value, dict) and value:
        lines = [f"{pad}{key}:"]
        for k, v in sorted(value.items()):
            lines += entry(k, v, indent + 2)
        return lines
    if isinstance(value, list) and value:
        lines = [f"{pad}{key}:"]
        for item in value:
            lines += list_item(item, indent + 2)
        return lines
    return [f"{pad}{key}: {json.dumps(value, ensure_ascii=False)}"]


def list_item(item: object, indent: int) -> list[str]:
    """The lines of one list item: a JSON value, or a mapping's keys after "- "."""
    pad = " " * indent
    if isinstance(item, dict) and item:
        lines = [
            line for k, v in sorted(item.items()) for line in entry(k, v, indent + 2)
        ]
        return [f"{pad}- {lines[0][indent + 2 :]}", *lines[1:]]
    return [f"{pad}- {json.dumps(item, ensure_ascii=False)}"]


def main() -> None:
    answers = yaml.safe_load((FOLDER / "answers.yml").read_text(encoding="utf-8"))
    lines = ["# Your answers: edit them, then run mise run brigade:update."]
    for key, value in sorted(answers.items()):
        if not key.startswith("_"):
            lines += entry(key, value, 0)
    (FOLDER / "data.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
