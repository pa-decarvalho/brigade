"""One project of each type, from brigade's latest release to the checkout.

In a temporary folder: the project, brigade applied from this checkout at its
latest tag, then pushed to the forge. Its pull request, its release and deploy,
then brigade:update to the checkout (HEAD) in a pull request whose CI passes.
The checkout is the projects' _src_path, mounted at the same path in the jobs
(tests/fixtures/).
"""

import json
import re
import time
import urllib.error
import urllib.request

import pytest  # ty: ignore[import-not-found]  # run with uv run --with pytest
import up
from conftest import Note, sh
from forges import Forge, wait_for
from projects import PROJECTS

SEMVER = re.compile(r"\d+\.\d+\.\d+")
COPIER = ["uvx", "copier@9.19.1"]  # .copier/settings.yml's pin


def latest_tag() -> str:
    tags = sh("git", "tag", "-l", cwd=up.ROOT).split()
    semver = [t for t in tags if SEMVER.fullmatch(t)]
    return max(semver, key=lambda t: tuple(map(int, t.split("."))))


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


@pytest.mark.parametrize("kind", PROJECTS)
def test_project(kind: str, forge: Forge, note: Note, tmp_path) -> None:
    project = PROJECTS[kind]
    if forge.server in project.not_on:
        pytest.skip(f"brigade refuses {kind} on {forge.server}")
    up.reset_registries(forge.server)  # each run publishes demo's 0.1.0 again
    path, repo = tmp_path / "demo", f"demo-{kind}-{int(time.time())}"
    path.mkdir()
    full = forge.name != "github"  # github on Gitea: GitHub's API is not there
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
        tools += [forge.cli] if forge.cli else []
        data = {**project.data, "ci": forge.ci, "tools": tools}
        if not full:  # no deploy without a release
            data = {k: v for k, v in data.items() if not k.endswith("_publish")}
        run("git", "init", "-q", "-b", "main")
        run(*COPIER, "copy", "--trust", "--defaults", "--vcs-ref", latest_tag(),
            *data_args(data), str(up.ROOT), ".")  # fmt: skip
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
            for name, value in secrets.items():
                value = value.format(user=forge.user, token=forge.token)
                forge.set_secret(repo, name, value)
        if forge.cli:
            run("mise", "exec", "--", *forge.login())
            run("mise", "run", f"{forge.cli}:setup")
            run("mise", "run", f"{forge.cli}:check")
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

    if full:
        with note.step("release"):
            before = forge.head(repo)
            forge.merge_pr(repo, pr, "feat: say hello")
            forge.wait_runs(repo, forge.moved(repo, before), "push")
            release, title, sha = wait_for(
                "release PR", lambda: forge.find_pr(repo, "release"), 300
            )
            assert title.startswith("chore(main): release"), title
            forge.wait_runs(repo, sha, "pull_request", names)
            before = forge.head(repo)
            forge.merge_pr(repo, release, title)
            tag_sha = forge.moved(repo, before)
            tags = wait_for(
                "X.Y.Z tag",
                lambda: [t for t in forge.tags(repo) if SEMVER.fullmatch(t)],
                600,
            )
            assert all(SEMVER.fullmatch(t) for t in forge.tags(repo)), forge.tags(repo)

        with note.step("deploy", go_on=True):
            tag = tags[0]
            forge.wait_runs(
                repo,
                tag_sha,
                "push",
                (tag,) if forge.server == "gitlab" else ("deploy",),
            )
            url, text = project.deployed
            page = wait_for("deployed release", lambda: fetch(url), 120)
            assert text.format(tag=tag) in page, page

    else:
        note.skip("release", "deploy", reason="not covered: they call GitHub's API")

    with note.step("update"):
        run("git", "switch", "-q", "main")
        run("git", "pull", "-q", "origin", "main")
        run("git", "switch", "-q", "-c", "update")
        run("mise", "run", "brigade:update", "--", "--defaults", "--vcs-ref", "HEAD")
        answers = (path / ".brigade/copier/answers.yml").read_text()
        assert f"_commit: {latest_tag()}\n" not in answers, "HEAD is the latest tag"
        run("git", "add", "-A")
        run("git", "commit", "-qm", "ci: update brigade")
        run("git", "push", "-q", "-u", "origin", "update")
        forge.open_pr(repo, "update", "ci: update brigade")
        forge.wait_runs(
            repo, run("git", "rev-parse", "HEAD").strip(), "pull_request", names
        )

    assert not note.failed, f"failed steps: {note.failed}"
