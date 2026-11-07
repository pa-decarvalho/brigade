# Questions

Answers are saved in `.mise/brigade-copier-answers.yml` and reused by `mise run brigade:update`.

| Question | Values | Default | Effect |
|---|---|---|---|
| `project_type` | `python`, `rust` | none | Adds `.mise/conf.d/<type>.toml`: see [Project types](project-types.md). |
| `ci` | `github`, `gitlab`, `gitea`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |
| `rustup_mirror` | URL | empty | Rustup mirror (`rust` only): see [Mirrors](mirrors.md). |

To change an answer later:

```sh
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data ci=gitlab
```
