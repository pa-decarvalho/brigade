# CI platforms

Each CI platform gets two kinds of files:

- **brigade-owned**: install mise and run the stages. `mise run brigade:update` keeps them up to date; do not edit them.
- **yours**: generated once, never touched again by `brigade:update`. This is where the CI is customized.

Jobs only install mise and call `mise run <task>`, so CI and laptops run the same tools.

## GitHub (`ci: github`)

| File | Owner | Role |
|---|---|---|
| `.github/workflows/ci.yml` | brigade | On pull requests: a `plan` job reads `.github/ci.toml`, then the `lint` and `test` jobs run, then `custom.yml`. |
| `.github/actions/mise/action.yml` | brigade | Installs the pinned mise ([mise-action](https://github.com/jdx/mise-action)) and the tools. |
| `.github/ci.toml` | you | The jobs of each stage: which task, on which runners. |
| `.github/workflows/custom.yml` | you | Extra jobs, run after the stages in the same workflow. |

`lint:actionlint` checks the workflows.

### Jobs of each stage: `ci.toml`

Each `[[<stage>]]` entry runs `mise run <task>` on each runner in `os` (default `["ubuntu-latest"]`).
A stage without entries is skipped. `fetch-depth` is the git history to fetch (`0` = all, default `1`).

The default runs each stage once, on Linux:

```toml
[[lint]]
task = "lint"
os = ["ubuntu-latest"]

[[test]]
task = "test"
os = ["ubuntu-latest"]
```

Tests on every OS, one task split into its own jobs:

```toml
[[lint]]
task = "lint"

[[test]]
task = "test:pytest"
os = ["ubuntu-latest", "macos-latest", "windows-latest"]

[[test]]
task = "test:integration"   # a custom task, see Custom tasks
fetch-depth = 0
```

### Extra jobs: `custom.yml`

`ci.yml` calls `custom.yml` as a [reusable workflow](https://docs.github.com/en/actions/reference/workflows-and-actions/reusable-workflows) after the stages.
It holds a disabled example job; each job should check out the code, use `./.github/actions/mise` and run `mise run <task>`:

```yaml
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.1
      - uses: ./.github/actions/mise
      - run: mise run docs:build
```

For other triggers (tags, schedules), add your own workflow files next to them.

## GitLab (`ci: gitlab`)

| File | Owner | Role |
|---|---|---|
| `.gitlab-ci.yml` | brigade | Includes the files below, `custom.yml` last. |
| `.gitlab/ci/default.yml` | brigade | Stages, the mise image, the tool cache and `mise install`. |
| `.gitlab/ci/lint.yml`, `test.yml` | brigade | One job per stage. |
| `.gitlab/ci/rust.yml` (rust) | brigade | Adds the C toolchain the Rust linker needs. |
| `.gitlab/ci/custom.yml` | you | Extra jobs, and overrides of brigade's jobs. |

GitLab merges included files, so `custom.yml` can add jobs or change brigade's:

```yaml
test:
  parallel:
    matrix:
      - PYTHON: ["3.12", "3.13"]
```

`lint:gitlab-ci` checks these files against the GitLab CI schema.

## Gitea and Forgejo (`ci: gitea`)

Same layout as GitHub, under `.gitea/`: `workflows/ci.yml`, `actions/mise/action.yml`, `ci.toml` and `workflows/custom.yml`.

- mise is installed with its install script: Forgejo resolves actions from its own mirror, which has `actions/checkout` but not mise-action.
- The jobs read from `ci.toml` need a recent runner (dynamic matrices, [gitea/act #149](https://gitea.com/gitea/act/issues/149)).
- `lint:actionlint` checks the workflows.

## None (`ci: none`)

Only `.mise/` is generated.
