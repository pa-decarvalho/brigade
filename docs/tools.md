# Tools

*The stations of the brigade, and who works at each one.*

Pick your tools in one list when applying brigade. A tool brings its version and
all its tasks, in one file: `.brigade/conf.d/<tool>-brigade.toml`, listed in
`.miserc.toml`. Its tasks run at the project root.

Tasks are named `<tool>:<action>`. Stages run in this order: `lint`, `build`,
`test`, `release`, `deploy`, `operate`, and each runs every `<tool>:<stage>`
task. Any other action, such as `zensical:serve`, stays out of the pipeline.

## Stages

For each stage, Copier asks whether to keep it, then its commands.

- Answer no to remove the stage: no mise task, no CI job.
- Leave the commands empty to run all the stage's tools. A stage without tools
  does nothing.
- Give commands to run them instead, in order, locally and in CI:

```yaml
lint_commands: ["mise run ruff:lint", "mise run typos:lint"]
```

## Presets

The `presets` question, asked before `tools`, pre-selects tools: tick or untick
them in `tools` before going on. Only `tools` decides what the project gets; a
preset changed in a later brigade release does not change existing projects. A
preset's tools never change: its answer is checked against the choices on each
`brigade:update`, so a new list is a new preset. A preset's answer is its tool
list, e.g. `presets: [[ruff, ty, pytest, uv]]` in `.brigade/copier/data.yml`.

| Preset | Tools |
|---|---|
| `python` | `ruff`, `ty`, `pytest`, `uv` |
| `go` | `golangci-lint` |
| `node` | `node`, `biome` (JavaScript or TypeScript) |
| `rust` | `rust` |
| `terraform` | `tflint`, `checkov`, `opentofu` |
| `ansible` | `ansible-lint`, `molecule`, `ansible` |
| `shell` | `shellcheck`, `shfmt` |
| `docker` | `hadolint` |
| `lua` | `stylua` |
| `docs` | `rumdl`, `zensical`, `pages` (GitHub, GitLab) |
| `copier-template` | `ctt` |
| `security` | `osv-scanner`, `checkov`, `zizmor` (GitHub) |
| `ci` | `act` (GitHub, Gitea) or `gitlab-ci-local` (GitLab): replays the CI |
| `maintenance` | `renovate`, `releasaurus` |

## Catalog

`brigade`, `yamllint`, `gitleaks` and `typos` are selected by default.

| Tool | Task | Command |
|---|---|---|
| `brigade` | `brigade:lint` | Fails when a brigade-owned file was edited or deleted: see [brigade](#brigade) |
| `yamllint` | `yamllint:lint` | `yamllint --strict` ([config](#tool-configs)) |
| `gitleaks` | `gitleaks:lint` | `gitleaks git` (history and staged changes) |
| `typos` | `typos:lint` | `typos`, without `.mise/` (mise's lock sidecars) ([config](#tool-configs)) |
| `editorconfig-checker` | `editorconfig-checker:lint` | `editorconfig-checker`, without `.mise/` (mise's lock sidecars) (needs your `.editorconfig`; [config](#tool-configs)) |
| `taplo` | `taplo:lint` | `taplo fmt --check` on `.brigade/*.toml`, `.brigade/*/*.toml` and `.miserc.toml` ([config](#tool-configs)) |
| `renovate` | `renovate:lint` | `check-jsonschema --builtin-schema vendor.renovate` on your Renovate config, wherever Renovate reads it (`renovate.json`, `.github/renovate.json5`, `.renovaterc`...); none: passes |
| | `renovate:operate` | `renovate` (needs `RENOVATE_TOKEN` and `RENOVATE_REPOSITORIES`: see [operate](#operate)): a PR updating brigade on each release, and what `renovate_updates` adds ([config](#tool-configs)) |
| `ruff` | `ruff:lint` | `ruff check && ruff format --check` ([config](#tool-configs)) |
| `ty` | `ty:lint` | `ty check` ([config](#tool-configs)). It reads the project's `.venv` for its dependencies: CI has none, so a project with dependencies creates it first (`ty_lint_command: "uv sync && ty check --config-file .brigade/configs/ty.toml"`), else their imports fail (`import-not-found`) |
| `shellcheck` | `shellcheck:lint` | `shellcheck` on every `*.sh` and `*.bash` (outside hidden folders); none: nothing to check |
| `shfmt` | `shfmt:lint` | `shfmt --diff` on the same files (style: your `.editorconfig`) |
| `rumdl` | `rumdl:lint` | `rumdl check --no-cache .` (Markdown: rumdl's rules, lines of 80 columns; `CHANGELOG.md`, written by the release tool, skipped; HTML only without a Markdown equivalent, or in `<p>` and `<h1>` blocks for a centered README header; [config](#tool-configs)) |
| `markdownlint` | `markdownlint:lint` | `markdownlint-cli2 "**/*.md"`, without `.mise-data/`, `.venv/` and `node_modules/`; reads your `.markdownlint-cli2.*` or `.markdownlint.*`. Same rules as `rumdl`: pick one |
| `vale` | `vale:lint` | `vale sync && vale .` (prose in Markdown, with Vale's built-in style), without `.mise-data/`, `.venv/` and `node_modules/` ([config](#tool-configs); `vale sync` downloads the style packages it lists) |
| `lychee` | `lychee:lint` | `lychee --no-progress .` (links in Markdown, HTML and text files, outside hidden folders and `CHANGELOG.md`, whose release PR links to a tag not made yet); reads your `lychee.toml`. Checks external links: a dead link fails an unchanged project |
| `codespell` | `codespell:lint` | `codespell`, outside hidden folders ([config](#tool-configs)) |
| `cspell` | `cspell:lint` | `cspell lint .`, outside hidden folders ([config](#tool-configs)). Checks every word against its dictionaries, unlike `typos` and `codespell`: add your project's words to the config's `words`, listed by `mise exec -- cspell lint --words-only --unique .` |
| `ls-lint` | `ls-lint:lint` | `ls-lint`: file and folder names ([config](#tool-configs): set your naming rules, none until then) |
| `sqlfluff` | `sqlfluff:lint` | `sqlfluff lint` on every `*.sql` (outside hidden folders); none: nothing to check ([config](#tool-configs): set your SQL dialect) |
| `prettier` | `prettier:lint` | `prettier --check .` (JavaScript, TypeScript, JSON, YAML, Markdown, CSS...), without `.mise-data/`, `.mise/`, `.venv/` and `.brigade/`; reads your `.prettierrc` and `.prettierignore` |
| `biome` | `biome:lint` | `biome ci .` (JavaScript, TypeScript, JSON, CSS, Markdown: lint and formatting), without what git ignores, `.mise-data/`, `.mise/`, `.venv/` and `.brigade/` ([config](#tool-configs)). Formats the same files as `prettier`: pick one |
| `clang-format` | `clang-format:lint` | `clang-format --dry-run --Werror` on every C and C++ file (outside hidden folders), with your `.clang-format` (else LLVM style); none: nothing to check |
| `trivy` | `trivy:lint` | `trivy fs .`: vulnerable dependencies and secrets, without `.mise-data/` and `.mise/` ([config](#tool-configs)); downloads its vulnerability database, so a new vulnerability can fail an unchanged project |
| `osv-scanner` | `osv-scanner:lint` | `osv-scanner scan source --recursive` on your lockfiles (`uv.lock`, `package-lock.json`...), without `.mise-data/` and `.mise/` (the tools' locked dependencies); queries osv.dev, so a new vulnerability can fail an unchanged project |
| `golangci-lint` | `golangci-lint:lint` | `golangci-lint run` (needs Go: the `go` tool, or `go` pinned in your `mise.toml`) |
| `revive` | `revive:lint` | `revive -set_exit_status ./...` (Go, golint's rules; faster than `golangci-lint`, which can run revive too), outside hidden folders; `-config revive.toml` in your command for your rules |
| `tflint` | `tflint:lint` | `tflint --recursive` (Terraform) |
| `opentofu` | `opentofu:lint` | `tofu fmt -check -recursive` (Terraform and OpenTofu formatting), outside hidden folders |
| `checkov` | `checkov:lint` | `checkov` on the project (Terraform, Kubernetes, Dockerfiles, workflows...), with no download from Prisma Cloud and without reading the repository's settings through the GitHub API ([config](#tool-configs)) |
| `cfn-lint` | `cfn-lint:lint` | `cfn-lint` on every YAML or JSON file holding `AWSTemplateFormatVersion` (CloudFormation and SAM templates, outside hidden folders); none: nothing to check |
| `dotenv-linter` | `dotenv-linter:lint` | `dotenv-linter check --recursive .` (`.env` files), without `.mise-data/` |
| `stylua` | `stylua:lint` | `stylua --check .` (Lua) |
| `ansible-lint` | `ansible-lint:lint` | `ansible-lint --strict` ([config](#tool-configs)) |
| `hadolint` | `hadolint:lint` | `hadolint` on every `*Dockerfile*` and `*Containerfile*` (outside hidden folders); none: nothing to check |
| `zizmor` | `zizmor:lint` | GitHub: `zizmor --offline .` audits the workflows and actions for security issues. brigade's own files pass; their `# zizmor: ignore[...]` comments keep `./` for local actions (act has no `$/` syntax) and allow fixed values written to `GITHUB_ENV` |
| `go` | `go:build` | Installs Go; `go build ./...` (a main package at the root writes its binary there: ignore it) |
| | `go:test` | `go test ./...` |
| `rust` | `rust:lint` | Installs Rust (rustup, then the toolchain with rustfmt and Clippy); `cargo fmt --check && cargo clippy --all-targets -- -D warnings` |
| | `rust:build` | `cargo build` (into `target/`: ignore it) |
| | `rust:test` | `cargo test` |
| | `rust:deploy` | With `cargo_publish: true`: `cargo publish`, the crate to crates.io or another registry on each release: see [deploy](#deploy) |
| `docker` | `docker:build` | GitHub, Gitea, none: `docker build .` (Docker from the machine or the runner) |
| | `docker:deploy` | Builds the image of the tag and pushes `X.Y.Z` and `latest` to its registry: see [deploy](#deploy) |
| `node` | `node:lint` | Installs Node.js; `npm ci && npm run lint --if-present`, for linters that are project dependencies (ESLint and its plugins) |
| | `node:build` | `npm ci && npm run build --if-present` (JavaScript or TypeScript: your `package.json` scripts; needs `package-lock.json`) |
| | `node:test` | `npm ci && npm test --if-present` |
| | `node:deploy` | With `npm_publish: true`: `npm ci && npm publish`, the package to npm or another registry on each release: see [deploy](#deploy) |
| `uv` | `uv:build` | `uv build` (into `dist/`) |
| | `uv:deploy` | With `uv_publish: true`: `uv build --clear && uv publish`, the package to PyPI or another index on each release: see [deploy](#deploy) |
| `zensical` | `zensical:build` | `zensical build --strict` (needs your `zensical.toml` and `docs/`: `zensical new .`) |
| | `zensical:serve` | `zensical serve --open`, to preview the site |
| `container-structure-test` | `container-structure-test:test` | GitHub, Gitea, none: builds the image, then checks its content with your tests ([config](#tool-configs): a placeholder test until you write yours) |
| `pytest` | `pytest:test` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `molecule` | `molecule:test` | `molecule test --all`, with the Docker driver (needs your `molecule/<scenario>/molecule.yml` and Docker: see [Molecule](#molecule)) |
| | `molecule:converge`, `molecule:verify`, `molecule:destroy` | `molecule converge`, `verify`, `destroy`, while writing a role |
| | `molecule:reconverge` | `molecule:destroy`, then `molecule converge`, to converge from scratch |
| | `molecule:login` | `molecule login`, a shell in the instance |
| `ctt` | `ctt:test` | `ctt`, for a Copier template (needs your `ctt.toml`; render the variants into `.ctt/`, which `yamllint` skips) |
| `codeceptjs` | `codeceptjs:test` | `npm ci`, Chromium (`npx playwright install --with-deps chromium`), then `npx codeceptjs run` with your `codecept.conf.*`; none: nothing runs. Needs `node`: see [codeceptjs](#codeceptjs) |
| `releasaurus` | `releasaurus:release` | `releasaurus release && releasaurus release-pr --tag-prefix ''`: see [release](#release) |
| `goreleaser` | `goreleaser:deploy` | GitHub, GitLab: `goreleaser release --clean`, the Go binaries attached to the release ([config](#tool-configs)): see [deploy](#deploy) |
| `pages` | `pages:deploy` | Runs the `*:build` tasks, then publishes the `pages_dir` folder (`site/` by default). GitHub: `ghp-import -n -p -f site`. GitLab: the job publishes it |
| `ansible` | `ansible:deploy`, `ansible:operate` | `ansible-playbook -i inventory playbooks/deploy.yml` (`operate.yml`): see [Ansible](#ansible) |
| `act` | `act:test` | GitHub, Gitea: `act pull_request` replays the pull request workflows in Docker: see below |
| `prek` | `prek:install` | `prek install --force`: the git hooks of `.brigade/configs/prek.yaml`, in place of any hook already there (local use, not a stage): see [prek](#prek) |
| | `prek:run` | `prek run --all-files`: the hooks on every file |
| `gh` | `gh:check`, `gh:setup` | GitHub: checks the repository's settings for the selected tools, or changes them (local use, not a stage): see [Repository settings](#repository-settings) |
| `glab` | `glab:check`, `glab:setup` | GitLab: the same for the project |
| `tea` | `tea:check`, `tea:setup` | Gitea, Forgejo: the same for the repository |
| `gitlab-ci-local` | `gitlab-ci-local:test` | GitLab: `gitlab-ci-local` replays the merge request pipeline in Docker: see below |

The CI platform adds its own linter (`jactionlint:lint`, `gitlab-ci:lint`): see
[CI platforms](ci.md).

## Tool configs

Tools that read a config file get one in `.brigade/configs/`, created when the
tool is selected; removing the tool from `tools` removes it. Paths in it are
relative to the project root.

- **brigade's settings** (the folders to skip, such as `.mise-data/` and
  `.mise/`): brigade-owned, like the rest of `.brigade/`. `brigade:update`
  updates them and `brigade:lint` fails when one is edited. For your own
  settings, write your own file (start from a copy of brigade's, or extend it
  where the tool allows: `extend` in ruff, `import` in cspell, `extends` in
  yamllint, biome and rumdl), and set `<tool>_config` to its path (see
  [Customize](#customize-a-version-or-a-command)); it then keeps your settings,
  and brigade's later changes are yours to follow.
- **Your content** (`goreleaser`, `container-structure-test`, `ls-lint`,
  `sqlfluff`, `prek`: your builds, tests, naming rules, SQL dialect, hooks):
  created once with a starting point, then yours: `brigade:update` keeps it,
  `brigade:lint` skips it.

| Tool | Config | Owner | Your usual config file, with brigade's |
|---|---|---|---|
| `yamllint` | `.brigade/configs/yamllint.yml` | brigade's (`yamllint_config`) | `.yamllint`: not read |
| `ruff` | `.brigade/configs/ruff.toml` | brigade's (`ruff_config`) | `[tool.ruff]` in `pyproject.toml`, `ruff.toml`: not read |
| `ty` | `.brigade/configs/ty.toml` | brigade's (`ty_config`) | `[tool.ty]` in `pyproject.toml`, `ty.toml`: not read |
| `typos` | `.brigade/configs/typos.toml` | brigade's (`typos_config`) | `_typos.toml`, `typos.toml`: still read, both apply |
| `taplo` | `.brigade/configs/taplo.toml` | brigade's (`taplo_config`) | `taplo.toml`: not read |
| `rumdl` | `.brigade/configs/rumdl.toml` | brigade's (`rumdl_config`) | `.rumdl.toml`: not read |
| `editorconfig-checker` | `.brigade/configs/editorconfig-checker.json` | brigade's (`editorconfig_checker_config`) | `.editorconfig-checker.json`: not read (`.editorconfig` still is) |
| `ansible-lint` | `.brigade/configs/ansible-lint.yml` | brigade's (`ansible_lint_config`) | `.ansible-lint`: not read |
| `vale` | `.brigade/configs/vale.ini` | brigade's (`vale_config`) | `.vale.ini`: not read |
| `codespell` | `.brigade/configs/codespell.cfg` | brigade's (`codespell_config`) | `.codespellrc`: not read |
| `biome` | `.brigade/configs/biome-brigade.jsonc` | brigade's (`biome_config`) | `biome.json`, `biome.jsonc`: not read |
| `trivy` | `.brigade/configs/trivy.yaml` | brigade's (`trivy_config`) | `trivy.yaml`: not read |
| `prek` | `.brigade/configs/prek.yaml` | yours | `.pre-commit-config.yaml`: not read |
| `sqlfluff` | `.brigade/configs/sqlfluff.cfg` | yours | `.sqlfluff`: still read, the brigade file wins (its `dialect`) |
| `checkov` | `.brigade/configs/checkov.yml` | brigade's (`checkov_config`) | `.checkov.yaml`: not read |
| `goreleaser` | `.brigade/configs/goreleaser.yaml` | yours | `.goreleaser.yaml`: not read |
| `container-structure-test` | `.brigade/configs/container-structure-test.yaml` | yours | none: your image's tests |
| `cspell` | `.brigade/configs/cspell.yaml` | brigade's (`cspell_config`) | `cspell.json`, `.cspell.json`...: still read, both apply |
| `ls-lint` | `.brigade/configs/ls-lint.yml` | yours | `.ls-lint.yml`: not read |
| `releasaurus` | `.brigade/configs/releasaurus.toml` | brigade's (`releasaurus_config`) | `releasaurus.toml`: not read |
| `renovate` | `.brigade/configs/renovate.json` | brigade's (`renovate_config`) | `renovate.json`, `.github/renovate.json5`...: still read, yours wins |

Other tools read their usual config file (`.golangci.yml`, `.tflint.hcl`,
`stylua.toml`, `lychee.toml`, `.markdownlint-cli2.yaml`, `.prettierrc`,
`.clang-format`...).

## codeceptjs

`codeceptjs` runs end-to-end tests: [CodeceptJS](https://codecept.io/) drives
Chromium through its Playwright helper, against your app. CodeceptJS and
Playwright are your dev dependencies (`npm install -D codeceptjs playwright`,
then `npx codeceptjs init`): the helper loads Playwright next to CodeceptJS, so
mise cannot install them apart, and their versions are in your
`package.json`. It needs the `node` tool, and waits for `node:test`, which also
runs `npm ci`.

Your `codecept.conf.*` holds your tests, your app's URL, and the server they
need: CI runs each stage in a fresh job, without the build stage's output, so
start it in `bootstrap` (and stop it in `teardown`), e.g. a static server on
your build, or `ng serve`. The task installs Chromium, and on Linux its system
packages (with `sudo` outside CI). Add CodeceptJS's `output` folder (e.g.
`e2e/output/`) to your `.gitignore`.

## prek

`prek` runs git hooks, for local use; it stays out of the pipeline, which CI
runs anyway. [prek](https://prek.j178.dev/) is a faster, single-binary
pre-commit: same config format, same hooks. Its config,
`.brigade/configs/prek.yaml`, is yours: brigade creates it once, then never
changes it. It starts with prek's builtin hooks, fast and offline, on the
committed files:

- `check-merge-conflict`: conflict markers, also those `brigade:update` leaves;
- `check-added-large-files`: files over 500 KiB;
- `check-case-conflict`, `check-illegal-windows-names`: names that break on
  macOS or Windows;
- `mixed-line-ending`, `trailing-whitespace`, `end-of-file-fixer`: they fix the
  files and fail the commit; stage the fixes and commit again.

Then `mise run lint`, the lint stage as in CI. Add hooks from the pre-commit
ecosystem there (they download their own tools), or `repo: local` hooks that
call your mise tasks.

`mise run prek:install` writes the hook into `.git/hooks/`, each clone once, in
place of any hook already there (`--force`): the hook of brigade 0.25 and
earlier, or one you wrote, whose commands go in `prek.yaml` as `repo: local`
hooks. The hook calls this prek by its install path, so run it again after a
prek version change. `mise run prek:run` runs the hooks on every file. Skip them
for one commit with `git commit --no-verify`.

## Repository settings

Each forge's CLI comes with a check, for local use (not a stage): `gh:check`
(GitHub), `glab:check` (GitLab), `tea:check` (Gitea, Forgejo). It reads the
repository's settings that the selected tools need, with your login
(`gh auth login`, `glab auth login`, `tea login add`), changes nothing, and
fails when a required one is missing, with where to change it:

| Tool | GitHub | GitLab | Gitea |
|---|---|---|---|
| always | squash merge only, the pull request title as the commit | squash commits required | squash merge only |
| `releasaurus` | `RELEASAURUS_GITHUB_TOKEN`, else Actions allowed to create pull requests | `RELEASAURUS_GITLAB_TOKEN` | `RELEASAURUS_GITEA_TOKEN` (advised) |
| `renovate` | `RENOVATE_TOKEN`; auto-merge allowed with `renovate_automerge` | `RENOVATE_TOKEN`; `RENOVATE_GITHUB_COM_TOKEN` and an active pipeline schedule (advised) | `RENOVATE_TOKEN`; `RENOVATE_GITHUB_COM_TOKEN` (advised) |
| `pages` | Pages published from `gh-pages` | Pages enabled | |

Secrets and CI/CD variables are looked up in the repository and its
organization or group. Only admins (maintainers on GitLab) can list them: for
others, they show as `unknown`.

`gh:setup`, `glab:setup` and `tea:setup` change the missing settings that need
no secret value (merge method, auto-merge, Actions allowed to create pull
requests, Pages once the first deploy has pushed `gh-pages`), then report the
others as the check does: set the secrets yourself, as printed.
Run it once on a new repository, as an admin.

`mise run brigade:update` runs the check at the end, outside CI, as a notice
that never fails the update: a new tool may need a new setting.

## Platforms

brigade's own files run on Linux, macOS and Windows; each tool runs where it is
supported. CI runs on Linux, so these limits only matter for local runs
(`mise run <stage>`, git hooks). Known limits on Windows:

- `taplo`: fails on checkouts with CRLF line endings
  (`git config core.autocrlf false`, or `* text eol=lf` in `.gitattributes`).
- `ctt`: ctt 3.0.0 fails inside a git repository.
- `rust`: needs the MSVC build tools (Visual Studio Build Tools, C++ workload)
  to link.
- `ansible-lint`, `molecule`, `ansible`: Ansible does not run on Windows (use
  WSL).
- `act`, `gitlab-ci-local`, `docker`, `container-structure-test`: need Docker
  with Linux containers (Docker Desktop, WSL 2).

## brigade

`brigade:lint` renders the template at the version of
`.brigade/copier/answers.yml`, with your answers, into a temporary folder, and
compares it with your brigade-owned files (`.miserc.toml`, `.brigade/`, the
generated workflows or `.gitlab-ci.yml`). An edited or deleted file fails the
lint stage, locally, in the git hook and in CI: `brigade:update` would overwrite
it. Run `mise run brigade:update` to restore them. An edited
`.brigade/copier/data.yml` fails it too until `brigade:update` applies it (see
[Changing answers](questions.md#changing-answers)).

It also tells when a newer brigade release is out (`copier check-update`),
without failing: run `mise run brigade:update`, or let
[Renovate](#brigade-updates) open the PR.

It needs access to the template (`gh:pa-decarvalho/brigade`, through git) on
each run. Offline, behind a proxy, or to edit a generated file on purpose,
remove `brigade` from your tools.

## release

CI runs this stage on its own, on pushes to the default branch: `lint`,
`build` and `test` already ran on the pull request.

With `releasaurus`, [Releasaurus](https://releasaurus.rgon.io/) reads the
Conventional Commits since the last tag and opens or updates a release pull
request, with the next version and a `CHANGELOG.md`. Once you merge it, the next
run tags `X.Y.Z` (no `v`) and publishes the release on your forge. It works on
GitHub, GitLab, Gitea and Forgejo.

Its config, `.brigade/configs/releasaurus.toml` (brigade's, read from the
default branch through the forge's API, so commit it):

- Releases on `feat`, `fix`, `perf`, `revert` and breaking changes only: other
  commits (`ci:`, `docs:`, `chore:`...) are left out of the version and
  `CHANGELOG.md`.
- Tags `X.Y.Z`, with no `v`.
- Updates your manifests to the new version in the release pull request
  (`release_type`), from your tools: `uv` → `pyproject.toml`, `node` →
  `package.json` and `package-lock.json`, `rust` → `Cargo.toml` and
  `Cargo.lock`, `go` → `version.go`. With none or several of them, none.
  `releasaurus_release_type` picks another (`java`, `php`, `ruby`, `helm`...) or
  `none` (see [Customize](#customize-a-version-or-a-command)). `uv.lock` is not
  updated: `uv` rewrites it on the next `uv lock` or `uv run`.

Two workflows (`releasaurus_workflow`, see
[Customize](#customize-a-version-or-a-command)):

- `pr` (default): a release pull request to merge; the next run tags it.
- `direct`: each push with a releasable commit is released at once, with no
  pull request (`releasaurus release-direct`): the version and `CHANGELOG.md`
  are committed to the default branch, then tagged. With the CI's own token, the
  tag starts no CI: on GitHub and Gitea, set the bot token below so that
  `deploy` runs. When the default branch is protected, that token must be
  allowed to push to it (the CI's own token cannot be):
  - GitHub: add the token's owner to the bypass list (ruleset: "Repository
    admin"; classic branch protection: leave "Do not allow bypassing the above
    settings" off, for admins).
  - GitLab: "Allowed to push and merge" on the protected branch includes the
    token's role (Maintainers by default: a project token with the Maintainer
    role).
  - Gitea, Forgejo: add the token's user to the branch protection's push
    whitelist.

For your own settings (prereleases, a monorepo, changelog options), set
`releasaurus_config` to your file, with `tag_prefix = ""` in its `[[package]]`
to keep the tags brigade's CI deploys. See
[Releasaurus configuration](https://releasaurus.rgon.io/configuration.html).

On GitHub and Gitea, it works with the CI's own token, with three manual
steps:

- GitHub: allow the workflow token to open pull requests (Settings → Actions →
  General → "Allow GitHub Actions to create and approve pull requests", off in
  new repositories), else the release fails with
  `Failed to create pull request`:

  ```sh
  gh api -X PUT repos/<owner>/<repo>/actions/permissions/workflow \
    -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true
  ```

- The release pull request starts no checks (GitHub shows failed runs with no
  job): re-run them, or merge with a bypass of the required checks.
- The tag starts no CI: run `deploy` by hand after each release.

A bot token avoids all three: the pull request and the tag start the CI as
usual. GitLab needs the token: until it is set, the first pipeline on the
default branch fails (`API authentication failed: Token not provided`); once it
is, retry the failed `release` job ("Run pipeline" only deploys). A project
token, created and stored without being printed:

```sh
glab token create releasaurus --access-level maintainer --scope api \
  --scope write_repository --duration 365d --output text \
  | glab variable set RELEASAURUS_GITLAB_TOKEN --masked
```

Merge pull requests with squash, the title being the commit: GitLab's default
merge commit can leave a branch's older commits out of the next release.

| CI | Secret or CI/CD variable (bot token) | Scopes |
|---|---|---|
| GitHub | `RELEASAURUS_GITHUB_TOKEN` | Contents, Issues and Pull requests: read and write |
| GitLab | `RELEASAURUS_GITLAB_TOKEN` | `api`, `write_repository` |
| Gitea, Forgejo | `RELEASAURUS_GITEA_TOKEN` | repository, issue and misc: read and write |

## deploy

CI runs this stage on its own, on tags `X.Y.Z` (or `vX.Y.Z`), such as the ones
Releasaurus pushes, and on a manual run, to deploy without a release: for
example to fix a typo in the documentation.

`pages` needs GitHub or GitLab, and a `<tool>:build` task that writes the site
to the `pages_dir` folder (`site` by default): `zensical`, `node` (a Vite app:
`pages_dir: dist`), or your own (for example `mkdocs:build`, see
[Custom tasks](custom-tasks.md)).

- **GitHub**: the site is pushed to the `gh-pages` branch. In Settings → Pages,
  choose "Deploy from a branch" and `gh-pages`.
- **GitLab**: the job publishes the `pages_dir` folder with `pages.publish`
  (GitLab 17.10 or later). The site is private by default, even in a public
  project: in Settings → General → Visibility, set Pages to "Everyone"
  (`glab api -X PUT projects/:id -f pages_access_level=enabled`).

The site's base path depends on the forge: GitHub serves
`https://<owner>.github.io/<repo>/`; GitLab serves it at the root of a unique
domain, `https://<project>-<hash>.gitlab.io/` (on by default; without it,
`https://<namespace>.gitlab.io/<project>/`, whose certificate fails when the
namespace has a dot). Set it in your build: Vite's `base`, Angular's
`baseHref`, zensical's `site_url`. Your end-to-end tests serve the build under
the same base, so they pass either way: check the deployed site once.

Add `site/` and `.cache/` to your `.gitignore`.

`goreleaser` builds the Go binaries for Linux, macOS and Windows and attaches
the archives and their checksums to the release Releasaurus made for the tag (it
needs Go: the `go` tool). GitHub: with the workflow token. GitLab: add a
`GITLAB_TOKEN` CI/CD variable (a token with the `api` scope); a self-managed
GitLab also needs its URLs in the config (`gitlab_urls`). Add `dist/` to your
`.gitignore`. A manual run needs a tag at the checked out commit.

`node:deploy` (the `node` tool, with the `npm_publish: true` answer) publishes
the package with `npm publish`, once per tag: the version is the one in
`package.json`, which Releasaurus bumps in the release PR. Build it in a
`prepublishOnly` script (`npm run build`). In CI, add an `NPM_TOKEN` secret
(CI/CD variable on GitLab), and give npm the line that reads it in your
`.npmrc`: `//registry.npmjs.org/:_authToken=${NPM_TOKEN}` (another registry: its
host, and `publishConfig.registry` in `package.json`). A scoped public package
needs `"publishConfig": {"access": "public"}`. A version already published
fails: a manual run on the same tag does nothing new.

`rust:deploy` (the `rust` tool, with the `cargo_publish: true` answer) publishes
the crate with `cargo publish`, once per tag: the version is the one in
`Cargo.toml`, which Releasaurus bumps in the release PR. In CI, add a
`CARGO_REGISTRY_TOKEN` secret (CI/CD variable on GitLab): a crates.io API token
with the `publish-update` scope (and `publish-new` for the first release).
Another registry: `publish = ["<name>"]` in `Cargo.toml` and the registry in
`.cargo/config.toml`; cargo reads its token from
`CARGO_REGISTRIES_<NAME>_TOKEN`, which your `mise.toml` can take from the same
secret (`[env]`:
`CARGO_REGISTRIES_<NAME>_TOKEN = "{{env.CARGO_REGISTRY_TOKEN}}"`). A version
already published fails: a manual run on the same tag does nothing new.

`docker` builds the image of the tag and pushes it as `X.Y.Z` and `latest`
(`.brigade/scripts/docker_deploy.py`). The image is `DOCKER_IMAGE`
(`registry/owner/name`, in your `mise.toml` `[env]` or a CI variable), else the
repository's: `ghcr.io/<owner>/<repo>` on GitHub, pushed with the workflow token
(the job has `packages: write`), `<server>/<owner>/<repo>` on Gitea. Another
registry, or Gitea: add `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets. It
needs Docker in CI, which brigade's GitLab image does not have: `docker` and
`container-structure-test` are not offered on GitLab yet. A manual run needs a
tag at the checked out commit.

`uv:deploy` (the `uv` tool, with the `uv_publish: true` answer) publishes the
Python package built by uv (`uv build --clear && uv publish`), once per tag: the
version is the one in `pyproject.toml`, which Releasaurus bumps in the release
PR. The index is PyPI, or the upload URL in `UV_PUBLISH_URL` (Nexus,
Artifactory, GitLab or Gitea package registry...): set it in your `mise.toml`
(`[env]`) or as a CI variable. In CI, add a `UV_PUBLISH_TOKEN` secret (CI/CD
variable on GitLab): the index's token (on PyPI, an API token scoped to the
project once it exists); or, for an index with a user and a password (Nexus...),
`UV_PUBLISH_USERNAME` and `UV_PUBLISH_PASSWORD`. A manual run on a tag already
published fails unless `UV_PUBLISH_CHECK_URL` is set to the index URL
(`https://pypi.org/simple/`), which skips the files already there.

## operate

Operations that do not belong to a release, such as `renovate:operate`. Run it
with `mise run operate`, or in CI:

- **GitHub, Gitea**: "Run workflow" on the Operate workflow, and on the
  `operate_schedule` answer (a cron expression, e.g. `0 5 * * 1` for Mondays at
  5:00 UTC).
- **GitLab**: scheduled pipelines only (CI/CD → Schedules; "Play" runs one now),
  since "Run pipeline" deploys.

Renovate reads brigade's config, `.brigade/configs/renovate.json`
(`RENOVATE_CONFIG_FILE`): no `renovate.json` is needed, so there is no
onboarding PR. What it updates is the `renovate_updates` answer, a list:

- `brigade` (the default): brigade's updates, see
  [brigade updates](#brigade-updates);
- `dependencies`: your project's own (`package.json`, `pyproject.toml`, your
  workflows...), with Renovate's `config:recommended`;
- `template`: the pins of a Copier template's `template/` folder made like
  brigade's (brigade's own repository), in one `fix:` PR.

Your own Renovate config (`renovate.json`, `.github/renovate.json5`...) adds to
it and wins, e.g. `"automerge": true`; without `dependencies`,
`"enabledManagers": []` there also updates your dependencies. To replace it
all, point `renovate_config` to your own file (keep brigade's
`customManagers` and `packageRules` entries for brigade's updates).

For Renovate, CI sets the platform, the endpoint and the repository; add a
`RENOVATE_TOKEN` secret (CI/CD variable on GitLab). On GitHub, the job commits
as the token's owner, with their noreply address (`RENOVATE_GIT_AUTHOR`);
elsewhere, set `gitAuthor` in your Renovate config if needed. See
[Renovate's token permissions](https://docs.renovatebot.com/modules/platform/).

Off GitHub, also add a `RENOVATE_GITHUB_COM_TOKEN` secret (CI/CD variable on
GitLab): many dependencies live on github.com (mise's `github:` and `aqua:`
tools, `github-releases`, npm packages' repositories), whose API without a
token soon hits its rate limit, so Renovate skips some lookups and opens PRs
without release notes. Any github.com token works, with no permissions: a
fine-grained token with "Public repositories" access. See
[Renovate's github.com token](https://docs.renovatebot.com/getting-started/running/#githubcom-token-for-changelogs-and-tools).

### brigade updates

`renovate:operate` also follows brigade: on a new release, it opens a PR that
runs `mise run brigade:update` to that version, on every CI platform, as a
`ci(deps):` commit (no release). Copier
shows conflicts with your edits as inline markers in the PR: fix them there
before merging (`brigade:lint` fails until then). On GitHub, the token also
needs the Workflows permission, since updates change workflow files.

The pins in brigade's own files (`.miserc.toml`, `.brigade/`, its workflows,
`.gitlab-ci.yml`) come with these updates: Renovate leaves them alone, since a
change there would fail `brigade:lint`. Your own files (`package.json`,
`mise.toml`, your workflows...) are updated with `dependencies`.

Renovate reads this from brigade's config (`.brigade/configs/renovate.json`):
your Renovate config can still change the PR, for example its commit type with a
`packageRules` entry on `matchDepNames: ["brigade"]`. If it sets `includePaths`,
add `.brigade/copier/answers.yml`. Keep `brigade` out of groups (such as
`group:all`): Copier needs a clean tree, so the update must be its own PR.

To update every day and merge automatically once the checks pass, answer
`operate_schedule: "0 5 * * *"` and `renovate_automerge: true`, and make your
checks required (GitHub: a branch ruleset, and "Allow auto-merge"
in Settings). A failing check, or Copier's conflict markers in a brigade update,
keep the PR open.

## Ansible

`ansible` installs `ansible-core` and runs your playbooks on your inventory:
`playbooks/deploy.yml` in the deploy stage (on `X.Y.Z` tags and manual runs),
`playbooks/operate.yml` in the operate stage (manual runs and
`operate_schedule`), both with `-i inventory`. Other paths or options: change
the commands (`ansible_deploy_command`, `ansible_operate_command`), or add
`ansible.cfg`.

In CI, two optional secrets (CI/CD variables on GitLab, of type Variable):

- `ANSIBLE_PRIVATE_KEY`: the SSH private key. Ansible loads it into an SSH agent
  of its own (`ANSIBLE_SSH_AGENT=auto`, ansible-core 2.19 or later), with no key
  file. Without it, the tasks keep your own SSH setup. On GitLab, brigade's
  image has no SSH client yet
  ([#139](https://github.com/pa-decarvalho/brigade/issues/139)).
- `ANSIBLE_VAULT_PASSWORD`: the vault password. When it is set, the tasks add
  `--vault-password-file .brigade/scripts/ansible_vault_password.py`, a script
  that prints it. Without it, Ansible uses your own setup (`ansible.cfg`,
  `ANSIBLE_VAULT_PASSWORD_FILE`), so it works the same locally:
  `ANSIBLE_VAULT_PASSWORD=... mise run deploy`.

Lint the playbooks with `ansible-lint`, test roles with `molecule`.

## Toolchain

Create the project with `uv init`: `uv` is always installed, and picks Python
from `.python-version` and `requires-python`.

## Molecule

`molecule:test` runs every scenario of `molecule/` (`molecule test --all`), with
the Docker driver of `molecule-plugins` and `ansible-core` installed alongside.
`molecule init scenario` writes a scenario to fill in; for Docker, set the
driver and an image with Python (`pre_build_image` uses it as is; without it,
the driver builds an image and needs `rsync`):

```yaml
# molecule/default/molecule.yml
driver:
  name: docker
platforms:
  - name: instance
    image: docker.io/library/python:3.13-slim
    pre_build_image: true
```

The other tasks stay out of the pipeline and work on the `default` scenario.
Arguments go to the command: `mise run molecule:converge -- -s <scenario>`;
`molecule:reconverge` passes them to `converge` only (its `molecule:destroy`
takes the `default` scenario). The tasks run Molecule with
`mise exec pipx:molecule@<version>`, so that its `ansible-playbook` (with the
Docker libraries) comes before the `ansible` tool's.

It needs Docker, also in CI: GitHub runners and `act` have it; on GitLab and
Gitea, the runner must give the job access to a Docker daemon (mounted socket or
`DOCKER_HOST`).

## Run the CI locally

Pick [act](https://github.com/nektos/act) (GitHub, Gitea) or
[gitlab-ci-local](https://github.com/firecow/gitlab-ci-local) (GitLab):
`act:test` or `gitlab-ci-local:test` replays the CI of pull requests in Docker,
as part of the test stage.

- It needs Docker, also in CI: GitHub runners have it; on GitLab, the task does
  nothing in a pipeline, and on Gitea it depends on the runner.
- Inside the replayed CI, its test job runs the task again: there it does
  nothing (act sets `ACT`, gitlab-ci-local sets `GITLAB_CI`), so the replay does
  not loop.
- In CI, the test job then replays the whole CI once more, which takes longer.

## Customize a version or a command

Each tool has one file with its version and its commands. Answer yes to
`customize_tools` and Copier asks, for each selected tool, a version, a config
file (tools with one in `.brigade/configs/`) and a command:

```text
Customize tool versions and commands? (y/N) y
ruff version (empty for brigade's):
Config file of ruff, from the project root (empty for brigade's): ruff.toml
Command of ruff:lint (empty for brigade's): ruff check src
```

- An answer replaces brigade's value, and stays on `brigade:update` until you
  change it.
- An empty answer takes brigade's value, and keeps following it on
  `brigade:update`. Clear an answer to go back to it.

Answers are named `<tool>_version`, `<tool>_config` and
`<tool>_<action>_command`, e.g. `ruff_version`, `ruff_config`,
`zensical_serve_command`. To change them later, see [Questions](questions.md).

Missing a tool? Add your own task: see [Custom tasks](custom-tasks.md).
