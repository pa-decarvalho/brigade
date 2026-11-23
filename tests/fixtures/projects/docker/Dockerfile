FROM ghcr.io/astral-sh/uv:0.13.8-python3.14-trixie-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
USER 65534
HEALTHCHECK NONE
ENTRYPOINT ["/app/.venv/bin/demo"]
