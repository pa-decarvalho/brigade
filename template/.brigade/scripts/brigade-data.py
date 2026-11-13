"""Write all the answers to .brigade/copier/data.yml (run by brigade-update.py).

brigade-owned: updated by mise run brigade:update, do not edit.
Runs after copier update, in Copier's environment (PyYAML), so that data.yml holds
every answer, new questions included, in the format of copier/data.yml.jinja: JSON
values (double quotes), lists indented under their key.
"""

import json
import pathlib

import yaml  # ty: ignore[import-not-found]  # in Copier's env, not the project's

FOLDER = pathlib.Path(".brigade/copier")


def main() -> None:
    answers = yaml.safe_load((FOLDER / "answers.yml").read_text(encoding="utf-8"))
    lines = ["# Your answers: edit them, then run mise run brigade:update."]
    for key, value in sorted(answers.items()):
        if key.startswith("_"):
            continue
        if isinstance(value, list) and value:
            lines.append(f"{key}:")
            lines += [f"  - {json.dumps(item, ensure_ascii=False)}" for item in value]
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    (FOLDER / "data.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
