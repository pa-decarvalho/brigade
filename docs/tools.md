# Tools

Pick your tools in one list when applying brigade. A tool brings its version and all its tasks, in one file: `.mise/conf.d/tool-<tool>.toml`.

Tasks are named `<tool>:<action>`. Stages run in this order: `lint`, `build`, `test`, `release`, `deploy`, and each runs every `<tool>:<stage>` task. Any other action, such as `zensical:serve`, stays out of the pipeline.
A stage without tools is left out: no mise task, no CI job.

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
| `ruff` | `ruff:lint` | `ruff check && ruff format --check` |
| `clippy` | `clippy:lint` | `cargo clippy --all-targets -- -D warnings` |
| `rustfmt` | `rustfmt:lint` | `cargo fmt --check` |
| `uv` | `uv:build` | `uv build` (into `dist/`) |
| `zensical` | `zensical:build` | `zensical build --strict` (needs your `zensical.toml` and `docs/`: `zensical new .`) |
| | `zensical:serve` | `zensical serve --open`, to preview the site |
| `cargo` | `cargo:build` | `cargo build --release` |
| | `cargo:test` | `cargo test` |
| `pytest` | `pytest:test` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `ctt` | `ctt:test` | `ctt`, for a Copier template (needs your `ctt.toml`; on Windows, ctt 3.0.0 fails inside a git repository) |
| `pypi` | `pypi:release` | `uv build && uv publish` |
| `crates` | `crates:release` | `cargo publish` |
| `pages` | `pages:deploy` | GitHub: `zensical build --strict && ghp-import -n -p -f site`. GitLab: `zensical build --strict` |
| `ci-local` | `brigade:ci-local` | Runs the CI locally: see below |

The CI platform adds its own linter (`actionlint:lint`, `gitlab-ci:lint`): see [CI platforms](ci.md).

## release

CI runs this stage only on tags `X.Y.Z` (or `vX.Y.Z`), after the other stages.

| Tool | Auth |
|---|---|
| `pypi` | GitHub: [trusted publishing](https://docs.pypi.org/trusted-publishers/); otherwise a `UV_PUBLISH_TOKEN` secret |
| `crates` | a `CARGO_REGISTRY_TOKEN` secret |

Secrets are repository secrets (GitHub, Gitea) or CI/CD variables (GitLab), under these names.

## deploy

CI runs this stage after the others, on tags `X.Y.Z` (or `vX.Y.Z`) and on a manual run, to deploy without a release: for example to fix a typo in the documentation.

`pages` needs the `zensical` tool, and GitHub or GitLab.

- **GitHub**: the site is pushed to the `gh-pages` branch. In Settings → Pages, choose "Deploy from a branch" and `gh-pages`.
- **GitLab**: the job publishes `site/` with `pages.publish` (GitLab 17.10 or later).

Add `site/` and `.cache/` to your `.gitignore`.

## Toolchains

| Toolchain | Create the project with | Installed |
|---|---|---|
| Python | `uv init` | `uv` is always installed; it picks Python from `.python-version` and `requires-python` |
| Rust | `cargo init` | `.mise/conf.d/rust.toml`, as soon as `clippy`, `rustfmt`, `cargo` or `crates` is selected, with `clippy` and `rustfmt` |

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
