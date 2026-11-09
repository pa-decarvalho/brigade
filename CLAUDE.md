# brigade

A [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not scaffold the project itself: create it with the ecosystem's own tool (`uv init`, `cargo init`, ...), then apply brigade on top.
The user picks tools in one list; each tool is one mise fragment with all its tasks, and stages and toolchains follow from the tools.

## Rules

- Generated projects only get `.mise/` and the CI files (GitLab: a root `.gitlab-ci.yml` that includes `.gitlab/ci/*.yml`). No source code, no package manifests, no tool config files.
- Generated files are brigade-owned (updated by `brigade:update`). Projects customize their stages through the `<stage>_enabled` and `<stage>_commands` answers, or add their own files, which Copier never touches: workflows (GitHub, Gitea), `.gitlab/ci/*.yml` (GitLab).
- Tool config is given inline in the mise task (command-line options), not in config files. Copier answers live in `.mise/brigade-copier-answers.yml`.
- Generated files must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` (uv, `brigade:update`), `conf.d/stages.toml` (stages, git hook tasks), one Jinja fragment per tool `conf.d/tool-<tool>.toml` (not `<tool>.toml`: mise reads files such as `ruff.toml` as tool config; subfolders of `conf.d` are not read), generated when selected, with `{{ <tool>_version | default('<pin>', true) }}` (a `# renovate: datasource=... depName=...` comment on the line above, read by a `customManagers` entry) and `<tool>:<action>` tasks, each with a single `run` string `{{ <tool>_<action>_command | default('<command>', true) }}` (chain steps with `&&`); `conf.d/rust.toml` for the toolchain, generated when a tool needs it (`needs_rust`).
- Pipeline stages are mise tasks in `conf.d/stages.toml`, in order `lint`, `build`, `test`, `release`, `deploy` (CI runs `release` on `X.Y.Z` tags only, `deploy` also on a manual run; publishing tokens are secrets named after the tool's env var). Each runs `*:<stage>`; tools are `<tool>:<stage>` tasks (e.g. `ruff:lint`), and any other action (`zensical:serve`) stays out of the pipeline. `<stage>_enabled` keeps the stage or not (mise task and CI job); `<stage>_commands`, when given, replaces its tools with a `run` list, the same locally and in CI. A stage without tools does nothing: its `depends` is `optional`, because `*:<stage>` fails otherwise. CI only calls `mise run <stage>`.
- Questions live in `.copier/questions/`: `common.yml` (`ci` first because choice validators can use it, the `tools` multi-select, `needs_rust` computed from it, `<stage>_enabled` and `<stage>_commands`, `customize_tools`, mirrors), one file per tool `tools/<tool>.yml` and `toolchains/rust.yml`, included by `copier.yml`. Tool questions are named `<tool>_version` and `<tool>_<action>_command`, `when: customize_tools`, with an empty default: an answer overrides brigade's value and stays until changed, an empty answer takes brigade's value in the Jinja file. Keep Jinja out of other files that hold pins (Renovate parses them): conditions go in file names or in pin-free files.
- Add a stage (build, release, deploy...) only when a tool needs it.
- brigade-owned CI files only install mise (GitHub/Gitea: the `actions/mise` composite action) and call `mise run <task>`; each CI platform lints its own files (`lint:actionlint`, `lint:gitlab-ci`).
- Each enabled stage is one CI job on Linux, running `mise run <stage>`; `needs` follows the jobs generated. GitHub/Gitea: `ci.yml.jinja`, the one file with both Jinja and pins (Renovate reads its `uses:`). GitLab: `.gitlab-ci.yml` includes only `.gitlab/ci/*.yml`, whose order is not guaranteed: no file may redefine a key of another (`default.yml` holds the image and cache, `setup.yml` the `before_script`).
- Linters and formatters are mise tools, not project dependencies.
- `brigade:*` tasks are brigade's own helpers (`brigade:update`, `brigade:hooks`, `brigade:ci-local`), not pipeline stages. `brigade:ci-local` (the `ci-local` tool) must stay out of the `*:test` tasks: run by CI, it would start the CI again. Its tools are declared on the task, so `mise install` and CI skip them.
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
`mise run test` also runs `test:ci`: each variant's generated CI, locally with its `brigade:ci-local` task (act on GitHub and Gitea, gitlab-ci-local on GitLab). It needs a running Docker (Docker Desktop's socket is found on macOS).
`mise run test` also runs `test:docs`: builds the documentation site (`docs/`, `zensical.toml`) with Zensical in strict mode, which fails on broken links. `.github/workflows/docs.yml` deploys it to GitHub Pages on push to `main`.
User-facing changes (questions, tasks, CI files) update the matching page in `docs/`; the README stays a short summary.
brigade's CI runs `test:ctt` and `test:update` on Linux, macOS and Windows (developer OSes), and `test:ci` on Linux only (generated CI runs in Linux containers).
