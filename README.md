![brigade: mise-en-place, ready for service](docs/assets/banner.webp)

# brigade

*Mise-en-place, ready for service.*

[![Release](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpa-decarvalho%2Fbrigade%2Freleases%2Flatest&query=%24.tag_name&label=release&color=orange)](https://github.com/pa-decarvalho/brigade/releases/latest) [![Release workflow](https://img.shields.io/github/actions/workflow/status/pa-decarvalho/brigade/release.yml?branch=main&label=release%20workflow)](https://github.com/pa-decarvalho/brigade/actions/workflows/release.yml) [![License: MIT](https://img.shields.io/github/license/pa-decarvalho/brigade)](https://github.com/pa-decarvalho/brigade/blob/main/LICENSE) [![Docs](https://img.shields.io/badge/docs-pa--decarvalho.github.io%2Fbrigade-blue)](https://pa-decarvalho.github.io/brigade/) [![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier) [![Built with brigade](https://img.shields.io/badge/built%20with-brigade-orange)](https://pa-decarvalho.github.io/brigade/) [![Built with mise](https://img.shields.io/badge/built%20with-mise-blue)](https://mise.jdx.dev/) [![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen?logo=renovatebot)](https://docs.renovatebot.com/) [![CI: GitHub | GitLab | Gitea](https://img.shields.io/badge/CI-GitHub%20%7C%20GitLab%20%7C%20Gitea-informational)](https://pa-decarvalho.github.io/brigade/ci/)

[Copier](https://copier.readthedocs.io/) template that adds [mise](https://mise.jdx.dev/) tooling and CI to a project.
It does not create the project: do that with the ecosystem's own tool, then apply brigade.

```sh
uv init my-project
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-project
cd my-project
mise install
mise tasks
```

Pick your tools in one list: each brings its tasks for the lint, build, test, release and deploy stages, with custom versions and commands. CI: GitHub, GitLab, Gitea/Forgejo or none. Optional mirrors for corporate networks.
Update a project with `mise run brigade:update`.

Documentation: <https://pa-decarvalho.github.io/brigade/> (sources in `docs/`, preview with `mise run zensical:serve`).

License: [MIT](LICENSE).
