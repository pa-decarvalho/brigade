# Tools

Stages run in this order: `lint`, `build`, `test`, `release`, `deploy`. Each stage runs every `<stage>:<tool>` task. Each tool is one file in `.mise/conf.d/` (`<stage>-<tool>.toml`), with its pinned version and its task.
Tools are picked per stage when applying brigade.
A stage without tools is left out: no mise task, no CI job.

## lint

| Tool | Default | Task | Command |
|---|---|---|---|
| `yamllint` | yes | `lint:yamllint` | `yamllint --strict` |
| `gitleaks` | yes | `lint:gitleaks` | `gitleaks git` (history and staged changes) |
| `typos` | yes | `lint:typos` | `typos` |
| `editorconfig-checker` | no | `lint:editorconfig` | `editorconfig-checker` (needs your `.editorconfig`) |
| `ruff` | no | `lint:ruff` | `ruff check && ruff format --check` |
| `clippy` | no | `lint:clippy` | `cargo clippy --all-targets -- -D warnings` |
| `rustfmt` | no | `lint:rustfmt` | `cargo fmt --check` |

The CI platform adds its own linter (`lint:actionlint`, `lint:gitlab-ci`): see [CI platforms](ci.md).

## build

Nothing is selected by default.

| Tool | Task | Command |
|---|---|---|
| `uv` | `build:uv` | `uv build` (into `dist/`) |
| `cargo` | `build:cargo` | `cargo build --release` |
| `zensical` | `build:zensical` | `zensical build --strict` (needs your `zensical.toml` and `docs/`: `zensical new .`) |

## test

| Tool | Default | Task | Command |
|---|---|---|---|
| `pytest` | no | `test:pytest` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `cargo` | no | `test:cargo` | `cargo test` |

## release

Nothing is selected by default. CI runs this stage only on tags `X.Y.Z` (or `vX.Y.Z`), after the other stages.

| Tool | Task | Command | Auth |
|---|---|---|---|
| `pypi` | `release:pypi` | `uv build && uv publish` | GitHub: [trusted publishing](https://docs.pypi.org/trusted-publishers/); otherwise a `UV_PUBLISH_TOKEN` secret |
| `crates` | `release:crates` | `cargo publish` | a `CARGO_REGISTRY_TOKEN` secret |

Secrets are repository secrets (GitHub, Gitea) or CI/CD variables (GitLab), under these names.

## deploy

Nothing is selected by default. CI runs this stage after the others, on tags `X.Y.Z` (or `vX.Y.Z`) and on a manual run, to deploy without a release: for example to fix a typo in the documentation.

| Tool | Task | Command | Needs |
|---|---|---|---|
| `pages` | `deploy:pages` | GitHub: `zensical build --strict && ghp-import -n -p -f site`. GitLab: `zensical build --strict` | the `zensical` build tool, and GitHub or GitLab |

- **GitHub**: the site is pushed to the `gh-pages` branch. In Settings → Pages, choose "Deploy from a branch" and `gh-pages`.
- **GitLab**: the job publishes `site/` with `pages.publish` (GitLab 17.10 or later).

Add `site/` and `.cache/` to your `.gitignore`.

## Toolchains

| Toolchain | Create the project with | Installed |
|---|---|---|
| Python | `uv init` | `uv` is always installed; it picks Python from `.python-version` and `requires-python` |
| Rust | `cargo init` | `.mise/conf.d/rust.toml`, as soon as `clippy`, `rustfmt`, `cargo` or `crates` is selected, with `clippy` and `rustfmt` |

## Customize a version or a command

Each tool has one file with its version and one command.
Answer yes to `customize_tools` and Copier asks, for each selected tool, a version and a command:

```text
Customize tool versions and commands? (y/N) y
ruff version (empty for brigade's):
Command of lint:ruff (empty for brigade's): ruff check src
```

- An answer replaces brigade's value, and stays on `brigade:update` until you change it.
- An empty answer takes brigade's value, and keeps following it on `brigade:update`. Clear an answer to go back to it.

Answers are named `<stage>_<tool>_version` and `<stage>_<tool>_command`, e.g. `lint_ruff_version`.
To change them later, see [Questions](questions.md).

Missing a tool? Add your own task: see [Custom tasks](custom-tasks.md).
