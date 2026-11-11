# brigade

A [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not scaffold the project itself: create it with the ecosystem's own tool (`uv init`, ...), then apply brigade on top.
The user picks tools in one list; each tool is one mise fragment with all its tasks, and stages follow from the tools.

## Rules

- Generated projects only get `.mise/` and the CI files (GitLab: a root `.gitlab-ci.yml` that includes `.gitlab/ci/*.yml`). No source code, no package manifests, no tool config files.
- Generated files are brigade-owned (updated by `brigade:update`). Projects customize their stages through the `<stage>_enabled` and `<stage>_commands` answers, or add their own files, which Copier never touches: workflows (GitHub, Gitea), `.gitlab/ci/*.yml` (GitLab).
- Tool config is given inline in the mise task (command-line options), not in config files. Copier answers live in `.mise/brigade-copier-answers.yml`.
- Generated files must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` (uv, `brigade:update`), `conf.d/stages.toml` (stages, git hook tasks), one Jinja fragment per tool `conf.d/tool-<tool>.toml` (not `<tool>.toml`: mise reads files such as `ruff.toml` as tool config; subfolders of `conf.d` are not read), generated when selected, with `{{ <tool>_version | default('<pin>', true) }}` (a `# renovate: datasource=... depName=...` comment on the line above, read by a `customManagers` entry) and `<tool>:<action>` tasks, each with a single `run` string `{{ <tool>_<action>_command | default('<command>', true) }}` (chain steps with `&&`).
- Pipeline stages are mise tasks in `conf.d/stages.toml`, in order `lint`, `build`, `test`, `release`, `deploy`, `operate`. CI runs `release` on pushes to the default branch (`releasaurus:release`: release PR, then tag `X.Y.Z` once merged, with an optional bot token secret, else the CI token, whose tag starts no CI), `deploy` on `X.Y.Z` tags and manual runs, and `operate` (`renovate:operate`) on manual runs and on the `operate_schedule` cron answer (GitLab: scheduled pipelines, since "Run pipeline" deploys). Tokens are secrets named after the tool's env var. Each runs `*:<stage>`; tools are `<tool>:<stage>` tasks (e.g. `ruff:lint`), and any other action (`zensical:serve`) stays out of the pipeline. `<stage>_enabled` keeps the stage or not (mise task and CI job); `<stage>_commands`, when given, replaces its tools with a `run` list, the same locally and in CI. A stage without tools does nothing: its `depends` is `optional`, because `*:<stage>` fails otherwise. CI only calls `mise run <stage>`.
- Questions live in `.copier/questions/`: `common.yml` (`ci` first because choice validators can use it, the `tools` multi-select, `<stage>_enabled` and `<stage>_commands`, `customize_tools`, mirrors), one file per tool `tools/<tool>.yml`, included by `copier.yml`. Tool questions are named `<tool>_version` and `<tool>_<action>_command`, `when: customize_tools`, with an empty default: an answer overrides brigade's value and stays until changed, an empty answer takes brigade's value in the Jinja file. Keep Jinja out of other files that hold pins (Renovate parses them): conditions go in file names or in pin-free files.
- Add a stage (build, release, deploy...) only when a tool needs it.
- brigade-owned CI files only install mise (GitHub/Gitea: the `actions/mise` composite action) and call `mise run <task>`; each CI platform lints its own files (`jactionlint:lint` with its default profile, `gitlab-ci:lint`): workflows pin actions by SHA with a version comment, set `permissions:`, `timeout-minutes` and `concurrency:`, and restore no cache where they publish (`deploy`).
- Each enabled stage is one CI job on Linux, running `mise run <stage>`, with no `needs` between stages: `lint`, `build`, `test` on pull/merge requests only, `release` on pushes to the default branch, `deploy` on `X.Y.Z` tags and manual runs, the same on every platform. GitHub/Gitea: one workflow per stage, `workflows/{% if <stage>_enabled %}<stage>.yml{% endif %}`, plain YAML (Renovate reads its `uses:`), except `operate.yml.jinja` for its schedule. GitLab: `.gitlab-ci.yml` includes only `.gitlab/ci/*.yml`, whose order is not guaranteed: no file may redefine a key of another (`default.yml` holds the image, cache and `before_script`).
- Linters and formatters are mise tools, not project dependencies.
- `brigade:*` tasks are brigade's own helpers (`brigade:update`, `brigade:hooks`, `brigade:ci-local`), not pipeline stages. `brigade:ci-local` (the `ci-local` tool) must stay out of the `*:test` tasks: run by CI, it would start the CI again. Its tools are declared on the task, so `mise install` and CI skip them.
- Pin versions (mise, tools, Copier). Renovate keeps them up to date (`.github/renovate.json5`): a new pin outside a standard mise/CI location needs a matching `customManagers` entry. Generated projects get new versions through a brigade release and `mise run brigade:update`. Renovate only reads `template/` (`includePaths`), in one `fix:` PR: brigade's generated files follow through `brigade:update`, its other pins (Copier and pytest in tests and docs) are updated by hand.
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.
- PRs are squash-merged with the PR title as commit message, so PR titles follow Conventional Commits (merge commits made the release tool list changes twice).
- Commits follow Conventional Commits. Releases are made by merging the release PR, which tags `X.Y.Z`; Copier uses these tags as template versions.

## Testing

brigade is generated by brigade: `mise run brigade:update` updates its `.mise/` and `.github/` CI files from the latest release (answers in `.mise/brigade-copier-answers.yml`, with commands adapted to this repo). Its own tasks and env live in `.mise/conf.d/project.toml`.
`mise run lint` checks this repo (yamllint, jactionlint, taplo, editorconfig-checker, gitleaks, typos, Renovate config schema).
`mise run build` builds the documentation site (`docs/`, `zensical.toml`) with Zensical in strict mode, which fails on broken links; `mise run deploy` pushes it to the `gh-pages` branch (CI: manual runs, since tags made with the workflow token start no CI).
`mise run test` renders each `ctt.toml` variant into `.ctt/` (`ctt:test`), creates a real project there with the ecosystem's tool, then runs its mise tasks.
ctt only sees files tracked by git.
`mise run test` also runs `update:test`: for each variant, create the project first, apply the template at the latest tag on top of it, update to HEAD with `mise run brigade:update`, then run the project's stages.
`mise run test` also runs `ci:test`: each variant's generated CI, locally with its `brigade:ci-local` task (act on GitHub and Gitea, gitlab-ci-local on GitLab). It needs a running Docker (Docker Desktop's socket is found on macOS).
User-facing changes (questions, tasks, CI files) update the matching page in `docs/`; the README stays a short summary.
brigade's CI runs these tests on Linux only: the rule above on macOS and Windows is no longer tested.
