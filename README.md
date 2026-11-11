# brigade

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

Documentation: https://pa-decarvalho.github.io/brigade/ (sources in `docs/`, preview with `mise run zensical:serve`).
