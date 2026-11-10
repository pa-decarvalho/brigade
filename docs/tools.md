# Tools

Pick your tools in one list when applying brigade. A tool brings its version and all its tasks, in one file: `.mise/conf.d/tool-<tool>.toml`.

Tasks are named `<tool>:<action>`. Stages run in this order: `lint`, `build`, `test`, `release`, `deploy`, `operate`, and each runs every `<tool>:<stage>` task. Any other action, such as `zensical:serve`, stays out of the pipeline.

## Stages

For each stage, Copier asks whether to keep it, then its commands.

- Answer no to remove the stage: no mise task, no CI job.
- Leave the commands empty to run all the stage's tools. A stage without tools does nothing.
- Give commands to run them instead, in order, locally and in CI:

```yaml
lint_commands: ["mise run ruff:lint", "mise run typos:lint"]
```

## Catalog

`yamllint`, `gitleaks` and `typos` are selected by default.

| Tool | Task | Command |
|---|---|---|
| `yamllint` | `yamllint:lint` | `yamllint --strict` |
| `gitleaks` | `gitleaks:lint` | `gitleaks git` (history and staged changes) |
| `typos` | `typos:lint` | `typos` |
| `editorconfig-checker` | `editorconfig-checker:lint` | `editorconfig-checker` (needs your `.editorconfig`) |
| `taplo` | `taplo:lint` | `taplo fmt --check` on `.mise/**/*.toml` (fails on Windows checkouts with CRLF line endings) |
| `renovate` | `renovate:lint` | `check-jsonschema --builtin-schema vendor.renovate renovate.json` (other config path: change the command) |
| | `renovate:operate` | `renovate` (needs `RENOVATE_TOKEN` and `RENOVATE_REPOSITORIES`) |
| `ruff` | `ruff:lint` | `ruff check && ruff format --check` |
| `uv` | `uv:build` | `uv build` (into `dist/`) |
| `zensical` | `zensical:build` | `zensical build --strict` (needs your `zensical.toml` and `docs/`: `zensical new .`) |
| | `zensical:serve` | `zensical serve --open`, to preview the site |
| `pytest` | `pytest:test` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `ctt` | `ctt:test` | `ctt`, for a Copier template (needs your `ctt.toml`; on Windows, ctt 3.0.0 fails inside a git repository) |
| `releasaurus` | `releasaurus:release` | `releasaurus release && releasaurus release-pr --tag-prefix ''`: see [release](#release) |
| `pages` | `pages:deploy` | Runs the `*:build` tasks, then publishes `site/`. GitHub: `ghp-import -n -p -f site`. GitLab: the job publishes it |
| `ci-local` | `brigade:ci-local` | Runs the CI locally: see below |

The CI platform adds its own linter (`actionlint:lint`, `gitlab-ci:lint`): see [CI platforms](ci.md).

## release

CI runs this stage on its own, on pushes to the default branch (`main`): `lint`, `build` and `test` already ran on the pull request.

With `releasaurus`, [Releasaurus](https://releasaurus.rgon.io/) reads the Conventional Commits since the last tag and opens or updates a release pull request, with the next version and a `CHANGELOG.md`. Once you merge it, the next run tags `X.Y.Z` (no `v`) and publishes the release on your forge. It works on GitHub, GitLab, Gitea and Forgejo.

On GitHub and Gitea, it works with the CI's own token, but the release pull request and the tag it makes start no CI: merge the release pull request with a bypass of the required checks, and run `deploy` by hand. With a bot token, both start the CI as usual. GitLab needs the token.

| CI | Secret or CI/CD variable (bot token) | Scopes |
|---|---|---|
| GitHub | `RELEASAURUS_GITHUB_TOKEN` | Contents, Issues and Pull requests: read and write |
| GitLab | `RELEASAURUS_GITLAB_TOKEN` | `api`, `write_repository` |
| Gitea, Forgejo | `RELEASAURUS_GITEA_TOKEN` | repository, issue and misc: read and write |

## deploy

CI runs this stage on its own, on tags `X.Y.Z` (or `vX.Y.Z`), such as the ones Releasaurus pushes, and on a manual run, to deploy without a release: for example to fix a typo in the documentation.

`pages` needs GitHub or GitLab, and a `<tool>:build` task that writes `site/`: `zensical`, or your own (for example `mkdocs:build`, see [Custom tasks](custom-tasks.md)).

- **GitHub**: the site is pushed to the `gh-pages` branch. In Settings → Pages, choose "Deploy from a branch" and `gh-pages`.
- **GitLab**: the job publishes `site/` with `pages.publish` (GitLab 17.10 or later).

Add `site/` and `.cache/` to your `.gitignore`.

## operate

Operations that do not belong to a release, such as `renovate:operate`. CI does not run this stage yet: run it with `mise run operate`.

## Toolchain

Create the project with `uv init`: `uv` is always installed, and picks Python from `.python-version` and `requires-python`.

## Run the CI locally

Pick `ci-local` to get `mise run brigade:ci-local`, which runs the project's CI in Docker: [act](https://github.com/nektos/act) on GitHub and Gitea, [gitlab-ci-local](https://github.com/firecow/gitlab-ci-local) on GitLab.
It is a helper, not a stage, and its tools are installed the first time you run it: CI does not download them.

## Customize a version or a command

Each tool has one file with its version and its commands.
Answer yes to `customize_tools` and Copier asks, for each selected tool, a version and a command:

```text
Customize tool versions and commands? (y/N) y
ruff version (empty for brigade's):
Command of ruff:lint (empty for brigade's): ruff check src
```

- An answer replaces brigade's value, and stays on `brigade:update` until you change it.
- An empty answer takes brigade's value, and keeps following it on `brigade:update`. Clear an answer to go back to it.

Answers are named `<tool>_version` and `<tool>_<action>_command`, e.g. `ruff_version`, `zensical_serve_command`; `ci-local` uses `ci_local_version` and `ci_local_command`.
To change them later, see [Questions](questions.md).

Missing a tool? Add your own task: see [Custom tasks](custom-tasks.md).
