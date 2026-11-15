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

## Docker image

An image with its structure tests, released by Releasaurus and pushed to a registry on each release (`ghcr.io` on GitHub). Tested as the `docker-github` variant, which pushes to a local registry in Docker.

```sh
mkdir my-image && cd my-image && git init
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade .
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
  - "hadolint"
  - "trivy"
  - "checkov"
  - "docker"
  - "container-structure-test"
  - "act"
  - "releasaurus"
  - "renovate"
```

| Stage | What runs |
|---|---|
| `lint` | `brigade`, YAML, spelling, `.editorconfig`, secrets, workflows (`zizmor`), the Dockerfile (`hadolint`, `checkov`), vulnerable dependencies and secrets (`trivy`) |
| `build` | `docker build .` |
| `test` | the image's content (`container-structure-test`), then the pull request workflows replayed in Docker (`act`) |
| `release` | the release PR, then the tag (`releasaurus`) |
| `deploy` | the image, tagged `X.Y.Z` and `latest`, pushed to `ghcr.io/<owner>/<repo>` (`docker`) |
| `operate` | dependency updates, the `FROM` images included (`renovate`) |

Your part: the `Dockerfile`, your image's tests in `.brigade/configs/container-structure-test.yaml` (brigade writes a placeholder), an `.editorconfig`, and the secrets `RENOVATE_TOKEN` and optionally `RELEASAURUS_GITHUB_TOKEN` (see [release](tools.md#release)). Another registry: `DOCKER_IMAGE`, `DOCKER_USERNAME` and `DOCKER_PASSWORD` (see [deploy](tools.md#deploy)).

## Python app in Docker

An application shipped as a Docker image: tested as code (`pytest`) and as an image (`container-structure-test`), pushed to a registry on each release, not published to PyPI. Tested as the `python-docker-github` variant, which pushes to a local registry in Docker.

```sh
uv init --package my-app
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade my-app
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
  - "ruff"
  - "ty"
  - "osv-scanner"
  - "hadolint"
  - "checkov"
  - "pytest"
  - "docker"
  - "container-structure-test"
  - "act"
  - "releasaurus"
  - "renovate"
```

| Stage | What runs |
|---|---|
| `lint` | `brigade`, YAML, spelling, `.editorconfig`, secrets, workflows (`zizmor`), Python (`ruff`, `ty`), vulnerable dependencies in `uv.lock` (`osv-scanner`), the Dockerfile (`hadolint`, `checkov`) |
| `build` | `docker build .` |
| `test` | `pytest`, the image's content (`container-structure-test`), then the pull request workflows replayed in Docker (`act`) |
| `release` | the release PR (it bumps `pyproject.toml`), then the tag (`releasaurus`) |
| `deploy` | the image, tagged `X.Y.Z` and `latest`, pushed to `ghcr.io/<owner>/<repo>` (`docker`) |
| `operate` | dependency updates, `uv.lock` and the `FROM` image included (`renovate`) |

No `uv` tool: it builds a package (`uv build`), which an app does not need; the Dockerfile installs the app. A Dockerfile from uv's image:

```dockerfile
FROM ghcr.io/astral-sh/uv:0.13.8-python3.14-trixie-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
USER 65534
HEALTHCHECK NONE
ENTRYPOINT ["/app/.venv/bin/my-app"]
```

Your part: the code in `src/`, the tests in `tests/`, the `Dockerfile` and a `.dockerignore` (at least `.git`, `.venv`, `.mise-data`: a local `.venv` must not end up in the image), your image's tests in `.brigade/configs/container-structure-test.yaml`, an `.editorconfig`, and the secrets `RENOVATE_TOKEN` and optionally `RELEASAURUS_GITHUB_TOKEN`.

## TypeScript library

A library with its tests, released by Releasaurus and published to npm on each release. JavaScript works the same: the `node` tool runs your `package.json` scripts, and a missing `build` script does nothing. Tested as the `node-github` variant, which publishes to a local npm registry (Verdaccio in Docker).

```sh
mkdir my-lib && cd my-lib && git init && npm init -y
uvx copier@9.19.1 copy gh:pa-decarvalho/brigade .
```

In `.brigade/copier/data.yml`:

```yaml
ci: "github"
npm_publish: true
tools:
  - "brigade"
  - "yamllint"
  - "gitleaks"
  - "typos"
  - "editorconfig-checker"
  - "zizmor"
  - "biome"
  - "osv-scanner"
  - "node"
  - "act"
  - "releasaurus"
  - "renovate"
```

| Stage | What runs |
|---|---|
| `lint` | `brigade`, YAML, spelling, `.editorconfig`, secrets, workflows (`zizmor`), TypeScript and JSON (`biome`: lint and formatting), vulnerable dependencies in `package-lock.json` (`osv-scanner`) |
| `build` | `npm ci`, then your `build` script (`tsc`; Node.js installed by the `node` tool) |
| `test` | `npm ci`, then your `test` script (`node --test`: Node runs `.ts` files), then the pull request workflows replayed in Docker (`act`) |
| `release` | the release PR (it bumps `package.json`), then the tag (`releasaurus`) |
| `deploy` | the package to npm (`node`, with `npm_publish: true`) |
| `operate` | dependency updates, `package-lock.json` included (`renovate`) |

The scripts in `package.json`:

```json
"scripts": {
	"build": "tsc",
	"test": "node --test",
	"prepublishOnly": "npm run build"
}
```

Your part: the code in `src/`, the tests, `package.json` with its scripts and a committed `package-lock.json`, a `tsconfig.json`, a `.gitignore` with `node_modules/` and `dist/`, an `.editorconfig`, the line `//registry.npmjs.org/:_authToken=${NPM_TOKEN}` in `.npmrc`, and the secrets `NPM_TOKEN`, `RENOVATE_TOKEN` and optionally `RELEASAURUS_GITHUB_TOKEN`.
