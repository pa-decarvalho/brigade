# Custom tasks

mise loads every file in `.mise/conf.d/`. Copier never touches files that are not in the template, so your own files survive `brigade:update`.

A task named `<name>:<stage>` joins that stage, because each stage runs `*:<stage>`:

```toml
# .mise/conf.d/project.toml
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
Pick a file name brigade does not use (not `tool-<tool>.toml` such as `tool-ruff.toml`, nor `stages.toml`).
