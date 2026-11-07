# CI platforms

The generated CI only installs mise and runs `mise run lint`, then `mise run test`.
Tool versions come from `.mise/`, so CI and laptops run the same tools.

## GitHub (`ci: github`)

- `.github/workflows/ci.yml`: jobs `lint` and `test` on pull requests, with [mise-action](https://github.com/jdx/mise-action).
- `lint:actionlint` checks the workflows.

## GitLab (`ci: gitlab`)

- `.gitlab-ci.yml` only includes the files in `.gitlab/ci/`:
  - `default.yml`: stages, the mise image, the tool cache and `mise install`;
  - `lint.yml` and `test.yml`: one job per stage;
  - `rust.yml` (rust): adds the C toolchain the Rust linker needs.
- `lint:gitlab-ci` checks these files against the GitLab CI schema.

## Gitea and Forgejo (`ci: gitea`)

- `.gitea/workflows/ci.yml`: jobs `lint` and `test` on pull requests.
- mise is installed with its install script: Forgejo resolves actions from its own mirror, which has `actions/checkout` but not mise-action.
- `lint:actionlint` checks the workflow.

## None (`ci: none`)

Only `.mise/` is generated.
