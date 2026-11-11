# brigade

brigade is a [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to an existing project.

## What it does

- Pins the project's tools (linters, formatters, test runners) in `.brigade/`, as mise tools rather than project dependencies.
- Defines the pipeline stages as mise tasks (`mise run lint`, `mise run test`), with the tools you pick.
- Generates a CI that installs mise and runs those stages, for GitHub, GitLab or Gitea/Forgejo.
- Keeps all of it up to date: `mise run brigade:update` applies the latest brigade release.

The same commands run on a laptop (Linux, macOS, Windows) and in CI.

## What it does not do

- Create the project: use the ecosystem's own tool (`uv init`, ...), then apply brigade on top.
- Write source code, package manifests or tool config files. Tool options are given inline in the mise tasks.

Next: [Getting started](getting-started.md).
