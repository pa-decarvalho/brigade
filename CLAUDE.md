# brigade

A [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not scaffold the project itself: create it with the ecosystem's own tool (`uv init`, `cargo init`, ...), then apply brigade on top.
The user picks a project type; the template adds the files for that type on top of a common base.

## Rules

- Generated projects only get `.mise/` and the CI file. No source code, no package manifests, no tool config files.
- Tool config is given inline in the mise task (command-line options), not in config files. Copier answers live in `.mise/copier-answers.yml`.
- Generated files must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` plus one fragment per project type in `.mise/conf.d/`.
- Pipeline stages are mise tasks in the base `config.toml` (today: `lint`, `test`). Each runs `<stage>:*`; tools are `<stage>:<tool>` tasks (e.g. `lint:ruff`), common ones in `.mise/conf.d/<stage>.toml`, type-specific ones in `.mise/conf.d/<type>.toml`. CI only calls `mise run <stage>`.
- Add a stage (build, release, deploy...) only when a project type needs it.
- CI files only install mise and call `mise run <stage>`; each CI platform lints its own file (`lint:actionlint`, `lint:gitlab-ci`).
- Linters and formatters are mise tools, not project dependencies.
- Pin versions (mise, tools, Copier).
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.

## Testing

`mise run lint` checks this repo (yamllint, actionlint, taplo, editorconfig-checker).
`mise run test` renders each `ctt.toml` variant into `.ctt/`, creates a real project there with the ecosystem's tool, then runs its mise tasks.
ctt only sees files tracked by git.
`mise run ci:github` / `mise run ci:gitlab` run the generated CI files locally with act / gitlab-ci-local (Docker required; with Docker Desktop on macOS set `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock`).
