# Development

Working on brigade itself. Requires [mise](https://mise.jdx.dev/) and, for `ci:test`, a running Docker.

```sh
mise trust && mise install
mise run hooks    # optional: lint before each commit
mise run lint
mise run test
mise run docs:serve
```

## Repository

- `copier.yml` includes `.copier/settings.yml` and `.copier/questions/`: `common.yml`, then `toolchains/` and one file per tool in `tools/`.
- `template/` holds the generated files.
- `ctt.toml` lists the test variants.
- `docs/` and `zensical.toml` hold this site.

## Lint

`mise run lint` checks this repo: yamllint, actionlint, taplo, editorconfig-checker, gitleaks, typos and the Renovate config schema.

## Tests

`mise run test` runs:

- `ctt:test`: renders each `ctt.toml` variant into `.ctt/` with [ctt](https://github.com/KyleKing/copier-template-tester), creates a real project there with the ecosystem's tool, then runs its stages. ctt only sees files tracked by git: `git add` new template files before testing.
- `update:test`: for each variant, applies the latest release, updates to the current commit with `mise run brigade:update`, then runs the stages.
- `ci:test`: runs each variant's generated CI locally with its `brigade:ci-local` task: [act](https://github.com/nektos/act) (GitHub, Gitea) or [gitlab-ci-local](https://github.com/firecow/gitlab-ci-local) (GitLab). It needs Docker; Docker Desktop's socket is found on macOS.
- `docs:test`: builds this site in strict mode, which fails on broken links.

brigade's CI runs these tests on Linux only.
The site is deployed to GitHub Pages on each push to `main`.

## Versions and releases

Pinned versions are updated by [Renovate](https://docs.renovatebot.com/) (`.github/renovate.json5`), run every Monday by `.github/workflows/renovate.yml` as two grouped PRs:

- template updates as `fix:`, which triggers a release;
- this repo's tooling as `chore:`.

It needs a `RENOVATE_TOKEN` secret: a fine-grained token on this repo with contents, pull requests, issues, workflows and commit statuses read/write.

Commits and PR titles follow Conventional Commits. On each push to `main`, `.github/workflows/release.yml` runs [Releasaurus](https://github.com/robgonnella/releasaurus) (`mise run release`): it opens or updates the release PR, and once merged tags `X.Y.Z` and updates `CHANGELOG.md`; Copier uses these tags as template versions.

It uses the workflow token: the release PR it opens starts no CI, so it is merged with a bypass of the required checks.
