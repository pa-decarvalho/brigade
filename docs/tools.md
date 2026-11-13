# Tools

Pick your tools in one list when applying brigade. A tool brings its version and all its tasks, in one file: `.brigade/tools/<tool>-brigade.toml`, listed in `.miserc.toml`. Its tasks run at the project root.

Tasks are named `<tool>:<action>`. Stages run in this order: `lint`, `build`, `test`, `release`, `deploy`, `operate`, and each runs every `<tool>:<stage>` task. Any other action, such as `zensical:serve`, stays out of the pipeline.

## Stages

For each stage, Copier asks whether to keep it, then its commands.

- Answer no to remove the stage: no mise task, no CI job.
- Leave the commands empty to run all the stage's tools. A stage without tools does nothing.
- Give commands to run them instead, in order, locally and in CI:

```yaml
lint_commands: ["mise run ruff:lint", "mise run typos:lint"]
```

## Catalog

`brigade`, `yamllint`, `gitleaks` and `typos` are selected by default.

| Tool | Task | Command |
|---|---|---|
| `brigade` | `brigade:lint` | Fails when a brigade-owned file was edited or deleted: see [brigade](#brigade) |
| `yamllint` | `yamllint:lint` | `yamllint --strict` |
| `gitleaks` | `gitleaks:lint` | `gitleaks git` (history and staged changes) |
| `typos` | `typos:lint` | `typos` |
| `editorconfig-checker` | `editorconfig-checker:lint` | `editorconfig-checker` (needs your `.editorconfig`) |
| `taplo` | `taplo:lint` | `taplo fmt --check` on `.brigade/**/*.toml` and `.miserc.toml` |
| `renovate` | `renovate:lint` | `check-jsonschema --builtin-schema vendor.renovate renovate.json` (other config path: change the command) |
| | `renovate:operate` | `renovate` (needs `RENOVATE_TOKEN` and `RENOVATE_REPOSITORIES`: see [operate](#operate)); also opens a PR updating brigade on each release |
| `ruff` | `ruff:lint` | `ruff check && ruff format --check`, without `.mise-data/` (GitLab CI tool cache) |
| `ty` | `ty:lint` | `uv sync && ty check` (`uv sync`: ty reads the project's `.venv`), without `.mise-data/` |
| `shellcheck` | `shellcheck:lint` | `shellcheck` on every `*.sh` and `*.bash` (outside hidden folders); none: nothing to check |
| `shfmt` | `shfmt:lint` | `shfmt --diff` on the same files (style: your `.editorconfig`) |
| `rumdl` | `rumdl:lint` | `rumdl check --no-cache .` (Markdown), without `.mise-data/` |
| `osv-scanner` | `osv-scanner:lint` | `osv-scanner scan source --recursive` on your lockfiles (`uv.lock`, `package-lock.json`...), without `.mise-data/`; queries osv.dev, so a new vulnerability can fail an unchanged project |
| `golangci-lint` | `golangci-lint:lint` | `golangci-lint run` (needs Go: pin `go` in your `mise.toml`) |
| `tflint` | `tflint:lint` | `tflint --recursive` (Terraform) |
| `checkov` | `checkov:lint` | `checkov --directory . --skip-download` (Terraform, Kubernetes, Dockerfiles, workflows...), without `.mise-data/` |
| `dotenv-linter` | `dotenv-linter:lint` | `dotenv-linter check --recursive .` (`.env` files), without `.mise-data/` |
| `stylua` | `stylua:lint` | `stylua --check .` (Lua) |
| `ansible-lint` | `ansible-lint:lint` | `ansible-lint --strict`, without `.brigade/answers.yml` (written by Copier) and `.mise-data/` |
| `hadolint` | `hadolint:lint` | `hadolint` on every `*Dockerfile*` and `*Containerfile*` (outside hidden folders); none: nothing to check |
| `zizmor` | `zizmor:lint` | GitHub: `zizmor --offline .` audits the workflows and actions for security issues. brigade's own files pass; their `# zizmor: ignore[...]` comments keep `./` for local actions (act has no `$/` syntax) and allow fixed values written to `GITHUB_ENV` |
| `uv` | `uv:build` | `uv build` (into `dist/`) |
| `zensical` | `zensical:build` | `zensical build --strict` (needs your `zensical.toml` and `docs/`: `zensical new .`) |
| | `zensical:serve` | `zensical serve --open`, to preview the site |
| `pytest` | `pytest:test` | `uv run pytest` (add it with `uv add --dev pytest`) |
| `molecule` | `molecule:test` | `molecule test --all`, with the Docker driver (needs your `molecule/<scenario>/molecule.yml` and Docker: see [Molecule](#molecule)) |
| | `molecule:converge`, `molecule:verify`, `molecule:destroy` | `molecule converge`, `verify`, `destroy`, while writing a role |
| | `molecule:reconverge` | `molecule:destroy`, then `molecule converge`, to converge from scratch |
| | `molecule:login` | `molecule login`, a shell in the instance |
| `ctt` | `ctt:test` | `ctt`, for a Copier template (needs your `ctt.toml`) |
| `releasaurus` | `releasaurus:release` | `releasaurus release && releasaurus release-pr --tag-prefix ''`: see [release](#release) |
| `pages` | `pages:deploy` | Runs the `*:build` tasks, then publishes `site/`. GitHub: `ghp-import -n -p -f site`. GitLab: the job publishes it |
| `ansible` | `ansible:deploy`, `ansible:operate` | `ansible-playbook -i inventory playbooks/deploy.yml` (`operate.yml`): see [Ansible](#ansible) |
| `act` | `act:test` | GitHub, Gitea: `act pull_request` replays the pull request workflows in Docker: see below |
| `gitlab-ci-local` | `gitlab-ci-local:test` | GitLab: `gitlab-ci-local` replays the merge request pipeline in Docker: see below |

The CI platform adds its own linter (`jactionlint:lint`, `gitlab-ci:lint`): see [CI platforms](ci.md).

## Platforms

brigade's own files run on Linux, macOS and Windows; each tool runs where it is supported. CI runs on Linux, so these limits only matter for local runs (`mise run <stage>`, git hooks). Known limits on Windows:

- `taplo`: fails on checkouts with CRLF line endings (`git config core.autocrlf false`, or `* text eol=lf` in `.gitattributes`).
- `ctt`: ctt 3.0.0 fails inside a git repository.
- `ansible-lint`, `molecule`, `ansible`: Ansible does not run on Windows (use WSL).
- `act`, `gitlab-ci-local`: need Docker with Linux containers (Docker Desktop, WSL 2).

## brigade

`brigade:lint` renders the template at the version of `.brigade/answers.yml`, with your answers, into a temporary folder, and compares it with your brigade-owned files (`.miserc.toml`, `.brigade/`, the generated workflows or `.gitlab-ci.yml`). An edited or deleted file fails the lint stage, locally, in the git hook and in CI: `brigade:update` would overwrite it. Run `mise run brigade:update` to restore them.

It also tells when a newer brigade release is out (`copier check-update`), without failing: run `mise run brigade:update`, or let [Renovate](#brigade-updates) open the PR.

It needs access to the template (`gh:pa-decarvalho/brigade`, through git) on each run. Offline, behind a proxy, or to edit a generated file on purpose, remove `brigade` from your tools.

## release

CI runs this stage on its own, on pushes to the default branch (`main`): `lint`, `build` and `test` already ran on the pull request.

With `releasaurus`, [Releasaurus](https://releasaurus.rgon.io/) reads the Conventional Commits since the last tag and opens or updates a release pull request, with the next version and a `CHANGELOG.md`. Once you merge it, the next run tags `X.Y.Z` (no `v`) and publishes the release on your forge. It works on GitHub, GitLab, Gitea and Forgejo.

By default, every Conventional Commit (`ci:`, `docs:`, `chore:`...) makes a release. To release on `feat` and `fix` only, add a `releasaurus.toml` that skips the other groups, which also leaves them out of `CHANGELOG.md`:

```toml
[defaults.versioning.named_parsers]
refactor.skip = true
documentation.skip = true
style.skip = true
test.skip = true
chore.skip = true
ci.skip = true
miscellaneous.skip = true
```

See [Releasaurus commit groups](https://releasaurus.rgon.io/changelog.html).

On GitHub and Gitea, it works with the CI's own token, but the release pull request and the tag it makes start no CI: merge the release pull request with a bypass of the required checks, and run `deploy` by hand. With a bot token, both start the CI as usual. GitLab needs the token.

| CI | Secret or CI/CD variable (bot token) | Scopes |
|---|---|---|
| GitHub | `RELEASAURUS_GITHUB_TOKEN` | Contents, Issues and Pull requests: read and write |
| GitLab | `RELEASAURUS_GITLAB_TOKEN` | `api`, `write_repository` |
| Gitea, Forgejo | `RELEASAURUS_GITEA_TOKEN` | repository, issue and misc: read and write |

## deploy

CI runs this stage on its own, on tags `X.Y.Z` (or `vX.Y.Z`), such as the ones Releasaurus pushes, and on a manual run, to deploy without a release: for example to fix a typo in the documentation.

`pages` needs GitHub or GitLab, and a `<tool>:build` task that writes `site/`: `zensical`, or your own (for example `mkdocs:build`, see [Custom tasks](custom-tasks.md)).

- **GitHub**: the site is pushed to the `gh-pages` branch. In Settings → Pages, choose "Deploy from a branch" and `gh-pages`.
- **GitLab**: the job publishes `site/` with `pages.publish` (GitLab 17.10 or later).

Add `site/` and `.cache/` to your `.gitignore`.

## operate

Operations that do not belong to a release, such as `renovate:operate`. Run it with `mise run operate`, or in CI:

- **GitHub, Gitea**: "Run workflow" on the Operate workflow, and on the `operate_schedule` answer (a cron expression, e.g. `0 5 * * 1` for Mondays at 5:00 UTC).
- **GitLab**: scheduled pipelines only (CI/CD → Schedules; "Play" runs one now), since "Run pipeline" deploys.

For Renovate, CI sets the platform, the endpoint and the repository; add a `RENOVATE_TOKEN` secret (CI/CD variable on GitLab). On GitHub, the job commits as the token's owner, with their noreply address (`RENOVATE_GIT_AUTHOR`); elsewhere, set `gitAuthor` in your Renovate config if needed. See [Renovate's token permissions](https://docs.renovatebot.com/modules/platform/).

### brigade updates

`renovate:operate` also follows brigade: on a new release, it opens a PR that runs `mise run brigade:update` to that version, on every CI platform. Copier shows conflicts with your edits as inline markers in the PR: fix them there before merging (`brigade:lint` fails until then). On GitHub, the token also needs the Workflows permission, since updates change workflow files.

Renovate reads this from its global config (`RENOVATE_CONFIG`, set by the task): your Renovate config can still change the PR, for example its commit type with a `packageRules` entry on `matchDepNames: ["brigade"]`. If it sets `includePaths`, add `.brigade/answers.yml`. Keep `brigade` out of groups (such as `group:all`): Copier needs a clean tree, so the update must be its own PR.

To update every day and merge automatically once the checks pass, answer `operate_schedule: "0 5 * * *"`, add `automerge: true` to your Renovate config and make your checks required (GitHub: a branch ruleset, and "Allow auto-merge" in Settings). A failing check, or Copier's conflict markers in a brigade update, keep the PR open.

## Ansible

`ansible` installs `ansible-core` and runs your playbooks on your inventory: `playbooks/deploy.yml` in the deploy stage (on `X.Y.Z` tags and manual runs), `playbooks/operate.yml` in the operate stage (manual runs and `operate_schedule`), both with `-i inventory`. Other paths or options: change the commands (`ansible_deploy_command`, `ansible_operate_command`), or add `ansible.cfg`.

In CI, two optional secrets (CI/CD variables on GitLab, of type Variable):

- `ANSIBLE_PRIVATE_KEY`: the SSH private key. Ansible loads it into an SSH agent of its own (`ANSIBLE_SSH_AGENT=auto`, ansible-core 2.19 or later), with no key file. Without it, the tasks keep your own SSH setup. On GitLab, brigade's image has no SSH client yet ([#139](https://github.com/pa-decarvalho/brigade/issues/139)).
- `ANSIBLE_VAULT_PASSWORD`: the vault password. When it is set, the tasks add `--vault-password-file .brigade/scripts/ansible-vault-password.py`, a script that prints it. Without it, Ansible uses your own setup (`ansible.cfg`, `ANSIBLE_VAULT_PASSWORD_FILE`), so it works the same locally: `ANSIBLE_VAULT_PASSWORD=... mise run deploy`.

Lint the playbooks with `ansible-lint`, test roles with `molecule`.

## Toolchain

Create the project with `uv init`: `uv` is always installed, and picks Python from `.python-version` and `requires-python`.

## Molecule

`molecule:test` runs every scenario of `molecule/` (`molecule test --all`), with the Docker driver of `molecule-plugins` and `ansible-core` installed alongside. `molecule init scenario` writes a scenario to fill in; for Docker, set the driver and an image with Python (`pre_build_image` uses it as is; without it, the driver builds an image and needs `rsync`):

```yaml
# molecule/default/molecule.yml
driver:
  name: docker
platforms:
  - name: instance
    image: docker.io/library/python:3.13-slim
    pre_build_image: true
```

The other tasks stay out of the pipeline and work on the `default` scenario. Arguments go to the command: `mise run molecule:converge -- -s <scenario>`; `molecule:reconverge` passes them to `converge` only (its `molecule:destroy` takes the `default` scenario). The tasks run Molecule with `mise exec pipx:molecule@<version>`, so that its `ansible-playbook` (with the Docker libraries) comes before the `ansible` tool's.

It needs Docker, also in CI: GitHub runners and `act` have it; on GitLab and Gitea, the runner must give the job access to a Docker daemon (mounted socket or `DOCKER_HOST`).

## Run the CI locally

Pick [act](https://github.com/nektos/act) (GitHub, Gitea) or [gitlab-ci-local](https://github.com/firecow/gitlab-ci-local) (GitLab): `act:test` or `gitlab-ci-local:test` replays the CI of pull requests in Docker, as part of the test stage.

- It needs Docker, also in CI: GitHub runners have it; on GitLab, the task does nothing in a pipeline, and on Gitea it depends on the runner.
- Inside the replayed CI, its test job runs the task again: there it does nothing (act sets `ACT`, gitlab-ci-local sets `GITLAB_CI`), so the replay does not loop.
- In CI, the test job then replays the whole CI once more, which takes longer.

## Customize a version or a command

Each tool has one file with its version and its commands.
Answer yes to `customize_tools` and Copier asks, for each selected tool, a version and a command:

```text
Customize tool versions and commands? (y/N) y
ruff version (empty for brigade's):
Command of ruff:lint (empty for brigade's): ruff check src
```

- An answer replaces brigade's value, and stays on `brigade:update` until you change it.
- An empty answer takes brigade's value, and keeps following it on `brigade:update`. Clear an answer to go back to it.

Answers are named `<tool>_version` and `<tool>_<action>_command`, e.g. `ruff_version`, `zensical_serve_command`.
To change them later, see [Questions](questions.md).

Missing a tool? Add your own task: see [Custom tasks](custom-tasks.md).
