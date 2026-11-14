# Custom tasks

*The chef's specials: your own tasks, next to the house menu.*

mise reads the files listed in `.miserc.toml`: brigade's, in `.brigade/`, then your own `mise.toml` and `mise.local.toml` at the project root. Copier never touches them, so your tasks and tools survive `brigade:update`. A file elsewhere (such as `.mise/conf.d/`) is not read.

A task named `<name>:<stage>` joins that stage, because each stage runs `*:<stage>`:

```toml
# mise.toml
[tools]
hadolint = "2.15.1"

[tasks."hadolint:lint"]
description = "Check the Dockerfile with hadolint"
run = "hadolint Dockerfile"

[tasks."integration:test"]
description = "Run integration tests"
run = "uv run pytest tests/integration"
```

`mise run lint` and `mise run test` now include them, locally and in CI.

## System packages

Some tools need OS packages (a library, an SSH client...) that mise tools do not cover. Declare them in your `mise.toml`, then install them with `mise bootstrap packages apply`:

```toml
# mise.toml
[bootstrap.packages]
"apt:openssh-client" = "latest"  # Debian, Ubuntu
"brew:jq" = "latest"             # macOS
```

mise never installs them on its own, and an entry is skipped on an OS its package manager does not run on. They are installed for the whole machine (often with `sudo`), not for the project, and Renovate does not update them. brigade does not generate them: see [#188](https://github.com/pa-decarvalho/brigade/issues/188).
