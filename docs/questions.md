# Questions

Answers are saved in `.mise/brigade-copier-answers.yml` and reused by `mise run brigade:update`.

| Question | Values | Default | Effect |
|---|---|---|---|
| `tools` | tools of the [catalog](tools.md) | `yamllint`, `gitleaks`, `typos` | One `.mise/conf.d/tool-<tool>.toml` each, with its tasks. Stages follow from the tools. |
| `customize_tools` | yes / no | no | Asks a version and a command for each selected tool: see [Tools](tools.md). |
| `ci` | `github`, `gitlab`, `gitea`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |
| `rustup_mirror` | URL | empty | Rustup mirror (`rust` only): see [Mirrors](mirrors.md). |

To change an answer later:

```sh
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data ci=gitlab
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data "tools=[yamllint, ruff]"
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data customize_tools=true --data ruff_version=0.16.0
```
