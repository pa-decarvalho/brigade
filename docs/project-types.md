# Project types

Every project gets the stages `lint` and `test`. Each stage runs all `<stage>:<tool>` tasks.

## Common

From `.mise/conf.d/lint.toml`:

| Task | Command |
|---|---|
| `lint:yamllint` | `yamllint --strict` |
| `lint:gitleaks` | `gitleaks git` (history and staged changes) |
| `lint:typos` | `typos` |

The CI platform adds its own linter: see [CI platforms](ci.md).

## python

Create the project with `uv init`. From `.mise/conf.d/python.toml`:

| Task | Command |
|---|---|
| `lint:ruff` | `ruff check` |
| `lint:ruff-format` | `ruff format --check` |
| `test:pytest` | `uv run pytest` |

`pytest` is a project dependency: `uv add --dev pytest`.

## rust

Create the project with `cargo init`. From `.mise/conf.d/rust.toml`, with the `clippy` and `rustfmt` components:

| Task | Command |
|---|---|
| `lint:clippy` | `cargo clippy --all-targets -- -D warnings` |
| `lint:rustfmt` | `cargo fmt --check` |
| `test:cargo` | `cargo test` |
