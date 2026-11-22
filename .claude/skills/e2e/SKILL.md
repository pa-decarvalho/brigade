---
name: e2e
description: Run brigade's end-to-end tests on a local forge (Gitea, Forgejo, GitLab, github on Gitea) for one or more project types, read their notes, and turn what fails into fixes or issues; also add a project type. Use when asked to test brigade for real, on a forge, end to end, or before a release.
---

# End-to-end tests on local forges

Reply in the user's language; files in English. Local only: Docker, nothing
pushed anywhere but the local forge.

## What they test

`tests/e2e/test_projects.py`, one test per project type (`tests/e2e/projects.py`),
in a temporary folder: the project created with its ecosystem's tool, brigade
applied from this checkout at its latest tag (at its `HEAD` when that release
lacks a tool or an answer of the type, or with `E2E_FROM_HEAD=1`: no update
step then), pushed to the forge, then:
`<cli>:setup` and `<cli>:check`, a pull request (lint, build, test),
`brigade:update` to the checkout's `HEAD` in a pull request whose CI passes
(both merged), then the release (release PR, `X.Y.Z` tag), the publish to a
local Nexus (`tests/fixtures/compose.yml`: pypi, npm, maven and docker
repositories, logged in as its deploy user) and the deploy publish starts on the
tag, all made by the checkout's files: a fix to them is tested before its
release. The `helm` type also installs on a k3s cluster (profile `cluster`,
`up.reset_cluster`): `dev` once published, `prod` by hand
(`Forge.deploy_by_hand`), each checked with `kubectl rollout status`. Answers
the latest release lacks go in `Project.data_later`, added for the update.
The checkout is the projects' `_src_path`, mounted at the same path in the
jobs: uncommitted changes are in it.

`github` is a `ci: github` project on Gitea: no release, publish nor deploy (GitHub's
API). No Renovate: its update is what `brigade:update` does.

## Run

- Per forge (`gitea`, `github`, `forgejo`, `gitlab`; `tests/e2e/up.py`):
  `<forge>:up` (start, admin token, runner; `.forges/<server>.json`),
  `<forge>:run [type...]` (the tests on it: `python`, `python-direct`,
  `node`, `bun`, `docker`, `java-maven`, `java-gradle`, `helm`; all by
  default), `<forge>:down`
  (remove it and its data; images stay),
  `<forge>:test` (up, run, down). To investigate: `up`, `run` as often as
  needed, `down` at the end. Every forge: `forges:test [type...]` (each in
  turn, then the big Docker-wide cleanup). GitLab takes a few minutes and,
  with Nexus and the jobs, about 3.2 GB at peak: one forge at a time.
- Each type takes 5 to 10 minutes: run it in the background and wait for the
  notification.
- `<forge>:up` prints the UI's URL and login; links the forge writes use its
  Docker name (`http://gitea:3000`): replace with the URL.

## Read the results

Each test writes `.forges/<date>-<forge>-<type>.md`: the steps (result, time,
error), the failed jobs' last log lines. For each failure:

1. Test or brigade? A wrong assumption in the tests (a registry not reset, a
   timeout, a forge API detail) is fixed in `tests/e2e/`. A generated file, task
   or CI job that fails is brigade's.
2. A brigade bug: find the cause in `template/` (`path:line`), check whether a
   ctt variant could have seen it, then fix it or open an issue with the
   `issue` skill (the note's log lines as evidence).
3. A known limit (a validator refusing a tool on a CI, #299 tea on Forgejo,
   #302 Releasaurus on Forgejo): `not_on` in `projects.py`, or a comment,
   never a silent skip.

Fill the note's "To improve" section, then report the table forge × type to the
user.

## Add a project type

- An entry in `PROJECTS` (`tests/e2e/projects.py`): its tools (copy a ctt
  variant's), files, commands (run with `mise exec` after `mise install`), the
  registry env and secrets, the published URL (from this machine) and the text
  it must hold, `not_on` for the forges brigade refuses it on.
- A registry it needs: a Nexus hosted repository in `up.REPOSITORIES` (emptied
  before each test by `up.reset_registries`), its URL by service name in `env`
  (`http://nexus:8081/repository/<name>/`, the jobs) and by `localhost:8099` in
  `published` (this machine, anonymous reads); its login from the secrets'
  `{deploy_user}`, `{deploy_password}` or `{npm_token}`.
- Its test id (`CASES` in `projects.py`, the type's name) in the help of the
  `<forge>:run` and `<forge>:test` tasks (`mise.toml`, `usage`): mise cannot
  list choices for a repeatable argument, `up.py` checks the names.
- Run it on gitea, then the other forges.
