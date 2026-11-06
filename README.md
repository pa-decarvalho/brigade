# brigade

[Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not create the project: do that with the ecosystem's own tool, then apply brigade.

```sh
uv init my-project
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-project
cd my-project
mise trust && mise install
mise tasks
```

`copier copy` uses the latest release; add `--vcs-ref X.Y.Z` to pick a version.
Update a project to the latest release with `mise run brigade:update`.
Run `mise run brigade:hooks` once to lint before each commit: the git hook in `.git/hooks/` runs `mise run brigade:pre-commit`, a task defined by brigade and kept up to date by `brigade:update`.

Project types: `python`, `rust`. CI: `github`, `gitlab`, `gitea` (Gitea and Forgejo Actions) or `none`; the generated pipeline runs `mise run lint` then `mise run test`.

## Development

Requires [mise](https://mise.jdx.dev/).

```sh
mise trust && mise install
mise run hooks    # optional: lint before each commit
mise run lint
mise run test
```

`mise run lint` checks this repo. Pinned versions are updated by [Renovate](https://docs.renovatebot.com/) (`.github/renovate.json5`), run every Monday by `.github/workflows/renovate.yml` as two grouped PRs (template updates as `fix:`, which triggers a release; this repo's tooling as `chore:`) with a `RENOVATE_TOKEN` secret (fine-grained token on this repo: contents, pull requests, issues, workflows and commit statuses read/write). `mise run test` renders each variant from `ctt.toml` into `.ctt/src/.ctt/` with [ctt](https://github.com/KyleKing/copier-template-tester), creates a real project there, then runs its mise tasks.
ctt only sees files tracked by git: `git add` new template files before testing.
It also checks that `mise run brigade:update` moves each variant from the latest release to the current commit without conflicts, and runs each variant's generated CI locally with [act](https://github.com/nektos/act) or [gitlab-ci-local](https://github.com/firecow/gitlab-ci-local).
That last part (`test:ci`) needs a running Docker. brigade's CI runs `test:ctt` and `test:update` on Linux, macOS and Windows, and `test:ci` on Linux.
