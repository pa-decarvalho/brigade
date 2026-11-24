"""The project types the tests create: their tools, secrets and publish.

Each one is brigade, then its files (tests/fixtures/projects/<type>/: its code,
lockfiles and mise.toml, without brigade); it publishes to a Nexus repository
(tests/fixtures/compose.yml) on its release tag, logged in as Nexus' deploy
user, and what it published is checked there.
"""

from dataclasses import dataclass, field

BASE = ["brigade", "yamllint", "gitleaks", "typos"]  # brigade's defaults


@dataclass(frozen=True)
class Project:
    tools: list[str]
    # CI secrets; "{user}" and "{token}": the admin's; "{deploy_user}",
    # "{deploy_password}" and "{npm_token}": Nexus' (up.reset_registries);
    # "{kubeconfig}": the cluster's (up.reset_cluster); "{ssh_private_key}":
    # the SSH server's key (up.reset_ssh_target)
    secrets: dict[str, str]
    # (URL from this machine, text once "{tag}" is out); None: nothing published
    published: tuple[str, str] | None
    data: dict = field(default_factory=dict)  # more Copier answers
    not_on: tuple[str, ...] = ()  # forges brigade refuses it on
    # Where its deploy goes, checked per environment of its environments answer:
    # "cluster" (k3s, up.reset_cluster), "ssh" (a server, up.reset_ssh_target).
    target: str = ""
    # The image its cluster deploy must run ("{tag}": the release's), if any.
    image: str = ""


PROJECTS = {
    # A library published to a Python index (Nexus' pypi repository).
    "python": Project(
        tools=[*BASE, "ruff", "pytest", "uv"],
        data={"uv_publish": True},
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
        # Installed on the cluster: dev once published, prod by hand.
        data={
            "helm_publish": True,
            "helm_install": True,
            "environments": [{"name": "dev", "auto": True}, {"name": "prod"}],
        },
        target="cluster",
        secrets={
            "HELM_REGISTRY_USERNAME": "{deploy_user}",
            "HELM_REGISTRY_PASSWORD": "{deploy_password}",
            "KUBECONFIG_DATA": "{kubeconfig}",
        },
        published=("http://localhost:5099/v2/charts/demo/tags/list", '"{tag}"'),
    ),
    # An app published then deployed: its image (docker:publish) and its chart
    # (helm:publish), at the project's root so that Releasaurus sets the chart's
    # version to the release, which the image tag follows; installed on the
    # cluster (helm:deploy), which pulls the image from Nexus: dev once
    # published, prod by hand. Not on GitLab: no Docker daemon in brigade's
    # image (#208).
    "app": Project(
        tools=[*BASE, "docker", "helm"],
        data={
            "helm_publish": True,
            "helm_install": True,
            "environments": [{"name": "dev", "auto": True}, {"name": "prod"}],
        },
        target="cluster",
        image="localhost:5099/demo:{tag}",
        not_on=("gitlab",),
        secrets={
            "DOCKER_USERNAME": "{deploy_user}",
            "DOCKER_PASSWORD": "{deploy_password}",
            "HELM_REGISTRY_USERNAME": "{deploy_user}",
            "HELM_REGISTRY_PASSWORD": "{deploy_password}",
            "KUBECONFIG_DATA": "{kubeconfig}",
        },
        published=("http://localhost:5099/v2/demo/tags/list", '"{tag}"'),
    ),
    # A playbook deployed over SSH to a server (up.reset_ssh_target), with a
    # vault-encrypted variable: dev once published, prod by hand. Not on GitLab:
    # brigade's image has no SSH client (#139).
    "ansible": Project(
        tools=[*BASE, "ansible"],
        data={"environments": [{"name": "dev", "auto": True}, {"name": "prod"}]},
        target="ssh",
        not_on=("gitlab",),
        secrets={
            "ANSIBLE_PRIVATE_KEY": "{ssh_private_key}",
            "ANSIBLE_VAULT_PASSWORD": "brigade",
        },
        published=None,
    ),
}

# The tests, by id (the e2e:* tasks' arguments): (project type, Releasaurus
# workflow). Each forge runs both workflows, on python.
CASES = {
    "python": ("python", "pr"),
    "python-direct": ("python", "direct"),
    **{kind: (kind, "pr") for kind in PROJECTS if kind != "python"},
}
