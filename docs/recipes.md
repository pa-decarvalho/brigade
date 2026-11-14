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

## Go command

A command with its tests, released by Releasaurus, its binaries for Linux, macOS and Windows attached to each release by GoReleaser. Tested as the `go-github` variant (GoReleaser in snapshot mode: it builds every archive without publishing).

```sh
mkdir my-command && cd my-command && git init
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade .
mise exec -- go mod init example.com/my-command
```

In `.brigade/copier/data.yml`:

```yaml
ci: "github"
tools:
  - "brigade"
  - "yamllint"
  - "gitleaks"
  - "typos"
  - "editorconfig-checker"
  - "zizmor"
  - "golangci-lint"
  - "revive"
  - "osv-scanner"
  - "go"
  - "act"
  - "goreleaser"
  - "releasaurus"
  - "renovate"
```

| Stage | What runs |
|---|---|
| `lint` | `brigade`, YAML, spelling, `.editorconfig`, secrets, workflows (`zizmor`), Go (`golangci-lint`, `revive`), vulnerable modules (`osv-scanner`) |
| `build` | `go build ./...` (Go installed by the `go` tool) |
| `test` | `go test ./...`, then the pull request workflows replayed in Docker (`act`) |
| `release` | the release PR, then the tag (`releasaurus`) |
| `deploy` | the binaries and their checksums attached to the release (`goreleaser`) |
| `operate` | dependency updates (`renovate`) |

Your part: the Go code and its tests, a `.gitignore` with `dist/` and the binary `go build` writes, an `.editorconfig`, and the secrets `RENOVATE_TOKEN` and optionally `RELEASAURUS_GITHUB_TOKEN` (see [release](tools.md#release)). GoReleaser uses the workflow token; its settings are in `.brigade/configs/goreleaser.yaml`.
