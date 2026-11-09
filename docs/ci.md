# CI platforms

brigade generates the CI files and `mise run brigade:update` keeps them up to date: do not edit them. Change the stages through your answers, or add your own files.

Jobs only install mise and call `mise run <stage>`, so CI and laptops run the same tools.

## GitHub (`ci: github`)

| File | Role |
|---|---|
| `.github/workflows/ci.yml` | On pull requests, `X.Y.Z` tags and manual runs: one job per stage. `release` runs on `X.Y.Z` tags only, `deploy` also on a manual run. |
| `.github/actions/mise/action.yml` | Installs the pinned mise ([mise-action](https://github.com/jdx/mise-action)) and the tools. |

`actionlint:lint` checks the workflows.

### Stages

Each stage is one job, on Linux, running `mise run <stage>`. To remove a stage or change its commands, see [Stages](tools.md#stages).

### Your own jobs

For anything else (several OSes, other triggers), add your own workflow file next to `ci.yml`: brigade never touches it.

```yaml
# .github/workflows/tests-os.yml
on:
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v7.0.1
      - uses: ./.github/actions/mise
      - run: mise run test
```

It runs next to the CI, so it does not hold back the `release` job of a tag.

## GitLab (`ci: gitlab`)

| File | Role |
|---|---|
| `.gitlab-ci.yml` | Stages, and includes every `.gitlab/ci/*.yml`. |
| `.gitlab/ci/default.yml` | The mise image and the tool cache. |
| `.gitlab/ci/setup.yml` | `mise install`, and the C toolchain the Rust linker needs when a tool needs it. |
| `.gitlab/ci/<stage>.yml` | One job per stage, running `mise run <stage>`; `release` runs on `X.Y.Z` tags only, `deploy` also on "Run pipeline". |

To add jobs, create your own file in `.gitlab/ci/`, with a name brigade does not generate: it is included automatically, and GitLab merges included files.

```yaml
# .gitlab/ci/extra.yml
extra:
  stage: test
  script:
    - mise run lint
```

`gitlab-ci:lint` checks these files against the GitLab CI schema.

## Manual run

To deploy without a release, use "Run workflow" on GitHub and Gitea, or "Run pipeline" on GitLab. The stages run, except `release`, then `deploy`.

## Gitea and Forgejo (`ci: gitea`)

Same layout as GitHub, under `.gitea/`: `workflows/ci.yml` and `actions/mise/action.yml`.

- mise is installed with its install script: Forgejo resolves actions from its own mirror, which has `actions/checkout` but not mise-action.
- `actionlint:lint` checks the workflows.

## None (`ci: none`)

Only `.mise/` is generated.
