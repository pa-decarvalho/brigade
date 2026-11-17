# Getting started

*Tie your apron: your first service starts here.*

Requires [mise](https://mise.jdx.dev/) and git.

## Create the project, then apply brigade

```sh
uv init my-project
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-project
cd my-project
mise -C .brigade lock
mise install
mise tasks
```

Copier asks a few [questions](questions.md): your tools, whether to customize
their versions and commands, CI platform, optional mirrors. `copier copy` uses
the latest release; add `--vcs-ref X.Y.Z` to pick a version.
`mise -C .brigade lock` writes the tools' exact versions and checksums to
`.brigade/mise.lock` (see [Lockfile](updating.md#lockfile)): commit it.

## Run the stages

```sh
mise run lint
mise run test
```

## Lint before each commit

```sh
mise run brigade:hooks
```

This writes a git hook in `.git/hooks/` that runs `mise run brigade:pre-commit`.
The task is defined by brigade, so `brigade:update` keeps it up to date.

## Generated files

```text
.miserc.toml                # mise files to read: brigade's, then mise.toml
.brigade/
  copier/answers.yml        # your answers, written by Copier
  copier/data.yml           # your answers, to edit: brigade:update applies them
  configs/                  # tool configs (yamllint.yml, ruff.toml...)
  mise.toml                 # uv and brigade:update
  stages.toml               # the stages and the git hook tasks
  mirror.toml               # only with mirrors
  conf.d/<tool>-brigade.toml  # one per tool, and the CI file linter
  mise.lock, .mise/locks/   # tools' versions and checksums (mise lock)
  ci/<ci>/                  # CI steps: actions (GitHub, Gitea), jobs (GitLab)
<CI files>                  # workflows or .gitlab-ci.yml: see CI platforms
```

Your own tasks and tools go in `mise.toml`: see [Custom tasks](custom-tasks.md).
