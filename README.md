<p align="center"><img src="docs/assets/logo.png" alt="brigade logo" width="120"></p>

<h1 align="center">brigade</h1>

<p align="center"><strong>Mise-en-place, ready for service.</strong></p>

<p align="center">A <a href="https://copier.readthedocs.io/">Copier</a> template that adds <a href="https://mise.jdx.dev/">mise</a> tooling and CI to an existing project.</p>

<p align="center">
  <a href="https://github.com/pa-decarvalho/brigade/releases/latest"><img src="https://img.shields.io/github/v/release/pa-decarvalho/brigade?color=orange" alt="Release"></a>
  <a href="https://github.com/pa-decarvalho/brigade/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/pa-decarvalho/brigade/test.yml?event=pull_request&label=test" alt="Test"></a>
  <a href="https://github.com/pa-decarvalho/brigade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pa-decarvalho/brigade" alt="License: MIT"></a>
  <a href="https://github.com/copier-org/copier"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json" alt="Copier"></a>
</p>

<p align="center"><code>lint · build · test · release · deploy · operate</code><br>on GitHub · GitLab · Gitea · your laptop</p>

<p align="center"><a href="https://pa-decarvalho.github.io/brigade/"><strong>Documentation</strong></a> · <a href="https://pa-decarvalho.github.io/brigade/getting-started/">Getting started</a> · <a href="https://pa-decarvalho.github.io/brigade/recipes/">Recipes</a> · <a href="https://github.com/pa-decarvalho/brigade/blob/main/CHANGELOG.md">Changelog</a></p>

<p align="center"><img src="docs/assets/banner.webp" alt="brigade: mise-en-place, ready for service"></p>

> [!WARNING]
> brigade is in alpha: its questions, tasks and generated files can still change
> before 1.0.0. Read the [release notes](CHANGELOG.md) and
> [Updating](https://pa-decarvalho.github.io/brigade/updating/) before you
> update.

## Getting started

brigade does not create the project: do that with the ecosystem's own tool, then
apply brigade.

```sh
uv init my-project
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-project
cd my-project
mise install
mise tasks
```

Pick your tools in one list: each brings its tasks for the lint, build, test,
release and deploy stages, with custom versions and commands. CI: GitHub,
GitLab, Gitea/Forgejo or none. Optional mirrors for corporate networks. Update a
project with `mise run brigade:update`.

Documentation: <https://pa-decarvalho.github.io/brigade/> (sources in `docs/`,
preview with `mise run zensical:serve`).

License: [MIT](LICENSE).
