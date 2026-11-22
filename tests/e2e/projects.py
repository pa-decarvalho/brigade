"""The project types the tests create: their tools, files and publish.

Each one is created with its ecosystem's tools on top of brigade, publishes to
a Nexus repository (tests/fixtures/compose.yml) on its release tag, logged in
as Nexus' deploy user, and what it published is checked there.
"""

from dataclasses import dataclass, field

BASE = ["brigade", "yamllint", "gitleaks", "typos"]  # brigade's defaults


@dataclass(frozen=True)
class Project:
    tools: list[str]
    files: dict[str, str]  # written after Copier
    commands: list[list[str]]  # then run with mise exec (uv init, npm install...)
    env: dict[str, str]  # the project's mise.toml [env]: its registry, from CI
    # CI secrets; "{user}" and "{token}": the admin's; "{deploy_user}",
    # "{deploy_password}" and "{npm_token}": Nexus' (up.reset_registries)
    secrets: dict[str, str]
    published: tuple[str, str]  # (URL from this machine, text once "{tag}" is out)
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

# Bun builds and tests it itself; its own name in Nexus' npm repository.
BUN_PACKAGE = """{
\t"name": "@brigade-forges/bun-demo",
\t"version": "0.1.0",
\t"type": "module",
\t"main": "dist/index.js",
\t"files": [
\t\t"dist"
\t],
\t"scripts": {
\t\t"build": "bun build src/index.ts --outdir dist --target node",
\t\t"prepublishOnly": "bun run build"
\t},
\t"publishConfig": {
\t\t"access": "public"
\t}
}
"""

BUN_TEST = """import { expect, test } from "bun:test";
import { hello } from "../src/index.ts";

test("hello", () => {
\texpect(hello("demo")).toBe("Hello, demo!");
});
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

# Maven's layout; Releasaurus bumps <version> on each release (release_type java).
JAVA_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>demo</groupId>
    <artifactId>demo</artifactId>
    <version>0.1.0</version>
    <properties>
        <maven.compiler.release>21</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.13.4</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""

# Gradle's layout, by hand (gradle init would overwrite brigade's files first); Releasaurus
# bumps version = "..." on each release (release_type java). Its own name: Nexus' maven
# repository keeps the Maven project's demo/demo versions.
GRADLE_SETTINGS = 'rootProject.name = "demo-gradle"\n'

GRADLE_BUILD = """plugins {
    `java-library`
    `maven-publish`
}

group = "demo"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.13.4"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.withType<JavaCompile> {
    options.release = 21
}

tasks.test {
    useJUnitPlatform()
}

publishing {
    publications {
        create<MavenPublication>("lib") {
            from(components["java"])
        }
    }
}
"""

JAVA_HELLO = (
    "package demo;\n\npublic final class Hello {\n    private Hello() {\n    }\n\n"
    '    public static String hello() {\n        return "Hello from demo!";\n    }\n}\n'
)

JAVA_TEST = (
    "package demo;\n\nimport static org.junit.jupiter.api.Assertions.assertEquals;\n\n"
    "import org.junit.jupiter.api.Test;\n\nclass HelloTest {\n    @Test\n"
    '    void hello() {\n        assertEquals("Hello from demo!", Hello.hello());\n'
    "    }\n}\n"
)

PROJECTS = {
    # A library published to a Python index (Nexus' pypi repository).
    "python": Project(
        tools=[*BASE, "ruff", "pytest", "uv"],
        data={"uv_publish": True},
        files={"tests/test_demo.py": PYTHON_TEST},
        commands=[
            ["uv", "init", "-q", "--lib", "--vcs", "none", "--name", "demo"],
            ["uv", "add", "-q", "--dev", "pytest==9.2.0"],
        ],
        env={"UV_PUBLISH_URL": "http://nexus:8081/repository/pypi/"},
        secrets={
            "UV_PUBLISH_USERNAME": "{deploy_user}",
            "UV_PUBLISH_PASSWORD": "{deploy_password}",
        },
        published=("http://localhost:8099/repository/pypi/simple/demo/", "demo-{tag}"),
    ),
    # A TypeScript library published to an npm registry (Nexus' npm repository).
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
            # The scope's registry, its token; the rest from npmjs.
            ".npmrc": "@brigade-forges:registry=http://nexus:8081/repository/npm/\n"
            "//nexus:8081/repository/npm/:_authToken=${NPM_TOKEN}\n",
            "README.md": "# Demo\n\nA demo TypeScript library.\n",
        },
        commands=[["npm", "install", "--package-lock-only"]],
        env={},
        secrets={"NPM_TOKEN": "{npm_token}"},
        published=(
            "http://localhost:8099/repository/npm/@brigade-forges%2fdemo",
            '"{tag}"',
        ),
    ),
    # The same library with Bun, published to the same registry.
    "bun": Project(
        tools=[*BASE, "biome", "bun"],
        data={"bun_publish": True},
        files={
            "package.json": BUN_PACKAGE,
            "src/index.ts": "export function hello(name: string): string {\n"
            "\treturn `Hello, ${name}!`;\n}\n",
            "test/index.test.ts": BUN_TEST,
            ".gitignore": "node_modules/\ndist/\n",
            ".npmrc": "@brigade-forges:registry=http://nexus:8081/repository/npm/\n"
            "//nexus:8081/repository/npm/:_authToken=${NPM_TOKEN}\n",
            "README.md": "# Demo\n\nA demo TypeScript library, built with Bun.\n",
        },
        commands=[["bun", "install"]],
        env={},
        secrets={"NPM_TOKEN": "{npm_token}"},
        published=(
            "http://localhost:8099/repository/npm/@brigade-forges%2fbun-demo",
            '"{tag}"',
        ),
    ),
    # A Python app shipped as an image, pushed to a registry (Nexus' docker repository).
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
        # The host's Docker daemon pushes (compose.yml's nexus).
        env={"DOCKER_IMAGE": "localhost:5099/demo"},
        secrets={
            "DOCKER_USERNAME": "{deploy_user}",
            "DOCKER_PASSWORD": "{deploy_password}",
        },
        published=("http://localhost:5099/v2/demo/tags/list", '"{tag}"'),
        # The docker tool's validator: no Docker daemon in GitLab's CI yet.
        not_on=("gitlab",),
    ),
    # A Java library published to a Maven repository (Nexus' maven repository).
    "java-maven": Project(
        tools=[*BASE, "maven"],
        data={"maven_publish": True},
        files={
            "pom.xml": JAVA_POM,
            "src/main/java/demo/Hello.java": JAVA_HELLO,
            "src/test/java/demo/HelloTest.java": JAVA_TEST,
            ".gitignore": "target/\n",
            "README.md": "# Demo\n\nA demo Java library.\n",
        },
        commands=[],
        env={"MAVEN_REPOSITORY_URL": "http://nexus:8081/repository/maven/"},
        secrets={
            "MAVEN_USERNAME": "{deploy_user}",
            "MAVEN_PASSWORD": "{deploy_password}",
        },
        published=(
            "http://localhost:8099/repository/maven/demo/demo/maven-metadata.xml",
            "<version>{tag}</version>",
        ),
    ),
    # The same with Gradle, published by gradle:publish (its init script adds the repository).
    "java-gradle": Project(
        tools=[*BASE, "gradle"],
        data={"gradle_publish": True},
        files={
            "settings.gradle.kts": GRADLE_SETTINGS,
            "build.gradle.kts": GRADLE_BUILD,
            "src/main/java/demo/Hello.java": JAVA_HELLO,
            "src/test/java/demo/HelloTest.java": JAVA_TEST,
            ".gitignore": "/.gradle/\n/build/\n",  # anchored: see docs/tools.md
            "README.md": "# Demo\n\nA demo Java library, built with Gradle.\n",
        },
        commands=[],
        env={"MAVEN_REPOSITORY_URL": "http://nexus:8081/repository/maven/"},
        secrets={
            "MAVEN_USERNAME": "{deploy_user}",
            "MAVEN_PASSWORD": "{deploy_password}",
        },
        published=(
            "http://localhost:8099/repository/maven/demo/demo-gradle/maven-metadata.xml",
            "<version>{tag}</version>",
        ),
    ),
    # A Helm chart pushed to an OCI registry (Nexus' docker repository, plain HTTP).
    "helm": Project(
        tools=[*BASE, "helm"],
        data={"helm_publish": True},
        files={"README.md": "# Demo\n\nA demo Helm chart.\n"},
        commands=[["helm", "create", "demo"]],
        env={"HELM_REGISTRY": "http://nexus:5000/charts"},
        secrets={
            "HELM_REGISTRY_USERNAME": "{deploy_user}",
            "HELM_REGISTRY_PASSWORD": "{deploy_password}",
        },
        published=("http://localhost:5099/v2/charts/demo/tags/list", '"{tag}"'),
    ),
}

# The tests, by id (the <forge>:run and :test arguments): (project type, Releasaurus
# workflow). Each forge runs both workflows, on python.
CASES = {
    "python": ("python", "pr"),
    "python-direct": ("python", "direct"),
    **{kind: (kind, "pr") for kind in PROJECTS if kind != "python"},
}
