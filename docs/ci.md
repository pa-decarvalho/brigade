# CI platforms

brigade generates the CI files and `mise run brigade:update` keeps them up to date: do not edit them. Change the stages through your answers, or add your own files.

Jobs only install mise and call `mise run <stage>`, so CI and laptops run the same tools.

On every platform, `lint`, `build` and `test` run on pull requests (merge requests on GitLab), side by side; `release` runs on pushes to the default branch, and `deploy` on `X.Y.Z` tags and manual runs.

## GitHub (`ci: github`)

| File | Role |
|---|---|
| `.github/workflows/<stage>.yml` | One workflow per stage, with one job running `mise run <stage>`: `lint.yml`, `build.yml` and `test.yml` on pull requests, `release.yml` on pushes to `main`, `deploy.yml` on `X.Y.Z` tags and manual runs. |
| `.github/actions/mise/action.yml` | Installs the pinned mise ([mise-action](https://github.com/jdx/mise-action)) and the tools. |

`actionlint:lint` checks the workflows.

### Stages

Each stage is one workflow with one job, on Linux, running `mise run <stage>`. To remove a stage or change its commands, see [Stages](tools.md#stages).

### Your own jobs

For anything else (several OSes, other triggers), add your own workflow file next to them, with another name: brigade never touches it.

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


## GitLab (`ci: gitlab`)

| File | Role |
|---|---|
| `.gitlab-ci.yml` | Stages, and includes every `.gitlab/ci/*.yml`. |
| `.gitlab/ci/default.yml` | The mise image, the tool cache and `mise install`. |
| `.gitlab/ci/<stage>.yml` | One job per stage, running `mise run <stage>`: `lint`, `build` and `test` in merge request pipelines (`needs: []`, side by side), `release` on pushes to the default branch, `deploy` on `X.Y.Z` tags and "Run pipeline". |

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

To deploy without a release, use "Run workflow" on the Deploy workflow (GitHub, Gitea), or "Run pipeline" on GitLab: only `deploy` runs. `operate` has no CI job yet.

## Gitea and Forgejo (`ci: gitea`)

Same layout as GitHub, under `.gitea/`: `workflows/<stage>.yml` and `actions/mise/action.yml`.

- mise is installed with its install script: Forgejo resolves actions from its own mirror, which has `actions/checkout` but not mise-action.
- `actionlint:lint` checks the workflows.

## None (`ci: none`)

Only `.mise/` is generated.
