# brigade

A [Copier](https://copier.readthedocs.io/) template that creates new projects managed with [mise](https://mise.jdx.dev/).
The user picks a project type; the template adds the files for that type on top of a common base.

## Rules

- Generated projects must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` plus one fragment per project type in `.mise/conf.d/`.
- Pin versions (mise, tools, Copier).
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.
