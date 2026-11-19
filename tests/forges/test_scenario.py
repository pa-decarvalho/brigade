"""brigade end to end on a local forge: one test per step, in order.

From brigade's latest release to the local checkout: a new project, its first
pull request, release, deploy, then Renovate's update to the checkout (a test
tag on brigade's mirror, the next patch version).
"""

import json
import re
from pathlib import Path

import pytest  # ty: ignore[import-not-found]  # run with uv run --with pytest (run.py)
from conftest import WORK, Forge, sh

UV = ["mise", "x", "uv@0.13.9", "python@3.14", "--"]
COPIER = [*UV, "uvx", "copier@9.19.1"]
SEMVER = re.compile(r"\d+\.\d+\.\d+")


def project(state: dict) -> Path:
    return WORK / f"demo-{state['run']}"


def moved(forge: Forge, repo: str, before: str) -> str:
    """The default branch's new commit after a merge (forges update it async)."""
    return forge.wait_for(
        "merge commit", lambda: forge.head(repo) != before and forge.head(repo), 120
    )


def github_api(forge: Forge) -> None:
    if forge.name == "github":
        pytest.skip("not covered: GitHub's API (Releasaurus, Renovate, Pages, gh)")


def test_1_mirror(forge: Forge, state: dict) -> None:
    """brigade's checkout on the forge, with a test tag for the update."""
    src = WORK / f"brigade-{state['run']}"
    sh("git", "clone", "-q", "/brigade", str(src))
    tags = sh("git", "tag", "-l", cwd=src).split()
    latest = max(
        (t for t in tags if SEMVER.fullmatch(t)),
        key=lambda t: tuple(map(int, t.split("."))),
    )
    major, minor, patch = map(int, latest.split("."))
    test_tag = f"{major}.{minor}.{patch + 1}"
    sh("git", "tag", test_tag, cwd=src)
    repo = f"brigade-{state['run']}"
    forge.create_repo(repo)
    forge.disable_ci(repo)  # Gitea and Forgejo run .github/workflows/ too
    sh(
        "git",
        "push",
        "-q",
        forge.remote(repo),
        "HEAD:refs/heads/main",
        "--tags",
        cwd=src,
    )
    head = sh("git", "rev-parse", "--short", "HEAD", cwd=src).strip()
    forge.notes.append(
        f"brigade's mirror: {forge.src_path(repo)}, from {latest} to the checkout's"
        f" HEAD {head} as {test_tag} (uncommitted changes are not in it)"
    )
    state.update(src=forge.src_path(repo), latest=latest, test_tag=test_tag)


def test_2_project(forge: Forge, state: dict) -> None:
    """A new Python project, brigade's latest release applied, pushed."""
    path = project(state)
    path.mkdir()
    tools = ["brigade", "yamllint", "gitleaks", "typos", "ruff", "pytest", "uv"]
    if forge.name != "github":
        tools += ["releasaurus", "renovate"]
    if forge.name == "forgejo":
        # mise installs tea from gitea.com with the job's Forgejo token: 401.
        forge.notes.append(
            "tea left out of the project: its install fails in Forgejo's CI"
            " (mise's forgejo: backend, 401 from gitea.com)"
        )
    elif forge.cli:
        tools.append(forge.cli)
    sh("git", "init", "-q", "-b", "main", cwd=path)
    sh(
        *COPIER, "copy", "--trust", "--defaults", "--vcs-ref", state["latest"],
        "--data", f"ci={forge.ci}",
        "--data", f"tools={json.dumps(tools)}",
        "--data", f"uv_publish={json.dumps(forge.name != 'github')}",
        state["src"], ".", cwd=path,
    )  # fmt: skip
    sh(*UV, "uv", "init", "-q", "--lib", "--vcs", "none", "--name", "demo", cwd=path)
    sh(*UV, "uv", "add", "-q", "--dev", "pytest==9.2.0", cwd=path)
    (path / "tests").mkdir()
    (path / "tests" / "test_demo.py").write_text(
        "import demo\n\n\ndef test_hello():\n    assert demo.hello()\n"
    )
    repo = f"demo-{state['run']}"
    forge.create_repo(repo)
    if forge.name != "github":
        # Another index: the project's env, as docs/tools.md says.
        (path / "mise.toml").write_text(f'[env]\nUV_PUBLISH_URL = "{forge.PYPI}/"\n')
    sh("mise", "install", cwd=path)
    sh("mise", "-C", ".brigade", "lock", cwd=path)
    sh("git", "add", "-A", cwd=path)
    sh("git", "commit", "-qm", "chore: init", cwd=path)
    sh("git", "remote", "add", "origin", forge.remote(repo), cwd=path)
    entry = {"github": ".github/workflows/lint.yml", "gitlab": ".gitlab-ci.yml"}
    assert (path / entry.get(forge.ci, ".gitea/workflows/lint.yml")).exists()
    state["repo"] = repo


def test_3_settings(forge: Forge, state: dict) -> None:
    """Secrets set through the API, <cli>:setup and <cli>:check, then the push."""
    repo, path = state["repo"], project(state)
    if forge.name != "github":
        forge.set_secret(repo, "RENOVATE_TOKEN", forge.token)
        forge.set_secret(repo, forge.releasaurus_secret, forge.token)
        forge.set_secret(repo, "UV_PUBLISH_USERNAME", forge.user)
        forge.set_secret(repo, "UV_PUBLISH_PASSWORD", forge.token)
        forge.notes.append(
            f"secrets set through the API: RENOVATE_TOKEN, {forge.releasaurus_secret},"
            " UV_PUBLISH_USERNAME, UV_PUBLISH_PASSWORD (the admin's token)"
        )
    if forge.cli:
        sh("mise", "exec", "--", *forge.login(), cwd=path)
        print(sh("mise", "run", f"{forge.cli}:setup", cwd=path))
        print(sh("mise", "run", f"{forge.cli}:check", cwd=path))
    else:
        forge.notes.append("no <cli>:setup nor <cli>:check: no forge CLI here")
    sh("git", "push", "-q", "-u", "origin", "main", cwd=path)
    if forge.name != "github":  # release.yml, on pushes to main
        sha = sh("git", "rev-parse", "HEAD", cwd=path).strip()
        forge.wait_runs(repo, sha, "push", timeout=900)


def test_4_pull_request(forge: Forge, state: dict) -> None:
    """A change in a pull request: lint, build and test pass."""
    repo, path = state["repo"], project(state)
    sh("git", "switch", "-q", "-c", "hello", cwd=path)
    readme = path / "README.md"
    readme.write_text(readme.read_text() + "\nSays hello.\n")
    sh("git", "commit", "-qam", "feat: say hello", cwd=path)
    sh("git", "push", "-q", "-u", "origin", "hello", cwd=path)
    pr = forge.open_pr(repo, "hello", "feat: say hello")
    sha = sh("git", "rev-parse", "HEAD", cwd=path).strip()
    names = () if forge.name == "gitlab" else ("lint", "test")
    forge.wait_runs(repo, sha, "pull_request", names=names)
    state["pr"] = pr


def test_5_release(forge: Forge, state: dict) -> None:
    """Merge: a release PR, then once merged an X.Y.Z tag."""
    github_api(forge)
    repo = state["repo"]
    before = forge.head(repo)
    forge.merge_pr(repo, state["pr"], "feat: say hello")
    forge.wait_runs(repo, moved(forge, repo, before), "push")
    found = forge.wait_for("release PR", lambda: forge.find_pr(repo, "release"), 300)
    pr, title, sha = found
    assert title.startswith("chore(main): release"), title
    names = () if forge.name == "gitlab" else ("lint", "test")
    forge.wait_runs(repo, sha, "pull_request", names=names)
    before = forge.head(repo)
    forge.merge_pr(repo, pr, title)
    tag_sha = moved(forge, repo, before)
    tags = forge.wait_for(
        "X.Y.Z tag", lambda: [t for t in forge.tags(repo) if SEMVER.fullmatch(t)], 600
    )
    assert all(SEMVER.fullmatch(t) for t in forge.tags(repo)), forge.tags(repo)
    state["tag"], state["tag_sha"] = tags[0], tag_sha


def test_6_deploy(forge: Forge, state: dict) -> None:
    """The tag deploys the package to the index (compose.yml's pypi)."""
    github_api(forge)
    repo, tag = state["repo"], state["tag"]
    names = (tag,) if forge.name == "gitlab" else ("deploy",)
    forge.wait_runs(repo, state["tag_sha"], "push", names=names)
    page = forge.wait_for("published package", lambda: forge.packages("demo"), 120)
    assert f"demo-{tag}" in page, page


def test_7_operate(forge: Forge, state: dict) -> None:
    """Renovate, run by hand: an update PR to the test tag."""
    github_api(forge)
    repo = state["repo"]
    forge.run_operate(repo)
    found = forge.wait_for(
        "brigade update PR", lambda: forge.find_pr(repo, "update brigade"), 1500
    )
    pr, title, sha = found
    # Renovate writes semver versions as vX.Y.Z in titles.
    assert title == f"ci(deps): update brigade to v{state['test_tag']}", title
    state["update"] = (pr, title, sha)


def test_8_update(forge: Forge, state: dict) -> None:
    """The update PR passes and merges: the project is on the checkout."""
    github_api(forge)
    repo = state["repo"]
    pr, title, sha = state["update"]
    names = () if forge.name == "gitlab" else ("lint", "test")
    forge.wait_runs(repo, sha, "pull_request", names=names)
    before = forge.head(repo)
    forge.merge_pr(repo, pr, title)
    forge.wait_runs(repo, moved(forge, repo, before), "push")
    answers = forge.file(repo, ".brigade/copier/answers.yml")
    assert f"_commit: {state['test_tag']}" in answers, answers
