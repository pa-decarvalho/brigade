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

Tools picked per stage (lint, build, test, release, deploy), with custom versions and commands. CI: GitHub, GitLab, Gitea/Forgejo or none. Optional mirrors for corporate networks.
Update a project with `mise run brigade:update`.

Documentation: https://pa-decarvalho.github.io/brigade/ (sources in `docs/`, preview with `mise run docs:serve`).
