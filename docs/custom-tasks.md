# Custom tasks

mise loads every file in `.mise/conf.d/`. Copier never touches files that are not in the template, so your own files survive `brigade:update`.

A task named `<stage>:<name>` joins that stage, because each stage runs `<stage>:*`:

```toml
# .mise/conf.d/project.toml
[tools]
hadolint = "2.15.1"

[tasks."lint:hadolint"]
description = "Check the Dockerfile with hadolint"
run = "hadolint Dockerfile"

[tasks."test:integration"]
description = "Run integration tests"
run = "uv run pytest tests/integration"
```

`mise run lint` and `mise run test` now include them, locally and in CI.
Pick a file name brigade does not use (not `lint.toml`, `python.toml`, ...).
