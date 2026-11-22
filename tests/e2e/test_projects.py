"""One project of each type, from brigade's latest release to the checkout.

In a temporary folder: the project, brigade applied from this checkout at its
latest tag, then pushed to the forge. Its pull request, then brigade:update to
the checkout (HEAD) in a pull request whose CI passes, both merged; then the
release, the publish and the deploy, made by the checkout's files. A type whose
tools or answers the latest release lacks (the current branch adds them) starts
from the checkout instead, with no update to make; E2E_FROM_HEAD=1 does so for
every type (a changed tool, a quicker run). The checkout is the
projects' _src_path, mounted at the same path in the jobs (tests/fixtures/).
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest  # ty: ignore[import-not-found]  # run with uv run --with pytest
import up
from conftest import Note, sh
from forges import Forge, wait_for
from projects import CASES, PROJECTS

SEMVER = re.compile(r"\d+\.\d+\.\d+")
COPIER = ["uvx", "copier@9.19.1"]  # .copier/settings.yml's pin


def latest_tag() -> str:
    tags = sh("git", "tag", "-l", cwd=up.ROOT).split()
    semver = [t for t in tags if SEMVER.fullmatch(t)]
    return max(semver, key=lambda t: tuple(map(int, t.split("."))))


def template_at(tag: str) -> str:
    """brigade at a tag, cloned in up.TEMPLATES (mounted in the jobs).

    The project starts from it, so brigade:lint, which renders a local template
    at its HEAD, compares to that release until the update moves _src_path to
    the checkout.
    """
    clone = up.TEMPLATES / f"brigade-{tag}"
    if not clone.exists():
        sh(
            "git",
            "clone",
            "-q",
            "--no-local",
            "--branch",
            tag,
            str(up.ROOT),
            str(clone),
            cwd=up.ROOT,
        )
    return str(clone)


def questions(template: str) -> set[str]:
    """The names of a template's questions (.copier/questions/)."""
    found = set()
    for path in Path(template, ".copier/questions").rglob("*.yml"):
        found |= set(re.findall(r"^([a-z][a-z0-9_]*):", path.read_text(), re.MULTILINE))
    return found


def fetch(url: str) -> str:
    """A page's text, "" when absent."""
    try:
        with urllib.request.urlopen(url, timeout=30) as page:
            return page.read().decode()
    except urllib.error.URLError:
        return ""


def data_args(data: dict) -> list[str]:
    """Copier --data options: strings as is, the rest as JSON (YAML)."""
    values = {k: v if isinstance(v, str) else json.dumps(v) for k, v in data.items()}
    return [arg for k, v in values.items() for arg in ("--data", f"{k}={v}")]


@pytest.mark.parametrize(("kind", "workflow"), CASES.values(), ids=CASES.keys())
def test_project(kind: str, workflow: str, forge: Forge, note: Note, tmp_path) -> None:
    """pr: the release PR opens on the feat merge, the update merge updates it.
    direct: the update merges first, then the feat merge releases at once."""
    project = PROJECTS[kind]
    if forge.server in project.not_on:
        pytest.skip(f"brigade refuses {kind} on {forge.server}")
    registry = up.reset_registries(forge.server)
    path, repo = tmp_path / "demo", f"demo-{kind}-{int(time.time())}"
    path.mkdir()
    full = forge.name != "github"  # github on Gitea: GitHub's API is not there
    if project.cluster and full:
        registry["kubeconfig"] = up.reset_cluster(forge.server)
    env = {"MISE_YES": "1", "MISE_TRUSTED_CONFIG_PATHS": str(path)}
    # Config files of their own (tea and glab logins, no global mise config):
    # a new user's, and this machine's left untouched.
    env |= {"XDG_CONFIG_HOME": str(tmp_path / "config")}
    env |= {"GLAB_CONFIG_DIR": str(tmp_path / "config" / "glab-cli")}
    for who in ("AUTHOR", "COMMITTER"):
        env |= {f"GIT_{who}_NAME": "brigade", f"GIT_{who}_EMAIL": "brigade@example.com"}

    def run(*command: str) -> str:
        return sh(*command, cwd=path, env=env)

    with note.step("create"):
        tools = list(project.tools)
        tools += ["releasaurus"] if full else []
        start = latest_tag()
        template = template_at(start)
        # A tool or an answer the release lacks (the branch adds it): from the
        # checkout (HEAD, uncommitted changes included), with no update to make.
        offered = Path(template, ".copier/questions/common.yml").read_text()
        missing = [t for t in tools if f": {t}\n" not in offered]
        missing += sorted(set(project.data) - questions(template))
        why = f"{', '.join(missing)}: not in {latest_tag()}" if missing else ""
        if os.environ.get("E2E_FROM_HEAD"):  # every type, e.g. a changed tool
            why = why or "E2E_FROM_HEAD"
        if why:
            start, template = "HEAD", str(up.ROOT)
        # A release without this ci (forgejo before 0.33): ci: gitea, then the update
        # moves to it, as docs/ci.md says.
        known = (
            f"\n    - {forge.ci}\n"
            in Path(template, ".copier/questions/common.yml").read_text()
        )
        ci = forge.ci if known else "gitea"
        data = {**project.data, "ci": ci, "tools": tools}
        if workflow == "direct":
            data |= {"customize_tools": True, "releasaurus_workflow": "direct"}
        if not full:  # no publish without a release
            data = {k: v for k, v in data.items() if not k.endswith("_publish")}
        run("git", "init", "-q", "-b", "main")
        # A release refusing the forge's CLI (tea on Forgejo before 0.33.1): the
        # update adds it.
        cli_later = False
        try:
            with_cli = {**data, "tools": [*tools, forge.cli] if forge.cli else tools}
            run(
                *COPIER,
                "copy",
                "--trust",
                "--defaults",
                *(["--vcs-ref", "HEAD"] if start == "HEAD" else []),
                *data_args(with_cli),
                template,
                ".",
            )
        except AssertionError as error:
            if not forge.cli or "Invalid choice for 'tools'" not in str(error):
                raise
            cli_later = True
            run(
                *COPIER,
                "copy",
                "--trust",
                "--defaults",
                *(["--vcs-ref", "HEAD"] if start == "HEAD" else []),
                *data_args(data),
                template,
                ".",
            )
        for name, text in project.files.items():
            (path / name).parent.mkdir(parents=True, exist_ok=True)
            (path / name).write_text(text)
        lines = "".join(f'{k} = "{v}"\n' for k, v in project.env.items())
        (path / "mise.toml").write_text(f"[env]\n{lines}")
        run("mise", "install")
        for command in project.commands:
            run("mise", "exec", "--", *command)
        run("mise", "-C", ".brigade", "lock")
        run("git", "add", "-A")
        run("git", "commit", "-qm", "chore: init")

    with note.step("settings"):
        forge.create_repo(repo)
        run("git", "remote", "add", "origin", forge.remote(repo))
        if full:
            secrets = {forge.releasaurus_secret: "{token}", **project.secrets}
            if ci != forge.ci:  # the secret's name before the move
                secrets[f"RELEASAURUS_{ci.upper()}_TOKEN"] = "{token}"
            for name, value in secrets.items():
                value = value.format(user=forge.user, token=forge.token, **registry)
                forge.set_secret(repo, name, value)

        def cli_settings() -> None:
            run("mise", "exec", "--", *forge.login())
            run("mise", "run", f"{forge.cli}:setup")
            run("mise", "run", f"{forge.cli}:check")

        if forge.cli and not cli_later:
            cli_settings()
        run("git", "push", "-q", "-u", "origin", "main")
        if full:  # release, on pushes to main
            forge.wait_runs(repo, run("git", "rev-parse", "HEAD").strip(), "push")

    with note.step("pull request"):
        run("git", "switch", "-q", "-c", "hello")
        (path / "README.md").write_text((path / "README.md").read_text() + "\nHello.\n")
        run("git", "commit", "-qam", "feat: say hello")
        run("git", "push", "-q", "-u", "origin", "hello")
        pr = forge.open_pr(repo, "hello", "feat: say hello")
        sha = run("git", "rev-parse", "HEAD").strip()
        names = () if forge.server == "gitlab" else ("lint", "test")
        forge.wait_runs(repo, sha, "pull_request", names)

    def merge(number: str, title: str) -> None:
        before = forge.head(repo)
        forge.merge_pr(repo, number, title)
        merged = forge.moved(repo, before)
        if full:  # release, on pushes to main
            forge.wait_runs(repo, merged, "push")

    if start == "HEAD":  # already the checkout's files
        if workflow == "pr":
            merge(pr, "feat: say hello")
        note.skip("update", reason=f"started from HEAD ({why})")
    else:
        with note.step("update"):
            if workflow == "pr":
                merge(pr, "feat: say hello")
            run("git", "switch", "-q", "main")
            run("git", "pull", "-q", "origin", "main")
            run("git", "switch", "-q", "-c", "update")
            answers = path / ".brigade/copier/answers.yml"
            answers.write_text(answers.read_text().replace(template, str(up.ROOT)))
            run("git", "commit", "-qam", "ci: brigade from the checkout")
            data_file = path / ".brigade/copier/data.yml"
            text = data_file.read_text()
            if ci != forge.ci:
                assert f'ci: "{ci}"' in text, text
                text = text.replace(f'ci: "{ci}"', f'ci: "{forge.ci}"')
            if cli_later:
                text = text.replace("tools:\n", f'tools:\n  - "{forge.cli}"\n', 1)
            data_file.write_text(text)
            run(
                "mise", "run", "brigade:update", "--", "--defaults", "--vcs-ref", "HEAD"
            )
            if cli_later:
                cli_settings()
            if ci != forge.ci:  # Copier moved the workflows
                assert (path / f".{forge.ci}/workflows/lint.yml").exists()
                assert not (path / f".{ci}/workflows").exists()
            assert f"_commit: {latest_tag()}\n" not in answers.read_text(), (
                "HEAD is the tag"
            )
            run("git", "add", "-A")
            run("git", "commit", "-qm", "ci: update brigade")
            run("git", "push", "-q", "-u", "origin", "update")
            update = forge.open_pr(repo, "update", "ci: update brigade")
            sha = run("git", "rev-parse", "HEAD").strip()
            forge.wait_runs(repo, sha, "pull_request", names)
            merge(update, "ci: update brigade")

    if not full:
        note.skip(
            "release", "publish", "deploy", reason="not covered: they call GitHub's API"
        )
        return

    with note.step("release"):
        if workflow == "pr":
            release, title, sha = wait_for(
                "release PR", lambda: forge.find_pr(repo, "release"), 300
            )
            assert title.startswith("chore(main): release"), title
            forge.wait_runs(repo, sha, "pull_request", names)
            merge(release, title)
        else:  # released by the feat merge's release job
            merge(pr, "feat: say hello")
            assert not forge.find_pr(repo, "release"), "a release PR in direct"
        tags = wait_for(
            "X.Y.Z tag",
            lambda: [t for t in forge.tags(repo) if SEMVER.fullmatch(t)],
            600,
        )
        assert all(SEMVER.fullmatch(t) for t in forge.tags(repo)), forge.tags(repo)
        tag_sha = forge.tag_sha(repo, tags[0])

    with note.step("publish", go_on=True):
        tag = tags[0]
        names = (tag,) if forge.server == "gitlab" else ("publish",)
        forge.wait_runs(repo, tag_sha, "push", names)
        url, text = project.published
        page = wait_for("published release", lambda: fetch(url), 120)
        assert text.format(tag=tag) in page, page

    # GitLab: deploy is a job of the tag's pipeline, waited for above.
    if forge.server != "gitlab":
        with note.step("deploy", go_on=True):  # started by publish (deploy_auto)
            forge.wait_runs(repo, tag_sha, "workflow_dispatch", ("deploy",), 600)

    if project.cluster:
        environments = project.data["environments"]
        with note.step("cluster", go_on=True):
            # The automatic ones, installed once published; then the others,
            # deployed by hand on the tag; each running in its namespace.
            for env_ in environments:
                if not env_.get("auto"):
                    forge.deploy_by_hand(repo, tag, tag_sha, env_["name"])
                rollout = ("rollout", "status", "deployment/demo", "--timeout=180s")
                up.kubectl(forge.server, "--namespace", env_["name"], *rollout)

    assert not note.failed, f"failed steps: {note.failed}"
