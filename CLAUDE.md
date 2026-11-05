# CLAUDE.md — brigade

## What this project is

`brigade` is a [Copier](https://copier.readthedocs.io/) template that bootstraps new projects managed with [mise](https://mise.jdx.dev/) (mise-en-place).

The user picks a **project type** (e.g. `python`, `ansible`, `rust`…) and the template renders:

- a **common layer** shared by every project (mise bootstrap launchers, base mise config, `.gitattributes`, `.gitignore`, CI…);
- the **files specific to the chosen type** (tools, tasks, scripts, config files).

Generated projects must stay updatable with `copier update`.

## Core principles

1. **Cross-platform first.** Every generated project must work out of the box on Linux, macOS and Windows: installing mise, installing tools, running tasks.
2. **No bash in the template.** No shell scripts, no shebang-based file tasks, no shell-specific syntax (`&&`, `$VAR`, `$@`, pipes, redirections, globs) in task commands.
3. **Python + uv for any real logic.** Any task that needs more than "run a tool with options" is a Python script run with `uv run`, declaring its own dependencies with PEP 723 inline metadata. Use `pathlib`, `subprocess`, `shutil` for portability; use Click for CLI arguments.
4. **Small files over big files.** Each project type drops whole files rather than editing blocks inside shared files. This keeps `copier update` conflicts low and avoids Jinja conditionals inside shared config.
5. **Pinned versions.** Pin mise itself, the tools and Copier. Never rely on `latest` in generated projects.

## Repository layout

```
brigade/
├── CLAUDE.md
├── copier.yml            # questions, _subdirectory: template, _tasks, _exclude
├── template/             # rendered content (Copier _subdirectory)
│   └── ...
├── tests/                # render tests for every project type
└── .mise/                # mise config for developing the template itself
```

## Generated project layout (target)

```
<project>/
├── bin/
│   ├── mise              # bash bootstrap launcher (LF)
│   └── mise.cmd          # Windows bootstrap launcher (CRLF) — exact filename to confirm
├── .mise/
│   ├── config.toml       # [tools], [settings], [task_config]
│   ├── conf.d/           # one fragment per concern / project type, loaded alphabetically
│   │   ├── 00-common.toml
│   │   └── 10-<type>.toml
│   ├── tasks/            # optional task files (TOML only)
│   ├── config.ci.toml    # loaded when MISE_ENV=ci
│   └── config.local.toml # personal overrides, gitignored
├── scripts/              # cross-platform Python scripts (uv run)
├── .gitattributes
├── .gitignore
└── .copier-answers.yml
```

Rules:

- Use **only** `.mise/` for mise config. Do not also create a root `mise.toml`; mixing locations makes precedence confusing (`mise cfg` shows the real load order).
- Prefix `conf.d` fragments with numbers to control load order.
- Avoid dots in `conf.d` fragment names (e.g. `tools.ci.toml`): environment-suffixed fragments are opt-in via `env_conf_d` in `miserc.toml` until mise 2027.8.10 and will change meaning afterwards.

## mise bootstrap

- Launchers are generated with `mise generate bootstrap --write --windows` (the `--windows` flag requires mise ≥ 2026.8.7). `--windows` is mandatory: without it only a bash launcher is produced.
- `--localize` is **optional**, exposed as a Copier question (default: off). It sandboxes mise data/cache into the project's `.mise/` instead of the user's home directory. When enabled, `.gitignore` must exclude **only** those generated subdirectories, never the committed config.
- Launchers embed checksums at generation time: regenerate them whenever the pinned mise version is bumped. This is a maintenance task of the template repo, not of generated projects.

## Tasks

- Define tasks in TOML (`.mise/config.toml`, `conf.d` fragments, or files included via `[task_config] includes`).
- One tool invocation per command; chain commands with a list: `run = ["ruff check .", "ruff format --check ."]`.
- Environment variables go in the task `env` table, not inline.
- Use `run_windows` only for genuine exceptions.
- Logic → `run = "uv run scripts/<name>.py"`.
- Extra CLI arguments: use mise `usage` specs, never `$@`.

## Copier conventions

- Template content lives in `template/` (`_subdirectory: template`).
- Project-type selection is a single-choice question (`project_type`). Start with one type per project; no multi-select until the single-type path is solid.
- Type-specific files are conditional via Jinja in file/dir names or `_exclude`.
- `_tasks` must be portable: use list-form commands (no shell) or Python. If an OS-specific branch is unavoidable, use `when:` with `_copier_conf.os` (`"linux"`, `"macos"`, `"windows"`).
- Tasks that run commands require `copier copy --trust`; document it in the README.

## AI agent tooling (for working on this repo)

These tools are part of the Claude Code setup of **this repository**, not of the template output (generated projects do not get them for now):

| Tool | What it does | Source |
|---|---|---|
| `context-mode` | MCP server + hooks that keep large tool outputs out of the context window | <https://github.com/mksglu/context-mode> |
| `ponytail` | Plugin that pushes the agent toward the simplest solution (less code) | <https://github.com/DietrichGebert/ponytail> |
| `graphify` | Builds a queryable knowledge graph of the codebase (`/graphify` skill) | <https://github.com/Graphify-Labs/graphify> |

Notes:

- context-mode may create or modify a root `CLAUDE.md` with its routing rules: keep this file as the source of truth and merge those rules here.
- `graphify` output (`graphify-out/`) must not be committed unless explicitly decided.

## Line endings

`.gitattributes` must enforce:

- `* text=auto eol=lf` by default;
- CRLF for Windows launchers (`*.cmd`, `*.bat`, `*.ps1` if any);
- LF for the bash launcher.

## Testing

- Render every project type in CI and run its main tasks (`mise run lint`, `mise run test`…).
- Target Linux, macOS and Windows runners when available; Linux at minimum.

## Known constraints / to verify

- **Corporate network:** downloads go through a Nexus "raw" proxy to GitHub (release assets only, no git clone). Check how to override the download base URL in the bootstrap launchers and for tool backends.
- Some tools in the mise registry may lack Windows builds: check each tool for each project type.
- How mise injects `usage` arguments under `cmd.exe`: validate on a real Windows machine.
- Exact names of the subdirectories created by `--localize` inside `.mise/`.
- Windows support in mise is recent and moves fast: pin a tested mise version.

## Conventions for contributions

- All code, comments, help texts and variable names in **English**.
- Keep answers and changes grounded in official docs (Copier, mise); cite the source when introducing a non-obvious behavior.
