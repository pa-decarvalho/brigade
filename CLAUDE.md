# brigade

A [Copier](https://copier.readthedocs.io/) template that adds
[mise](https://mise.jdx.dev/) tooling and CI to a project. It does not scaffold
the project itself: create it with the ecosystem's own tool (`uv init`, ...),
then apply brigade on top. The user picks tools in one list; each tool is one
mise fragment with all its tasks, and stages follow from the tools.

## Rules

- Generated projects only get `.miserc.toml`, `.brigade/` and the CI entry files
  that cannot live elsewhere (GitHub/Gitea workflows, GitLab's root
  `.gitlab-ci.yml`). Everything else brigade generates goes in `.brigade/`. No
  source code, no package manifests, no tool config files at the root.
- Generated files are brigade-owned (updated by `brigade:update`). Projects
  customize their stages through the `<stage>_enabled` and `<stage>_commands`
  answers, or add their own files, which Copier never touches: `mise.toml` and
  `mise.local.toml` (the only other mise files read), workflows (GitHub, Gitea),
  `.gitlab/ci/*.yml` (GitLab).
- Tool config goes in `.brigade/configs/<tool>.<ext>` when the tool takes a
  config path (`-c`...) and brigade passes it settings
  (`template/.brigade/configs/{% if '<tool>' in tools %}<file>{% endif %}`, no
  Jinja inside unless a setting depends on the answers, then a `.jinja` file:
  `renovate.json`'s parts, from `renovate_updates`;
  `releasaurus.toml`'s `release_type`, from `releasaurus_release_type` or the
  ecosystem tool; paths relative to the project root): brigade-owned, the
  task's path being
  `{%- set config = <tool>_config or '.brigade/configs/<file>' -%}` (a
  `<tool>_config` answer points to the project's own file); except configs that
  hold the project's content (`goreleaser`, `container-structure-test`,
  `ls-lint`, `sqlfluff`, `prek`): created once, then the project's
  (`_skip_if_exists` in `.copier/settings.yml`, `PROJECT_CONFIGS` skipped by
  `brigade:lint`). A setting brigade needs goes in the brigade-owned config, or
  in the command when the config is the project's and the option adds to it.
  Other settings stay command-line options. Copier answers live in
  `.brigade/copier/answers.yml` (written by Copier); the project edits them in
  `.brigade/copier/data.yml` (all the answers but `_commit` and `_src_path`:
  rendered once, `_skip_if_exists`, since Copier's merge of it conflicts;
  `brigade:update` runs `.brigade/scripts/brigade_update.py` (pinned Copier
  command as arguments), which passes it with `--data-file`, set aside in
  `.git/brigade-data.yml` when it is the only uncommitted change (Copier needs a
  clean tree; put back on failure or Ctrl+C, and by the next run after a killed
  one), then, on success only, `.brigade/scripts/brigade_data.py` (PyYAML from
  the same Copier's env, `uvx --from copier@<version>`; not a `depends_post`
  task, which runs even on failure) writes all the answers back to it, new
  questions included, in the format `copier/data.yml.jinja` renders (sorted
  keys, JSON values, lists and mappings as YAML blocks); `brigade:lint` compares
  it as any file, so an edit not yet applied fails).
- Generated files must work on Linux, macOS and Windows; each tool runs where it
  is supported (limits listed in `docs/tools.md#platforms`).
- No bash: tasks are TOML commands, real logic is Python run with `uv run`.
- mise reads only the files listed in `.miserc.toml`
  (`override_config_filenames`: exact names, no globs, missing ones ignored):
  `.brigade/mise.toml` (uv, `brigade:update`), `.brigade/stages.toml` (stages),
  `.brigade/mirror.toml`, one Jinja fragment per selected tool
  `.brigade/conf.d/<tool>-brigade.toml` (the suffix avoids names such as
  `ruff.toml`, which mise reads as tool config; `conf.d/` makes mise write one
  lockfile, `.brigade/mise.lock` with its `.brigade/.mise/locks/` sidecars, for
  all of `.brigade/`: `brigade:update` runs `mise -C .brigade install` then
  `mise -C .brigade lock` after Copier (installed first: `mise lock` leaves out
  what only an install records, an npm package's provenance, which CI's install
  would add, dirtying the tree that `deno publish` and GoReleaser check)
  (from the root, mise locks only a project's own `mise.toml` when it exists),
  and `mise install` checks the checksums; `pipx:` tools set `python = "3.14"`,
  which locked Python dependencies need), the CI file linter
  (`jactionlint-brigade.toml`, `gitlab-ci-brigade.toml`), then the project's
  `mise.toml` and `mise.local.toml`. A task runs in its file's folder by
  default: every brigade task sets `dir` to the project root
  (`{{config_root}}/..` in `.brigade/`, `{{config_root}}/../..` in `conf.d/`;
  not `[task_config] dir`, which also moves the project's tasks). Tool fragments
  are generated when selected, with
  `{{ <tool>_version | default('<pin>', true) }}` (a
  `# renovate: datasource=... depName=...` comment on the line above, read by a
  `customManagers` entry) and `<tool>:<action>` tasks, each with a single `run`
  string `{{ <tool>_<action>_command | default('<command>', true) }}` (chain
  steps with `&&`).
- Pipeline stages are mise tasks in `.brigade/stages.toml`, in order `lint`,
  `build`, `test`, `release`, `publish`, `deploy`, `operate`. CI runs `release`
  on pushes to the default branch (`releasaurus:release`: release PR, then tag
  `X.Y.Z` once merged, with an optional bot token secret, else the CI token,
  whose tag starts no CI), `publish` (artifacts to registries, once per
  version) on `X.Y.Z` tags and manual runs, `deploy` (to an environment, as
  often as needed, nothing published) after `publish` (by itself with the
  `deploy_auto` answer, else when started; GitHub/Gitea: `publish.yml`'s last
  job starts `deploy.yml` on the tag with `.brigade/scripts/ci_dispatch.py`
  and the job token; GitLab: a job of the tag's pipeline, `when: manual`
  without `deploy_auto`) and on manual runs (on `X.Y.Z` tags itself when
  `publish` is disabled); the `environments` answer (`{name, auto}`) makes it
  one deploy per environment (`BRIGADE_ENVIRONMENT`; GitHub/Gitea: a matrix
  over the dispatch's `environments` input, secrets scoped by GitHub
  Environments or suffixed `<NAME>_<ENV>` on Gitea, never `secrets[...]`;
  GitLab: one job per environment), and `operate`
  (`renovate:operate`) on manual runs and on the `operate_schedule` cron answer
  (GitLab: scheduled pipelines, since "Run pipeline" deploys). Tokens are
  secrets named after the tool's env var. Each runs `*:<stage>`; tools are
  `<tool>:<stage>` tasks (e.g. `ruff:lint`), and any other action
  (`zensical:serve`, `gh:check`) stays out of the pipeline. `<stage>_enabled`
  keeps the stage or not (mise task and CI job); `<stage>_commands`, when given,
  replaces its tools with a `run` list, the same locally and in CI. A stage
  without tools does nothing: its `depends` is `optional`, because `*:<stage>`
  fails otherwise. CI only calls `mise run <stage>`.
- Questions live in `.copier/questions/`: `common.yml` (`ci` first because
  choice validators can use it, `presets`, whose choice values are tool lists,
  merged into `tools`' default (without the tools `ci` refuses); a preset's list
  never changes, since Copier checks the stored answer against the choices on
  update: a new list is a new preset, the `tools` multi-select,
  `<stage>_enabled` and `<stage>_commands`, `jobs`, `customize_tools`, mirrors),
  one file per tool `tools/<tool>.yml`, then `computed.yml` (values computed
  from the answers, `when: false`: never asked nor saved), included by
  `copier.yml`. Tool questions are named `<tool>_version`, `<tool>_config`
  (tools with a brigade-owned config) and `<tool>_<action>_command`,
  `when: customize_tools`, with an empty default: an answer overrides brigade's
  value and stays until changed, an empty answer takes brigade's value in the
  Jinja file. Keep Jinja out of other files that hold pins (Renovate parses
  them): conditions go in file names or in pin-free files.
- Add a stage (build, release, publish, deploy...) only when a tool needs it.
- brigade-owned CI files only install mise and call `mise run <task>`.
  Forgejo (`ci: forgejo`) uses Gitea's files (`.forgejo/workflows/`, the same
  `.brigade/ci/gitea/actions/`), with its own Releasaurus forge and Renovate
  platform. GitHub/Gitea: each workflow checks out, then calls its stage's
  composite action `.brigade/ci/<ci>/actions/<stage>` (mise via `actions/mise`,
  `mise run <stage>`, the stage's env; secrets as inputs, since actions cannot
  read them); `publish` and `deploy` call mise-action itself with
  `cache: false`, because
  jactionlint does not follow a nested action's inputs; each CI platform lints
  its own files (`jactionlint:lint` with its default profile, `gitlab-ci:lint`):
  workflows pin actions by SHA with a version comment, set `permissions:`,
  `timeout-minutes` and `concurrency:`, and restore no cache where they publish
  or deploy (`publish`, `deploy`).
- Each enabled stage is one CI job on Linux, running `mise run <stage>` (or,
  when the `jobs` answer lists named jobs for the stage (`{name, run}`;
  `split_stages`, a computed question in `.copier/questions/computed.yml`), one
  job per job: each is a hidden `<stage>-<name>` task in `.brigade/stages.toml`
  running its commands in order (the stage task runs all of them in order
  locally), a static matrix (GitHub/Gitea, rendered by Jinja) or a
  `parallel:matrix` (GitLab) runs `mise run <stage>-<name>`, and on GitHub/Gitea
  a last job named after the stage is its check; the shared jobs are Jinja
  snippets in `.copier/ci/`, outside `template/`), with no `needs` between
  stages: `lint`, `build`, `test` on pull/merge requests only, `release` on
  pushes to the default branch, `publish` on `X.Y.Z` tags and manual runs,
  `deploy` after it (the one exception to no `needs`, through a dispatch) and
  on manual runs, the
  same on every platform. GitHub/Gitea: one workflow per stage,
  `workflows/{% if <stage>_enabled %}<stage>.yml{% endif %}`, plain YAML
  (Renovate reads its `uses:`), except `operate.yml.jinja` for its schedule.
  GitLab: `.gitlab-ci.yml` includes `.brigade/ci/gitlab/*.yml` and the project's
  `.gitlab/ci/*.yml` (when it exists), whose order is not guaranteed: no file
  may redefine a key of another (`default.yml` holds the image, cache and
  `before_script`).
- Linters and formatters are mise tools, not project dependencies.
- `brigade:*` tasks are brigade's own helpers (`brigade:update`), not pipeline
  stages, except `brigade:lint`, the task of the
  `brigade` tool (selected by default): it renders the template at `_commit`
  (`HEAD` for a local `_src_path`) with the answers and fails when a
  brigade-owned file differs (`.brigade/scripts/brigade_lint.py`); it also
  prints a notice, never a failure, when `copier check-update` finds a newer
  release. `renovate:operate` sets `RENOVATE_CONFIG_FILE` to
  `.brigade/configs/renovate.json` (global config, Jinja: what it updates is the
  `renovate_updates` answer, `brigade` by default, also `dependencies` (the
  project's, `config:recommended`) and `template` (brigade's `template/`);
  `onboarding: false`, so no `renovate.json` is needed): a regex manager on
  `.brigade/copier/answers.yml`
  (`_commit`, `_src_path`, `git-tags`) whose `postUpgradeTasks` undo Renovate's
  `_commit` change and run
  `mise run brigade:update -- --defaults --vcs-ref <version>`, so each release
  opens an update PR on every forge. Every other task is `<tool>:<action>`.
  `act:test` and `gitlab-ci-local:test` replay the CI in Docker and do nothing
  inside a replay (`ACT`, `GITLAB_CI` set), so the replayed test job does not
  loop.
- Pin versions (mise, tools, Copier). Renovate keeps them up to date
  (`.brigade/configs/renovate.json`, from the `template` part of
  `renovate_updates` in brigade's answers; no config of its own): a new pin
  outside a standard mise/CI location needs a matching `customManagers` entry
  there, in the template, which applies to brigade after a release and its
  update. Generated projects get new versions
  through a brigade release and `mise run brigade:update`. Renovate only reads
  `template/` (`includePaths`), in one `fix:` PR, and brigade's own
  `.brigade/copier/answers.yml`, whose `ci:` PR runs `brigade:update` on each
  release: brigade's generated files follow that way, its other pins (Copier and
  pytest in tests and docs) are updated by hand.
- Keep it simple: add a file or an option only when it is needed.
- Code, comments and help texts in English.
- PRs are squash-merged with the PR title as commit message, so PR titles follow
  Conventional Commits (merge commits made the release tool list changes twice).
- Commits follow Conventional Commits. Releases are made by merging the release
  PR, which tags `X.Y.Z`; Copier uses these tags as template versions.

## Testing

brigade is generated by brigade: `mise run brigade:update` updates its
`.miserc.toml`, `.brigade/` and `.github/workflows/` files from the latest
release (answers in `.brigade/copier/data.yml`, with some commands adapted to
this repo; lint settings for `template/` and `.ctt/` in `.brigade/configs/`).
Its own env lives in `mise.toml`; it is tested only with the tools it ships (no
hand-written test scripts), added as needed, except `tests/e2e/`:
end-to-end tests on a local forge with its runner (`tests/fixtures/`, Docker
Compose, local only), as Molecule's (`tests/e2e/phases.py`:
`mise run e2e:converge <forge> [type...]` (prepare, converge, verify; resumes),
`e2e:destroy`, `e2e:test <forge|all> [type...]`, the `e2e` skill), one
scenario per project type of `tests/e2e/projects.py`, its files in
`tests/fixtures/projects/<type>/` (linted with this repo); Nexus for publish,
a k3s cluster and an SSH server for the deploys; their state and notes in
`.forges/` (each step, the failed jobs' logs), and a summary forge × type
after `e2e:test all`. `mise run lint` checks this repo
(yamllint, jactionlint, zizmor, taplo, editorconfig-checker, gitleaks, typos,
ruff, ty, rumdl, lychee, ls-lint, Renovate config schema). `mise run build`
builds the documentation site (`docs/`, `zensical.toml`) with Zensical in strict
mode, which fails on broken links; `mise run deploy` pushes it to the `gh-pages`
branch (CI: after the publish of each `X.Y.Z` tag, made with the
`RELEASAURUS_GITHUB_TOKEN` secret, and manual runs; a `docs:` change waits for
the next release or a manual run).
`mise run test` renders each `ctt.toml` variant into `.ctt/` (`ctt:test`),
creates a real project there with the ecosystem's tool, then runs its mise
tasks. In CI, each variant is its own job (`jobs` in `.brigade/copier/data.yml`:
add a new variant there too); `mise run ctt:test -- -t .ctt/<variant>` runs one
locally. Some variants are recipes, documented in `docs/recipes.md`: a whole
project with every tool it uses, up to its publish or deploy (`python-github`:
a package published to a local PyPI in Docker; `go-github`: binaries built by GoReleaser
in snapshot mode; `python-docker-github`: a Python app shipped as an image;
`node-github`: a TypeScript library published to a local npm registry;
`react-github`: a Vite React app with ESLint and Vitest; `angular-github`: an
Angular app with Vitest and CodeceptJS end-to-end tests); the others cover CI
platforms and the rest of the catalog. ctt only sees files tracked by git. The
variants do not select `act` or `gitlab-ci-local` (a replay ran their stages a
second time); their CI files are only linted, except in the `template-*`
variants, which split their test stage (`jobs`) and replay it. The Docker,
Ansible and publishing variants need a running Docker. User-facing changes
(questions, tasks, CI files) update the matching page in `docs/`; the README
stays a short summary. brigade's CI runs these tests on Linux only: the rule
above on macOS and Windows is no longer tested.
