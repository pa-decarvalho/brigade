---
name: add-tool
description: Add one or more tools (linters, formatters, test or deploy tools) to brigade's tool catalog — fragment, questions, choice, ctt test, docs, epic #138. Use when asked to add a tool, a linter, or the next tools of #138.
---

# Add a tool to the catalog

Follow CLAUDE.md's rules; this is the checklist they imply. Reply in the user's language; files in English.

## 1. Check the tool first (in the scratchpad, not the repo)

- `mise registry <tool>`: prefer an `aqua:`/`github:` binary, else `pipx:`/`npm:`. Latest version: `gh release view -R <owner>/<repo> --json tagName`.
  - aqua's registry can miss platforms the release has (dotenv-linter: no linux/arm64, which act uses on Apple Silicon): compare with `gh release view <tag> -R <owner>/<repo> --json assets`, and use `github:<owner>/<repo>` then.
  - A tool that needs a runtime (golangci-lint: Go) relies on the project's `mise.toml` for it, as `pytest` relies on the project's dependencies.
  - A tool that needs a config file to do anything (vale, kubeconform's manifest folder) waits for #145.
- In a scratch dir with a `mise.toml` pinning it, run its command and check:
  - **file discovery**: does it walk the folder itself? Does it skip hidden folders and `.mise-data/` (GitLab's tool cache, inside the project)? Put a bad file in `.mise-data/x/` and see. Exclude it with the tool's option (`--exclude .mise-data`...). A tool that cannot exclude it is a poor fit (biome was left out for this).
  - **files it writes** in the project (caches: `--no-cache`).
  - **no input files**: must pass, not fail or wait for stdin.
  - **network** needs, and whether results can change without a project change (say so in the docs).
  - **CI-only behavior**: CI sets env vars a local run lacks (`GITHUB_TOKEN`, `GITHUB_ACTIONS`, `CI`). Run it once with them set to dummy values and check it writes nothing (checkov wrote `github_conf/`).
- A tool that takes a file list: a Python glob run by uv, as in `hadolint` or `shellcheck` (no shell, works on Windows; `glob` skips hidden folders):
  `uv run --no-project python -c "import glob, subprocess, sys; files = glob.glob('**/*.sh', recursive=True); sys.exit(subprocess.call(['<tool>', *files]) if files else 0)"`
- Clean up afterwards: tools installed from the scratchpad leave global mise shims (`mise uninstall <tool> --all && mise reshim`); a shim with no version breaks tools that look it up in PATH (jactionlint and shellcheck).

## 2. Files

Copy an existing tool of the same kind (`gitleaks` for a plain binary, `hadolint` for a file list, `ansible-lint` for `pipx:`).

- `template/.brigade/tools/{% if '<tool>' in tools %}<tool>-brigade.toml{% endif %}.jinja`:
  - `# renovate: datasource=<github-releases|pypi|npm> depName=<owner/repo|package>` on the line above `<tool> = "{{ <tool_>_version | default('<pin>', true) }}"`. The `customManagers` regex in `.github/renovate.json5` reads it; a pin elsewhere in the line (`uvx_args`...) needs its own entry there.
  - `[tasks."<tool>:<stage>"]` with `description`, `{% raw %}dir = "{{config_root}}/../.."{% endraw %}` and one `run = '''{{ <tool_>_<action>_command | default('<command>', true) }}'''`. Inside a `default("...")` with double quotes, escape inner `"` as `\"`.
  - In variable names, `-` becomes `_` (`osv_scanner_version`).
- `.copier/questions/tools/<tool>.yml`: copy `gitleaks.yml`, replace the name (`sed 's/gitleaks/<tool>/g'`, then fix `-` → `_` in the variable names only).
- `.copier/questions/common.yml`: a choice `<tool> (<stage>): <tool>` next to tools of the same stage; a `validator` on `ci` when it only fits one CI platform (`zizmor`).
- `docs/tools.md`: a catalog row (tool, task, command and what it excludes); a "Platforms" line if it does not run on Windows.
- `ctt.toml`: add it to a variant whose project type fits (`none-github` for generic linters, `python-gitlab` to test the `.mise-data` exclusion inside the gitlab-ci-local replay), with a file for it to check (`_post_tasks`, written with `uv run --no-project python -c`; in TOML basic strings, `\\n` is a Python `\n` and `\"` a quote).

## 3. Verify

- `mise run lint`, `mise run build`.
- Start Docker first (`docker info`; macOS: `open -a Docker`).
- `git add -A && mise run test; git reset -q` (ctt only sees tracked files; needs Docker). Check the tool's lines in the log, also inside the act / gitlab-ci-local replays.
- Fix what the new tool finds in brigade's own generated files (as `zizmor` did) rather than weakening its command.

## 4. Deliver

- Ask before committing, pushing or opening the PR. Branch `feat/<tool>` (or `feat/linters` for a batch), title `feat: add <tool> to the tool catalog`, body "Part of #138", no AI attribution.
- Once merged: tick the tool in #138 (`gh issue view 138 --json body -q .body > <scratchpad>/138.md`, edit, `gh issue edit 138 --body-file ...`) with the PR number.
