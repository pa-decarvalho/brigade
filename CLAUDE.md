# brigade

A [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not scaffold the project itself: create it with the ecosystem's own tool (`uv init`, `cargo init`, ...), then apply brigade on top.
The user picks a project type; the template adds the files for that type on top of a common base.

## Rules

- Generated projects only get `.mise/` and the CI files (GitLab: a root `.gitlab-ci.yml` that includes `.gitlab/ci/*.yml`). No source code, no package manifests, no tool config files.
- Tool config is given inline in the mise task (command-line options), not in config files. Copier answers live in `.mise/brigade-copier-answers.yml`.
- Generated files must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` plus one fragment per project type in `.mise/conf.d/`.
- Pipeline stages are mise tasks in the base `config.toml` (today: `lint`, `test`). Each runs `<stage>:*`; tools are `<stage>:<tool>` tasks (e.g. `lint:ruff`), common ones in `.mise/conf.d/<stage>.toml`, type-specific ones in `.mise/conf.d/<type>.toml`. CI only calls `mise run <stage>`.
- Add a stage (build, release, deploy...) only when a project type needs it.
- CI files only install mise and call `mise run <stage>`; each CI platform lints its own files (`lint:actionlint`, `lint:gitlab-ci`).
- Linters and formatters are mise tools, not project dependencies.
- `brigade:*` tasks are brigade's own helpers (`brigade:update`, `brigade:hooks`), not pipeline stages.
- Pin versions (mise, tools, Copier). Renovate keeps them up to date (`.github/renovate.json5`): a new pin outside a standard mise/CI location needs a matching `customManagers` entry. Generated projects get new versions through a brigade release and `mise run brigade:update`.
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.
- PRs are squash-merged with the PR title as commit message, so PR titles follow Conventional Commits (merge commits made release-please list changes twice).
- Commits follow Conventional Commits. Releases are made by merging the release-please PR, which tags `X.Y.Z`; Copier uses these tags as template versions.

## Testing

`mise run lint` checks this repo (yamllint, actionlint, taplo, editorconfig-checker, gitleaks, typos, Renovate config schema).
`mise run test` renders each `ctt.toml` variant into `.ctt/src/.ctt/`, creates a real project there with the ecosystem's tool, then runs its mise tasks.
ctt only sees files tracked by git.
`mise run test` also runs `test:update`: for each variant, create the project first, apply the template at the latest tag on top of it, update to HEAD with `mise run brigade:update`, then run the project's stages.
`mise run test` also runs `test:ci`: each variant's generated CI, locally with act (GitHub) or gitlab-ci-local (GitLab). It needs a running Docker (Docker Desktop's socket is found on macOS).
brigade's CI runs `test:ctt` and `test:update` on Linux, macOS and Windows (developer OSes), and `test:ci` on Linux only (generated CI runs in Linux containers).
