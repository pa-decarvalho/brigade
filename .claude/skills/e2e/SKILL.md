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
applied from this checkout at its latest tag, pushed to the forge, then:
`<cli>:setup` and `<cli>:check`, a pull request (lint, build, test), the
release (release PR, `X.Y.Z` tag), the deploy to a local registry
(`tests/fixtures/compose.yml`: pypi, verdaccio, registry), and
`brigade:update` to the checkout's `HEAD` in a pull request whose CI passes.
The checkout is the projects' `_src_path`, mounted at the same path in the
jobs: uncommitted changes are in it.

`github` is a `ci: github` project on Gitea: no release nor deploy (GitHub's
API). No Renovate: its update is what `brigade:update` does.

## Run

- `mise run forges:test -- --forge <gitea|github|forgejo|gitlab>`: every
  project type; `-k <type>` for one. The forge starts on first use
  (`tests/e2e/up.py`, `.forges/<forge>.json`) and stays up: the next runs reuse
  it. GitLab takes a few minutes and about 4 GB: one forge at a time
  (`mise run forges:down` between them).
- Each type takes 5 to 10 minutes: run it in the background and wait for the
  notification.
- `mise run forges:up -- <forge>` prints the UI's URL and login; links the forge
  writes use its Docker name (`http://gitea:3000`): replace with the URL.
- `mise run forges:down` removes the forges and their data, then everything
  Docker no longer uses, Docker-wide (`docker system prune --all --volumes`).

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
   #301 the GitLab TLS proxy): `not_on` in `projects.py`, or a comment, never a
   silent skip.

Fill the note's "To improve" section, then report the table forge × type to the
user.

## Add a project type

- An entry in `PROJECTS` (`tests/e2e/projects.py`): its tools (copy a ctt
  variant's), files, commands (run with `mise exec` after `mise install`), the
  registry env and secrets, the deployed URL (from this machine) and the text
  it must hold, `not_on` for the forges brigade refuses it on.
- A registry it needs: a service in `tests/fixtures/compose.yml` (reset before
  each test by `up.reset_registries`), its URL by service name in `env` (the
  jobs) and by `localhost` in `deployed` (this machine).
- Run it on gitea, then the other forges.
