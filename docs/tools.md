# Tools

Stages run in this order: `lint`, `build`, `test`, `release`. Each stage runs every `<stage>:<tool>` task. Each tool is one file in `.mise/conf.d/` (`<stage>-<tool>.toml`), with its pinned version and its task.
Tools are picked per stage when applying brigade; `languages` only pre-selects them.
A stage without tools is left out: no mise task, no CI job.

## lint

| Tool | Default | Task | Command |
|---|---|---|---|
| `yamllint` | yes | `lint:yamllint` | `yamllint --strict` |
| `gitleaks` | yes | `lint:gitleaks` | `gitleaks git` (history and staged changes) |
| `typos` | yes | `lint:typos` | `typos` |
| `editorconfig-checker` | no | `lint:editorconfig` | `editorconfig-checker` (needs your `.editorconfig`) |
| `ruff` | python | `lint:ruff`, `lint:ruff-format` | `ruff check`, `ruff format --check` |
| `clippy` | rust | `lint:clippy` | `cargo clippy --all-targets -- -D warnings` |
| `rustfmt` | rust | `lint:rustfmt` | `cargo fmt --check` |

The CI platform adds its own linter (`lint:actionlint`, `lint:gitlab-ci`): see [CI platforms](ci.md).

## test

| Tool | Default | Task | Command |
|---|---|---|---|
| `pytest` | python | `test:pytest` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `cargo` | rust | `test:cargo` | `cargo test` |

## build

Nothing is selected by default.

| Tool | Task | Command |
|---|---|---|
| `uv` | `build:uv` | `uv build` (into `dist/`) |
| `cargo` | `build:cargo` | `cargo build --release` |

## release

Nothing is selected by default. CI runs this stage only on tags `X.Y.Z` (or `vX.Y.Z`), after the other stages.

| Tool | Task | Command | Auth |
|---|---|---|---|
| `pypi` | `release:pypi` | `uv build`, then `uv publish` | GitHub: [trusted publishing](https://docs.pypi.org/trusted-publishers/); otherwise a `UV_PUBLISH_TOKEN` secret |
| `crates` | `release:crates` | `cargo publish` | a `CARGO_REGISTRY_TOKEN` secret |

Secrets are repository secrets (GitHub, Gitea) or CI/CD variables (GitLab), under these names.

## Languages

| Language | Create the project with | Adds |
|---|---|---|
| `python` | `uv init` | nothing: `uv` is always installed |
| `rust` | `cargo init` | `.mise/conf.d/rust.toml`: the toolchain with `clippy` and `rustfmt` |

`clippy`, `rustfmt`, `cargo` and `crates` need the `rust` language.

Missing a tool? Add your own task: see [Custom tasks](custom-tasks.md).
