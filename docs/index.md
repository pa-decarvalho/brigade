<h1 align="center">brigade</h1>

<p align="center"><strong>Mise-en-place, ready for service.</strong></p>

<p align="center">A <a href="https://copier.readthedocs.io/">Copier</a> template that adds <a href="https://mise.jdx.dev/">mise</a> tooling and CI to an existing project.</p>

<p align="center">
  <a href="https://github.com/pa-decarvalho/brigade/releases/latest"><img src="https://img.shields.io/github/v/release/pa-decarvalho/brigade?color=orange" alt="Release"></a>
  <a href="https://github.com/pa-decarvalho/brigade/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/pa-decarvalho/brigade/test.yml?event=pull_request&label=test" alt="Test"></a>
  <a href="https://github.com/pa-decarvalho/brigade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pa-decarvalho/brigade" alt="License: MIT"></a>
  <a href="https://github.com/copier-org/copier"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json" alt="Copier"></a>
</p>

<p align="center"><code>lint · build · test · release · publish · deploy · operate</code><br>on GitHub · GitLab · Gitea · Forgejo · your laptop</p>

<p align="center"><a href="https://pa-decarvalho.github.io/brigade/"><strong>Documentation</strong></a> · <a href="https://pa-decarvalho.github.io/brigade/getting-started/">Getting started</a> · <a href="https://pa-decarvalho.github.io/brigade/recipes/">Recipes</a> · <a href="https://github.com/pa-decarvalho/brigade/blob/main/CHANGELOG.md">Changelog</a></p>

<p align="center"><img src="assets/banner.webp" alt="brigade: mise-en-place, ready for service"></p>

> **Alpha.** brigade's questions, tasks and generated files can still change
> before 1.0.0. Read the
> [release notes](https://github.com/pa-decarvalho/brigade/blob/main/CHANGELOG.md)
> and [Updating](updating.md) before you update.

brigade is a [Copier](https://copier.readthedocs.io/) template that adds
[mise](https://mise.jdx.dev/) tooling and CI to an existing project.

## What it does

- Pins the project's tools (linters, formatters, test runners) in `.brigade/`,
  as mise tools rather than project dependencies.
- Defines the pipeline stages as mise tasks (`mise run lint`, `mise run test`),
  with the tools you pick.
- Generates a CI that installs mise and runs those stages, for GitHub, GitLab or
  Gitea/Forgejo.
- Keeps all of it up to date: `mise run brigade:update` applies the latest
  brigade release.

The same commands run on a laptop (Linux, macOS, Windows: see
[Platforms](tools.md#platforms)) and in CI.

## What it does not do

brigade sets up the kitchen; it does not cook your dish.

- Create the project: use the ecosystem's own tool (`uv init`, ...), then apply
  brigade on top.
- Write source code or package manifests. Tool settings are options of the mise
  tasks, or a file in `.brigade/configs/` for tools that read one: see
  [Tool configs](tools.md#tool-configs).

## The kitchen

In a restaurant, the *brigade* is the kitchen team: each cook runs one station,
the chef calls the orders, and nothing starts before the *mise en place*,
everything prepared and in its place. [mise](https://mise.jdx.dev/) is named
after it; brigade staffs the kitchen:

| In the kitchen | In brigade |
|---|---|
| Mise en place | `mise install`: every tool pinned and ready before you start |
| One station per cook | One file per tool, `.brigade/conf.d/<tool>-brigade.toml`, with its tasks |
| The service, course after course | The stages: `lint`, `build`, `test`, `release`, `publish`, `deploy`, `operate` |
| The chef calling the orders | `mise run <stage>`: every station's task for that stage |
| The pass, where each plate is checked | CI, running the same stages on every pull request |
| The house recipe | The template, with your answers in `.brigade/copier/data.yml` |
| Fresh deliveries | `mise run brigade:update`: a new release, delivered by Renovate if you like |
| The chef inspecting the stations | `brigade:lint`: brigade's files are as delivered, nobody salted the sauce |

Next: [Getting started](getting-started.md).
