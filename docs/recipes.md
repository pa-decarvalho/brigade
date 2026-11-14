# Recipes

*Tested dishes: a whole project, from the first commit to its release.*

Each recipe is a real project that brigade's tests build and run end to end (`ctt.toml`): pick the same tools to get the same kitchen.

## Python package

A library with its tests and docs, released by Releasaurus and published to PyPI (or another index) on each tag. Tested as the `python-github` variant.

```sh
uv init --lib my-package
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-package
```

Tick the `python` and `docs` presets, then add the rest in `tools`. In `.brigade/copier/data.yml`:

```yaml
ci: "github"
uv_publish: true
tools:
  - "brigade"
  - "yamllint"
  - "gitleaks"
  - "typos"
  - "editorconfig-checker"
  - "zizmor"
  - "taplo"
  - "rumdl"
  - "ruff"
  - "ty"
  - "osv-scanner"
  - "pytest"
  - "act"
  - "uv"
  - "zensical"
  - "pages"
  - "releasaurus"
  - "renovate"
```

| Stage | What runs |
|---|---|
| `lint` | `brigade`, YAML, TOML, Markdown, spelling, `.editorconfig`, secrets, workflows (`zizmor`), Python (`ruff`, `ty`), vulnerable dependencies in `uv.lock` (`osv-scanner`) |
| `build` | the package (`uv build`) and the docs site (`zensical`) |
| `test` | `pytest`, then the pull request workflows replayed in Docker (`act`) |
| `release` | the release PR, then the tag (`releasaurus`) |
| `deploy` | the docs to GitHub Pages (`pages`), the package to PyPI (`uv`, with `uv_publish: true`) |
| `operate` | dependency updates (`renovate`) |

Your part: the code in `src/`, the tests in `tests/`, the docs in `docs/` with a `zensical.toml`, an `.editorconfig`, and these secrets: `UV_PUBLISH_TOKEN` (a PyPI token; another index: `UV_PUBLISH_URL`), `RENOVATE_TOKEN`, and optionally `RELEASAURUS_GITHUB_TOKEN` (see [release](tools.md#release)). In Settings → Pages, deploy from the `gh-pages` branch.

The test publishes to a local PyPI (pypiserver in Docker) twice: the second run skips the files already there.
