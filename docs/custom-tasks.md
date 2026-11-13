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
