# Questions

Answers are saved in `.mise/brigade-copier-answers.yml` and reused by `mise run brigade:update`.

| Question | Values | Default | Effect |
|---|---|---|---|
| `languages` | `python`, `rust` (several or none) | none | Pre-selects tools; `rust` adds the toolchain. See [Tools](tools.md). |
| `lint` | lint tools | from `languages` | One `.mise/conf.d/lint-<tool>.toml` each. See [Tools](tools.md). |
| `test` | test tools | from `languages` | Same; none leaves the `test` stage out. |
| `build` | build tools | none | Same, for the `build` stage. |
| `release` | release tools | none | Same, for the `release` stage, run by CI on `X.Y.Z` tags. |
| `ci` | `github`, `gitlab`, `gitea`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |
| `rustup_mirror` | URL | empty | Rustup mirror (`rust` only): see [Mirrors](mirrors.md). |

To change an answer later:

```sh
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data ci=gitlab
uvx copier@9.19.1 update -a .mise/brigade-copier-answers.yml --data "lint=[yamllint, ruff]"
```
