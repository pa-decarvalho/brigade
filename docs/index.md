![brigade: mise-en-place, ready for service](assets/banner.webp)

# brigade

*Mise-en-place, ready for service.*

brigade is a [Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to an existing project.

## What it does

- Pins the project's tools (linters, formatters, test runners) in `.brigade/`, as mise tools rather than project dependencies.
- Defines the pipeline stages as mise tasks (`mise run lint`, `mise run test`), with the tools you pick.
- Generates a CI that installs mise and runs those stages, for GitHub, GitLab or Gitea/Forgejo.
- Keeps all of it up to date: `mise run brigade:update` applies the latest brigade release.

The same commands run on a laptop (Linux, macOS, Windows: see [Platforms](tools.md#platforms)) and in CI.

## What it does not do

brigade sets up the kitchen; it does not cook your dish.

- Create the project: use the ecosystem's own tool (`uv init`, ...), then apply brigade on top.
- Write source code or package manifests. Tool settings are options of the mise tasks, or a file in `.brigade/configs/` for tools that read one: see [Tool configs](tools.md#tool-configs).

## The kitchen

In a restaurant, the *brigade* is the kitchen team: each cook runs one station, the chef calls the orders, and nothing starts before the *mise en place*, everything prepared and in its place. [mise](https://mise.jdx.dev/) is named after it; brigade staffs the kitchen:

| In the kitchen | In brigade |
|---|---|
| Mise en place | `mise install`: every tool pinned and ready before you start |
| One station per cook | One file per tool, `.brigade/tools/<tool>-brigade.toml`, with its tasks |
| The service, course after course | The stages: `lint`, `build`, `test`, `release`, `deploy`, `operate` |
| The chef calling the orders | `mise run <stage>`: every station's task for that stage |
| The pass, where each plate is checked | CI, running the same stages on every pull request |
| The house recipe | The template, with your answers in `.brigade/copier/data.yml` |
| Fresh deliveries | `mise run brigade:update`: a new release, delivered by Renovate if you like |
| The chef inspecting the stations | `brigade:lint`: brigade's files are as delivered, nobody salted the sauce |

Next: [Getting started](getting-started.md).
