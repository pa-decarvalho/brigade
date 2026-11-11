# Questions

Answers are saved in `.mise/brigade-copier-answers.yml` and reused by `mise run brigade:update`.

| Question | Values | Default | Effect |
|---|---|---|---|
| `tools` | tools of the [catalog](tools.md) | `yamllint`, `gitleaks`, `typos` | One `.mise/conf.d/tool-<tool>.toml` each, with its tasks. Stages follow from the tools. |
| `<stage>_enabled` | yes / no | yes | Keeps the stage: its mise task and its CI job. See [Stages](tools.md#stages). |
| `<stage>_commands` | list of commands | empty | Commands of the stage, run in order, locally and in CI. Empty runs all its tools. |
| `operate_schedule` | cron expression, e.g. `0 5 * * 1` | empty | GitHub, Gitea: when the Operate workflow runs, besides manual runs. Empty: manual runs only. On GitLab, set a pipeline schedule instead. |
| `customize_tools` | yes / no | no | Asks a version and a command for each selected tool: see [Tools](tools.md). |
| `ci` | `github`, `gitlab`, `gitea`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |

To change an answer later:

```sh
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data ci=gitlab
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data "tools=[yamllint, ruff]"
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data customize_tools=true --data ruff_version=0.16.0
```
