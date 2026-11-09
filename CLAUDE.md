# brigade

A [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not scaffold the project itself: create it with the ecosystem's own tool (`uv init`, `cargo init`, ...), then apply brigade on top.
The user picks the tools of each stage; each tool is one mise fragment, and toolchains follow from the tools.

## Rules

- Generated projects only get `.mise/` and the CI files (GitLab: a root `.gitlab-ci.yml` that includes `.gitlab/ci/*.yml`). No source code, no package manifests, no tool config files.
- Generated files are brigade-owned (updated by `brigade:update`) or user-owned: generated once, listed in `_skip_if_exists` (`.copier/settings.yml`), never updated. User-owned files are where projects customize brigade: the CI layout (`ci.toml`), extra CI jobs (`custom.yml`).
- Tool config is given inline in the mise task (command-line options), not in config files. Copier answers live in `.mise/brigade-copier-answers.yml`.
- Generated files must work on Linux, macOS and Windows.
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise config lives in `.mise/`: `config.toml` (uv, `brigade:update`), `conf.d/stages.toml` (stages, git hook tasks), one Jinja fragment per tool `conf.d/<stage>-<tool>.toml` (not `<tool>.toml`: mise reads files such as `ruff.toml` as tool config), generated when selected, with `{{ <stage>_<tool>_version | default('<pin>', true) }}` (a `# renovate: datasource=... depName=...` comment on the line above, read by a `customManagers` entry) and one `<stage>:<tool>` task with a single `run` string `{{ <stage>_<tool>_command | default('<command>', true) }}` (chain steps with `&&`); `conf.d/rust.toml` for the toolchain, generated when a tool needs it (`needs_rust`).
- Pipeline stages are mise tasks in `conf.d/stages.toml`, in order `lint`, `build`, `test`, `release`, `deploy` (CI runs `release` on `X.Y.Z` tags only, `deploy` also on a manual run; publishing tokens are secrets named after the tool's env var). Each runs `<stage>:*`; tools are `<stage>:<tool>` tasks (e.g. `lint:ruff`). A stage without selected tools is left out (stage task, `ci.toml` entry, GitLab job). CI only calls `mise run <task>`.
- Questions live in `.copier/questions/`: `common.yml` (`ci` first because choice validators can use it, one multi-select per stage in stage order, `customize_tools`, mirrors), one file per tool `<stage>/<tool>.yml` and `toolchains/rust.yml`, included by `copier.yml`. Tool questions are named `<stage>_<tool>_version` and `<stage>_<tool>_command`, `when: customize_tools`, with an empty default: an answer overrides brigade's value and stays until changed, an empty answer takes brigade's value in the Jinja file. Keep Jinja out of other files that hold pins (Renovate parses them): conditions go in file names or in pin-free files.
- Add a stage (build, release, deploy...) only when a tool needs it.
- brigade-owned CI files only install mise (GitHub/Gitea: the `actions/mise` composite action) and call `mise run <task>`; each CI platform lints its own files (`lint:actionlint`, `lint:gitlab-ci`).
- GitHub/Gitea: a `plan` job turns the user-owned `ci.toml` (jobs × runners per stage) into matrices (`.mise/scripts/ci_plan.py`); `ci.yml` then calls the user-owned `custom.yml`. GitLab: `.gitlab-ci.yml` includes the user-owned `.gitlab/ci/custom.yml` last.
- Linters and formatters are mise tools, not project dependencies.
- `brigade:*` tasks are brigade's own helpers (`brigade:update`, `brigade:hooks`, `brigade:ci-local`), not pipeline stages. `brigade:ci-local` (`ci_local` question) must stay out of `test:*`: run by CI, it would start the CI again. Its tools are declared on the task, so `mise install` and CI skip them.
- Pin versions (mise, tools, Copier). Renovate keeps them up to date (`.github/renovate.json5`): a new pin outside a standard mise/CI location needs a matching `customManagers` entry. Generated projects get new versions through a brigade release and `mise run brigade:update`.
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.
- PRs are squash-merged with the PR title as commit message, so PR titles follow Conventional Commits (merge commits made release-please list changes twice).
- Commits follow Conventional Commits. Releases are made by merging the release-please PR, which tags `X.Y.Z`; Copier uses these tags as template versions.

## Testing

`mise run lint` checks this repo (yamllint, actionlint, taplo, editorconfig-checker, gitleaks, typos, Renovate config schema).
`mise run test` renders each `ctt.toml` variant into `.ctt/src/.ctt/`, creates a real project there with the ecosystem's tool, then runs its mise tasks.
ctt only sees files tracked by git.
`mise run test` also runs `test:update`: for each variant, create the project first, apply the template at the latest tag on top of it, update to HEAD with `mise run brigade:update`, then run the project's stages; it also checks that user-owned files keep their content.
`mise run test` also runs `test:ci`: each variant's generated CI, locally with its `brigade:ci-local` task (act on GitHub and Gitea, gitlab-ci-local on GitLab). It needs a running Docker (Docker Desktop's socket is found on macOS).
`mise run test` also runs `test:docs`: builds the documentation site (`docs/`, `zensical.toml`) with Zensical in strict mode, which fails on broken links. `.github/workflows/docs.yml` deploys it to GitHub Pages on push to `main`.
User-facing changes (questions, tasks, CI files) update the matching page in `docs/`; the README stays a short summary.
brigade's CI runs `test:ctt` and `test:update` on Linux, macOS and Windows (developer OSes), and `test:ci` on Linux only (generated CI runs in Linux containers).
