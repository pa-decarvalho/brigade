# Questions

*Taking the order: what goes on the menu.*

Answers are saved in `.brigade/copier/data.yml`, where you change them (see
[Changing answers](#changing-answers)), and in `.brigade/copier/answers.yml`,
Copier's own copy (do not edit).

| Question | Values | Default | Effect |
|---|---|---|---|
| `presets` | `python`, `go`, `terraform`, `ansible`, `shell`, `docker`, `lua`, `docs`, `copier-template`, `security`, `ci`, `maintenance` (each answered as its tool list) | none | Pre-select their tools in `tools`: see [Presets](tools.md#presets). |
| `tools` | tools of the [catalog](tools.md) | `brigade`, `yamllint`, `gitleaks`, `typos` | One `.brigade/conf.d/<tool>-brigade.toml` each, with its tasks. Stages follow from the tools. |
| `<stage>_enabled` | yes / no | yes | Keeps the stage: its mise task and its CI job. See [Stages](tools.md#stages). |
| `<stage>_commands` | list of commands | empty | Commands of the stage, run in order, locally and in CI. Empty runs all its tools. |
| `jobs` | stages to lists of `{name, run}` | empty | CI jobs per stage, in parallel, each running its commands in order (locally, all in order). Replaces the stage's tools and `<stage>_commands`. See [Named CI jobs](ci.md#named-ci-jobs). |
| `operate_schedule` | cron expression, e.g. `0 5 * * 1` | empty | GitHub, Gitea, Forgejo: when the Operate workflow runs, besides manual runs. Empty: manual runs only. On GitLab, set a pipeline schedule instead. |
| `pages_dir` | folder | `site` | With the `pages` tool: the folder your build writes the site to (`dist` for Vite). |
| `uv_publish` | yes / no | no | With the `uv` tool: publish the package on each release (`uv:deploy`, see [deploy](tools.md#deploy)). |
| `npm_publish` | yes / no | no | With the `node` tool: publish the package on each release (`node:deploy`, see [deploy](tools.md#deploy)). |
| `maven_publish` | yes / no | no | With the `maven` tool: deploy the artifacts on each release (`maven:deploy`, see [deploy](tools.md#deploy)). |
| `gradle_publish` | yes / no | no | With the `gradle` tool: publish the artifacts on each release (`gradle:deploy`, see [deploy](tools.md#deploy)). |
| `cargo_publish` | yes / no | no | With the `rust` tool: publish the crate on each release (`rust:deploy`, see [deploy](tools.md#deploy)). |
| `customize_tools` | yes / no | no | Asks a version, a config file and a command for each selected tool: see [Tools](tools.md#customize-a-version-or-a-command). |
| `ci` | `github`, `gitlab`, `gitea`, `forgejo`, `none` | `github` | CI files and their linter: see [CI platforms](ci.md). |
| `github_mirror` | URL | empty | Mirror of `https://github.com/`: see [Mirrors](mirrors.md). |
| `pypi_index` | URL | empty | PyPI simple index: see [Mirrors](mirrors.md). |

## Changing answers

Your answers are all in `.brigade/copier/data.yml`. Edit them there, then run
`mise run brigade:update`:

```yaml
# Your answers: edit them, then run mise run brigade:update.
build_commands:
  - "uv build"
ci: "gitlab"
customize_tools: true
ruff_version: "0.16.0"
tools:
  - "brigade"
  - "ruff"
```

`brigade:update` applies them, then writes all the answers back to this file,
sorted, with JSON values (double quotes) and lists indented under their key:

- New questions of a release show up with their default (Renovate's update PR
  included): change them there too.
- A removed key comes back with its last value: set the value you want instead.
- A key that is not a question (a typo), or a question not asked (tool versions
  need `customize_tools: true`), is dropped.
- Your comments and formatting are not kept.

When `data.yml` is your only change, `brigade:update` applies it without a
commit first: review and commit the edit and the update together. Your edits are
kept if the update fails or is stopped; after a killed run, the next
`brigade:update` puts them back first (they wait in `.git/brigade-data.yml`).
With other uncommitted changes, Copier refuses to update: commit them first.
Until you run `brigade:update`, `brigade:lint` fails: the answers are not
applied yet.
