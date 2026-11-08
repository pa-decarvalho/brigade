# Questions

Answers are saved in `.mise/brigade-copier-answers.yml` and reused by `mise run brigade:update`.

| Question | Values | Default | Effect |
|---|---|---|---|
| `lint` | lint tools | `yamllint`, `gitleaks`, `typos` | One `.mise/conf.d/lint-<tool>.toml` each. See [Tools](tools.md). |
| `test` | test tools | none | Same; none leaves the `test` stage out. |
| `build` | build tools | none | Same, for the `build` stage. |
| `release` | release tools | none | Same, for the `release` stage, run by CI on `X.Y.Z` tags. |
| `customize_tools` | yes / no | no | Asks a version and a command for each selected tool: see [Tools](tools.md). |
| `ci` | `github`, `gitlab`, `gitea`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |
| `rustup_mirror` | URL | empty | Rustup mirror (`rust` only): see [Mirrors](mirrors.md). |

To change an answer later:

```sh
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data ci=gitlab
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data "lint=[yamllint, ruff]"
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data customize_tools=true --data lint_ruff_version=0.16.0
```
