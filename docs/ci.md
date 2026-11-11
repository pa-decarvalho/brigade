# CI platforms

brigade generates the CI files and `mise run brigade:update` keeps them up to date: do not edit them. Change the stages through your answers, or add your own files.

Jobs only install mise and call `mise run <stage>`, so CI and laptops run the same tools.

On every platform, `lint`, `build` and `test` run on pull requests (merge requests on GitLab), side by side; `release` runs on pushes to the default branch, `deploy` on `X.Y.Z` tags and manual runs, and `operate` on manual runs and on the `operate_schedule` answer (scheduled pipelines on GitLab).

## GitHub (`ci: github`)

| File | Role |
|---|---|
| `.github/workflows/<stage>.yml` | One workflow per stage, with one job that checks out the code and runs the stage's action: `lint.yml`, `build.yml` and `test.yml` on pull requests, `release.yml` on pushes to `main`, `deploy.yml` on `X.Y.Z` tags and manual runs, `operate.yml` on manual runs and on the `operate_schedule` answer. |
| `.brigade/ci/github/actions/<stage>/action.yml` | The stage's steps: install mise and the tools, then `mise run <stage>` with the stage's environment (Releasaurus, Renovate). Secrets are passed as inputs: `token` (release), `renovate-token` (operate). |
| `.brigade/ci/github/actions/mise/action.yml` | Installs the pinned mise ([mise-action](https://github.com/jdx/mise-action)) and the tools, with a cache. `deploy` installs them without a cache. |

GitHub only reads workflows in `.github/workflows/`: everything else lives in `.brigade/`.

[jactionlint](https://jactionlint.jdx.dev) (`jactionlint:lint`) checks the workflows and the actions, with its default rules: actions pinned by commit SHA (Renovate updates the SHA and its version comment), `permissions:`, `timeout-minutes`, `concurrency:` (pull request runs cancel the older ones, release and deploy runs wait), and no cache restored in `deploy`.

### Stages

Each stage is one workflow with one job, on Linux, running its action. To remove a stage or change its commands, see [Stages](tools.md#stages).

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
      - uses: ./.brigade/ci/github/actions/test
```


## GitLab (`ci: gitlab`)

| File | Role |
|---|---|
| `.gitlab-ci.yml` | Stages, and includes every `.brigade/ci/gitlab/*.yml` and `.gitlab/ci/*.yml`. GitLab only reads this file. |
| `.brigade/ci/gitlab/default.yml` | The mise image, the tool cache and `mise install`. |
| `.brigade/ci/gitlab/<stage>.yml` | One job per stage, running `mise run <stage>`: `lint`, `build` and `test` in merge request pipelines (`needs: []`, side by side), `release` on pushes to the default branch, `deploy` on `X.Y.Z` tags and "Run pipeline", `operate` in scheduled pipelines. |

To add jobs, create your own file in `.gitlab/ci/`: it is included automatically, and GitLab merges included files.

```yaml
# .gitlab/ci/extra.yml
extra:
  stage: test
  script:
    - mise run lint
```

`gitlab-ci:lint` checks these files against the GitLab CI schema.

## Manual run

To deploy without a release, use "Run workflow" on the Deploy workflow (GitHub, Gitea), or "Run pipeline" on GitLab: only `deploy` runs. To run `operate` now, use "Run workflow" on the Operate workflow (GitHub, Gitea), or a pipeline schedule on GitLab.

## Gitea and Forgejo (`ci: gitea`)

Same layout as GitHub: `.gitea/workflows/<stage>.yml` and `.brigade/ci/gitea/actions/`.

- mise is installed with its install script: Forgejo resolves actions from its own mirror, which has `actions/checkout` but not mise-action, and act (local runs) refuses full URLs. The script checks the archive against a checksum file from the same server, so it trusts HTTPS only: `jactionlint:lint` ignores that one finding (`unverified-download`).

## None (`ci: none`)

Only `.miserc.toml` and `.brigade/` (without `ci/`) are generated.
