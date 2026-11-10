# Getting started

Requires [mise](https://mise.jdx.dev/) and git.

## Create the project, then apply brigade

```sh
uv init my-project
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-project
cd my-project
mise trust && mise install
mise tasks
```

Copier asks a few [questions](questions.md): your tools, whether to customize their versions and commands, CI platform, optional mirrors.
`copier copy` uses the latest release; add `--vcs-ref X.Y.Z` to pick a version.

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
.mise/
  config.toml                     # uv and brigade:update
  brigade-copier-answers.yml      # your answers, used by brigade:update
  conf.d/
    stages.toml                   # lint, build, test, release, deploy and the git hook tasks
    tool-<tool>.toml              # one per tool, e.g. tool-ruff.toml
    <ci>.toml                     # CI file linter
    mirror.toml                   # only with mirrors
<CI files>                        # see CI platforms (some are yours to edit)
```
