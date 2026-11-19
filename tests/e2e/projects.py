"""The project types the tests create: their tools, files and deploy.

Each one is created with its ecosystem's tools on top of brigade, deploys to a
registry of tests/fixtures/compose.yml on its release tag, and its deploy is
checked there.
"""

from dataclasses import dataclass, field

BASE = ["brigade", "yamllint", "gitleaks", "typos"]  # brigade's defaults


@dataclass(frozen=True)
class Project:
    tools: list[str]
    files: dict[str, str]  # written after Copier
    commands: list[list[str]]  # then run with mise exec (uv init, npm install...)
    env: dict[str, str]  # the project's mise.toml [env]: its registry, from CI
    secrets: dict[str, str]  # CI secrets; "{user}" and "{token}": the admin's
    deployed: tuple[str, str]  # (URL from this machine, text once "{tag}" is out)
    data: dict = field(default_factory=dict)  # more Copier answers
    not_on: tuple[str, ...] = ()  # forges brigade refuses it on


PYTHON_TEST = "import demo\n\n\ndef test_hello():\n    assert demo.hello()\n"

NODE_PACKAGE = """{
\t"name": "@brigade-forges/demo",
\t"version": "0.1.0",
\t"type": "module",
\t"main": "dist/index.js",
\t"types": "dist/index.d.ts",
\t"files": [
\t\t"dist"
\t],
\t"scripts": {
\t\t"build": "tsc",
\t\t"test": "node --test",
\t\t"prepublishOnly": "npm run build"
\t},
\t"publishConfig": {
\t\t"access": "public"
\t},
\t"devDependencies": {
\t\t"typescript": "7.0.2"
\t}
}
"""

NODE_TSCONFIG = """{
\t"compilerOptions": {
\t\t"target": "ES2022",
\t\t"module": "NodeNext",
\t\t"declaration": true,
\t\t"rootDir": "src",
\t\t"outDir": "dist",
\t\t"strict": true
\t},
\t"include": ["src"]
}
"""

NODE_TEST = """import assert from "node:assert/strict";
import { test } from "node:test";
import { hello } from "../src/index.ts";

test("hello", () => {
\tassert.equal(hello("demo"), "Hello, demo!");
});
"""

DOCKERFILE = """FROM ghcr.io/astral-sh/uv:0.13.8-python3.14-trixie-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
USER 65534
HEALTHCHECK NONE
ENTRYPOINT ["/app/.venv/bin/demo"]
"""

# One string: the indentation of YAML in a Python block breaks editorconfig's.
STRUCTURE_TEST = (
    "---\nschemaVersion: 2.0.0\nmetadataTest:\n"
    '  user: "65534"\n  entrypoint: [/app/.venv/bin/demo]\n'
    "commandTests:\n  - name: the app runs\n    command: /app/.venv/bin/demo\n"
    "    expectedOutput: [Hello from demo!]\n"
)

PROJECTS = {
    # A library published to a Python index (pypi).
    "python": Project(
        tools=[*BASE, "ruff", "pytest", "uv"],
        data={"uv_publish": True},
        files={"tests/test_demo.py": PYTHON_TEST},
        commands=[
            ["uv", "init", "-q", "--lib", "--vcs", "none", "--name", "demo"],
            ["uv", "add", "-q", "--dev", "pytest==9.2.0"],
        ],
        env={"UV_PUBLISH_URL": "http://pypi:8080/"},
        secrets={"UV_PUBLISH_USERNAME": "{user}", "UV_PUBLISH_PASSWORD": "{token}"},
        deployed=("http://localhost:8099/simple/demo/", "demo-{tag}"),
    ),
    # A TypeScript library published to an npm registry (verdaccio).
    "node": Project(
        tools=[*BASE, "biome", "node"],
        data={"npm_publish": True},
        files={
            "package.json": NODE_PACKAGE,
            "tsconfig.json": NODE_TSCONFIG,
            "src/index.ts": "export function hello(name: string): string {\n"
            "\treturn `Hello, ${name}!`;\n}\n",
            "test/index.test.ts": NODE_TEST,
            ".gitignore": "node_modules/\ndist/\n",
            ".npmrc": "//verdaccio:4873/:_authToken=${NPM_TOKEN}\n",
            "README.md": "# Demo\n\nA demo TypeScript library.\n",
        },
        # This machine resolves packages from npmjs (verdaccio is the jobs').
        commands=[
            [
                "env",
                "NPM_CONFIG_REGISTRY=https://registry.npmjs.org/",
                "npm",
                "install",
                "--package-lock-only",
            ],
        ],
        env={"NPM_CONFIG_REGISTRY": "http://verdaccio:4873/"},
        secrets={"NPM_TOKEN": "{token}"},
        deployed=("http://localhost:4873/@brigade-forges%2fdemo", '"{tag}"'),
    ),
    # A Python app shipped as an image, pushed to a registry (registry).
    "docker": Project(
        tools=[
            *BASE,
            "ruff",
            "hadolint",
            "pytest",
            "docker",
            "container-structure-test",
        ],
        files={
            "Dockerfile": DOCKERFILE,
            ".dockerignore": ".git\n.venv\n.mise-data\n.ruff_cache\n.pytest_cache\n",
            "README.md": "# Demo\n\nA demo app, shipped as a Docker image.\n",
            "tests/test_main.py": "import demo\n\n\ndef test_main(capsys):\n"
            '    demo.main()\n    assert capsys.readouterr().out == "Hello from demo!\\n"\n',
            ".brigade/configs/container-structure-test.yaml": STRUCTURE_TEST,
        },
        commands=[
            ["uv", "init", "-q", "--package", "--vcs", "none", "--name", "demo"],
            ["uv", "add", "-q", "--dev", "pytest==9.2.0"],
        ],
        # The host's Docker daemon pushes (compose.yml's registry).
        env={"DOCKER_IMAGE": "localhost:5099/demo"},
        secrets={},
        deployed=("http://localhost:5099/v2/demo/tags/list", '"{tag}"'),
        # The docker tool's validator: no Docker daemon in GitLab's CI yet.
        not_on=("gitlab",),
    ),
}
