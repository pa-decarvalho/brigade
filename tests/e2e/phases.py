"""brigade end to end on a local forge, in phases (as Molecule's scenarios).

Usage: phases.py <converge|destroy|test> <forge> [type...]; forge gitea,
forgejo, gitlab or github (a ci: github project on Gitea, the same server);
types: the ids of projects.CASES, all by default. As mise's e2e:<command> tasks
run it, as Molecule's:
- converge: the forge up if it is not (up.ensure, its URL and login printed),
    then for each type in turn (they share Nexus and the cluster) its phases:
    prepare (when not done: the registries and the target emptied, the project
    (brigade at its latest release, then tests/fixtures/projects/<type>/), its
    repository and secrets, pushed), converge (what CI does: a pull request,
    brigade:update to this checkout's HEAD in a pull request, the release, the
    publish, the deploys; resumes at the first step not done, a step's actions
    done once, its waits again), verify (what came out: the published release,
    the deploys on their target; every time);
- destroy: with types, their state and project (the next converge starts them
    over); without, the forge and its data too (up.down);
- test: the types' state cleared, converge, then destroy, even after a
    failure; test all [type...]: every forge in turn, then the big cleanup
    (up.clean) and the table forge x type, also written to .forges/summary.md.

A type starts from brigade's latest tag; from this checkout (HEAD, uncommitted
changes included) when that release lacks one of its tools or answers (the
branch adds them), or with E2E_FROM_HEAD=1 (every type), with no update step
then. The checkout is the projects' _src_path, mounted at the same path in the
jobs (tests/fixtures/): the release, the publish and the deploy run its files.

State: .forges/<forge>-<type>.json (what the next phase needs); note:
.forges/<forge>-<type>.md (each step's result and time, the failed jobs' last
log lines); the project in up.WORK/<forge>-<type>/.
"""

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

import up
from forges import FORGES, Forge, wait_for
from projects import CASES, PROJECTS

SEMVER = re.compile(r"\d+\.\d+\.\d+")
COPIER = ["uvx", "copier@9.19.1"]  # .copier/settings.yml's pin
FILES = up.FIXTURES / "projects"  # each type's files, without brigade


def sh(*command: str, cwd: Path, env: dict | None = None) -> str:
    """Run a command; fails with the end of its output."""
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
        check=False,
    )
    output = result.stdout + result.stderr
    assert not result.returncode, (
        f"{' '.join(command)} exited {result.returncode}:\n"
        + "\n".join(output.splitlines()[-40:])
    )
    return output


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


def duration(seconds: float) -> str:
    """1h02m, 5m12s or 40s."""
    minutes, secs = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


def data_args(data: dict) -> list[str]:
    """Copier --data options: strings as is, the rest as JSON (YAML)."""
    values = {k: v if isinstance(v, str) else json.dumps(v) for k, v in data.items()}
    return [arg for k, v in values.items() for arg in ("--data", f"{k}={v}")]


class Scenario:
    """One type on one forge: its phases, its state and its note."""

    def __init__(self, forge: Forge, case: str) -> None:
        self.forge, self.case = forge, case
        self.kind, self.workflow = CASES[case]
        self.project = PROJECTS[self.kind]
        self.title = f"{forge.name}-{case}"
        self.file = up.STATE / f"{self.title}.json"
        self.state: dict = (
            json.loads(self.file.read_text()) if self.file.exists() else {}
        )
        self.root = up.WORK / self.title
        self.path = self.root / "demo"
        self.full = forge.name != "github"  # github on Gitea: no GitHub API
        self.failed: list[str] = []  # this phase's failed steps
        env = {"MISE_YES": "1", "MISE_TRUSTED_CONFIG_PATHS": str(self.path)}
        # Config files of their own (tea and glab logins, no global mise
        # config): a new user's, and this machine's left untouched.
        env |= {"XDG_CONFIG_HOME": str(self.root / "config")}
        env |= {"GLAB_CONFIG_DIR": str(self.root / "config" / "glab-cli")}
        for who in ("AUTHOR", "COMMITTER"):
            env |= {
                f"GIT_{who}_NAME": "brigade",
                f"GIT_{who}_EMAIL": "brigade@example.com",
            }
        self.env = env

    # -- helpers ---------------------------------------------------------------

    def run(self, *command: str) -> str:
        return sh(*command, cwd=self.path, env=self.env)

    def save(self) -> None:
        up.STATE.mkdir(exist_ok=True)
        self.file.write_text(json.dumps(self.state, indent=2))
        self.write_note()

    def once(self, key: str, action):
        """action()'s result, kept: a rerun gets it without acting again."""
        done = self.state.setdefault("once", {})
        if key not in done:
            done[key] = action()
            self.save()
        return done[key]

    def todo(self, name: str) -> bool:
        """The step is not done yet (converge resumes at the first one)."""
        return name not in self.state.get("done", [])

    @contextlib.contextmanager
    def step(self, name: str, *, go_on: bool = False):
        """One step, timed; with go_on, its failure is noted and the next run."""
        start = time.time()
        steps = self.state.setdefault("steps", {})
        try:
            yield
        except Exception as error:  # noted, then raised or kept
            steps[name] = ["failed", time.time() - start, str(error)]
            self.failed.append(name)
            if not go_on:
                raise
        else:
            steps[name] = ["passed", time.time() - start, ""]
            self.done(name)
        finally:
            logs = self.state.setdefault("logs", [])
            logs += [log for log in self.forge.logs if log not in logs]
            self.forge.logs.clear()
            self.save()

    def skip(self, *names: str, reason: str) -> None:
        for name in names:
            self.state.setdefault("steps", {})[name] = ["skipped", 0.0, reason]
            self.done(name)
        self.save()

    def done(self, name: str) -> None:
        done = self.state.setdefault("done", [])
        done += [] if name in done else [name]

    def write_note(self) -> None:
        lines = [f"# {self.title} ({time.strftime('%Y-%m-%d %H:%M')})", ""]
        repo = self.state.get("repo", "")
        lines += [
            f"Forge: {self.forge.url}/{self.forge.user}/{repo}; project: {self.path}"
        ]
        steps = self.state.get("steps", {})
        total = sum(seconds for _, seconds, _ in steps.values())
        lines += [f"Time: {duration(total)} (the steps')"]
        lines += ["", "| Step | Result | Time | Detail |", "|---|---|---|---|"]
        for name, (outcome, seconds, message) in steps.items():
            detail = " ".join(message.split())[:300].replace("|", "\\|")
            lines.append(f"| {name} | {outcome} | {seconds:.0f}s | {detail} |")
        if self.state.get("logs"):
            lines += ["", "## Failed jobs", "", *self.state["logs"]]
        lines.append("")
        (up.STATE / f"{self.title}.md").write_text("\n".join(lines))

    def merge(self, number: str, title: str) -> None:
        """Merge a PR once; then wait for the release run on its commit."""
        repo = self.state["repo"]

        def act() -> str:
            before = self.forge.head(repo)
            self.forge.merge_pr(repo, number, title)
            return self.forge.moved(repo, before)

        merged = self.once(f"merged {number}", act)
        if self.full:  # release, on pushes to main
            self.forge.wait_runs(repo, merged, "push")

    def names(self) -> tuple[str, ...]:
        """The pull request runs to wait for (GitLab: one pipeline)."""
        return () if self.forge.server == "gitlab" else ("lint", "test")

    # -- phases ----------------------------------------------------------------

    def prepare(self) -> None:
        """Start over: the project, its repository, secrets and first push."""
        shutil.rmtree(self.root, ignore_errors=True)
        self.state = {}
        project, forge = self.project, self.forge
        if forge.server in project.not_on:
            self.state["skipped"] = f"brigade refuses {self.kind} on {forge.server}"
            self.skip("create", reason=self.state["skipped"])  # for the summary
            print(f"{self.title}: skipped ({self.state['skipped']})")
            return
        registry = up.reset_registries(forge.server)
        if project.target == "cluster" and self.full:
            registry["kubeconfig"] = up.reset_cluster(forge.server)
        if project.target == "ssh" and self.full:
            registry["ssh_private_key"] = up.reset_ssh_target(forge.server)
        repo = f"demo-{self.case}-{int(time.time())}"
        self.state["repo"] = repo
        self.path.mkdir(parents=True)

        with self.step("create"):
            tools = list(project.tools) + (["releasaurus"] if self.full else [])
            start = latest_tag()
            template = template_at(start)
            # A tool or an answer the release lacks (the branch adds it): from
            # the checkout (HEAD, uncommitted changes included), no update.
            offered = Path(template, ".copier/questions/common.yml").read_text()
            missing = [t for t in tools if f": {t}\n" not in offered]
            missing += sorted(set(project.data) - questions(template))
            why = f"{', '.join(missing)}: not in {start}" if missing else ""
            if os.environ.get("E2E_FROM_HEAD"):  # every type, e.g. a changed tool
                why = why or "E2E_FROM_HEAD"
            if why:
                start, template = "HEAD", str(up.ROOT)
            # A release without this ci (forgejo before 0.33): ci: gitea, then
            # the update moves to it, as docs/ci.md says.
            common = Path(template, ".copier/questions/common.yml").read_text()
            ci = forge.ci if f"\n    - {forge.ci}\n" in common else "gitea"
            data = {**project.data, "ci": ci, "tools": tools}
            if self.workflow == "direct":
                data |= {"customize_tools": True, "releasaurus_workflow": "direct"}
            if not self.full:  # no publish without a release
                data = {k: v for k, v in data.items() if not k.endswith("_publish")}
            self.run("git", "init", "-q", "-b", "main")
            copy = [*COPIER, "copy", "--trust", "--defaults"]
            copy += ["--vcs-ref", "HEAD"] if start == "HEAD" else []
            # A release refusing the forge's CLI (tea on Forgejo before
            # 0.33.1): the update adds it.
            cli_later = False
            try:
                cli = [forge.cli] if forge.cli else []
                with_cli = {**data, "tools": [*tools, *cli]}
                self.run(*copy, *data_args(with_cli), template, ".")
            except AssertionError as error:
                if not forge.cli or "Invalid choice for 'tools'" not in str(error):
                    raise
                cli_later = True
                self.run(*copy, *data_args(data), template, ".")
            shutil.copytree(FILES / self.kind, self.path, dirs_exist_ok=True)
            self.run("mise", "install")
            self.run("mise", "-C", ".brigade", "lock")
            self.run("git", "add", "-A")
            self.run("git", "commit", "-qm", "chore: init")
            self.state |= {"start": start, "template": template, "why": why}
            self.state |= {"ci": ci, "cli_later": cli_later}

        with self.step("settings"):
            forge.create_repo(repo)
            self.run("git", "remote", "add", "origin", forge.remote(repo))
            if self.full:
                secrets = {forge.releasaurus_secret: "{token}", **project.secrets}
                if ci != forge.ci:  # the secret's name before the move
                    secrets[f"RELEASAURUS_{ci.upper()}_TOKEN"] = "{token}"
                for name, value in secrets.items():
                    value = value.format(user=forge.user, token=forge.token, **registry)
                    forge.set_secret(repo, name, value)
            if forge.cli and not cli_later:
                self.cli_settings()
            self.run("git", "push", "-q", "-u", "origin", "main")
            if self.full:  # release, on pushes to main
                sha = self.run("git", "rev-parse", "HEAD").strip()
                forge.wait_runs(repo, sha, "push")
        print(f"{self.title}: {forge.url}/{forge.user}/{repo}, project {self.path}")

    def cli_settings(self) -> None:
        self.run("mise", "exec", "--", *self.forge.login())
        self.run("mise", "run", f"{self.forge.cli}:setup")
        self.run("mise", "run", f"{self.forge.cli}:check")

    def converge(self) -> None:
        """What CI does, from the pull request to the deploys; resumes."""
        state, forge = self.state, self.forge
        repo, start = state["repo"], state["start"]

        def hello() -> list[str]:
            self.run("git", "reset", "-q", "--hard")
            self.run("git", "switch", "-q", "-C", "hello", "main")
            readme = self.path / "README.md"
            readme.write_text(readme.read_text() + "\nHello.\n")
            self.run("git", "commit", "-qam", "feat: say hello")
            self.run("git", "push", "-q", "-f", "-u", "origin", "hello")
            pr = forge.open_pr(repo, "hello", "feat: say hello")
            return [pr, self.run("git", "rev-parse", "HEAD").strip()]

        if self.todo("pull request"):
            with self.step("pull request"):
                pr, sha = self.once("hello", hello)
                forge.wait_runs(repo, sha, "pull_request", self.names())
        pr = state["once"]["hello"][0]

        if start == "HEAD":  # already the checkout's files
            if self.workflow == "pr":
                self.merge(pr, "feat: say hello")
            if self.todo("update"):
                self.skip("update", reason=f"started from HEAD ({state['why']})")
        elif self.todo("update"):
            with self.step("update"):
                if self.workflow == "pr":
                    self.merge(pr, "feat: say hello")
                update, sha = self.once("update", self.update)
                forge.wait_runs(repo, sha, "pull_request", self.names())
                self.merge(update, "ci: update brigade")

        if not self.full:
            if self.todo("release"):
                reason = "not covered: they call GitHub's API"
                self.skip("release", "publish", "deploy", reason=reason)
            return

        if self.todo("release"):
            with self.step("release"):
                if self.workflow == "pr":
                    release, title, sha = self.once(
                        "release pr",
                        lambda: wait_for(
                            "release PR", lambda: forge.find_pr(repo, "release"), 300
                        ),
                    )
                    assert title.startswith("chore(main): release"), title
                    forge.wait_runs(repo, sha, "pull_request", self.names())
                    self.merge(release, title)
                else:  # released by the feat merge's release job
                    self.merge(pr, "feat: say hello")
                    assert not forge.find_pr(repo, "release"), "a release PR in direct"
                tags = wait_for(
                    "X.Y.Z tag",
                    lambda: [t for t in forge.tags(repo) if SEMVER.fullmatch(t)],
                    600,
                )
                assert all(SEMVER.fullmatch(t) for t in forge.tags(repo)), forge.tags(
                    repo
                )
                state["tag"], state["tag_sha"] = tags[0], forge.tag_sha(repo, tags[0])
        tag, tag_sha = state["tag"], state["tag_sha"]

        if self.todo("publish"):
            with self.step("publish", go_on=True):
                names = (tag,) if forge.server == "gitlab" else ("publish",)
                forge.wait_runs(repo, tag_sha, "push", names)

        # GitLab: deploy is a job of the tag's pipeline, waited for above.
        if forge.server != "gitlab" and self.todo("deploy"):
            with self.step("deploy", go_on=True):  # started by publish (deploy_auto)
                forge.wait_runs(repo, tag_sha, "workflow_dispatch", ("deploy",), 600)

        # The environments not deployed once published: by hand, on the tag.
        envs = self.project.data.get("environments", [])
        by_hand = [e["name"] for e in envs if not e.get("auto")]
        if by_hand and self.todo("deploy by hand"):
            with self.step("deploy by hand", go_on=True):
                for name in by_hand:
                    self.once(
                        f"deployed {name}",
                        lambda: forge.deploy_by_hand(repo, tag, tag_sha, name),  # noqa: B023  # called at once
                    )

    def update(self) -> list[str]:
        """brigade:update to the checkout's HEAD, in a pull request: (id, sha)."""
        state, forge, path = self.state, self.forge, self.path
        ci, template = state["ci"], state["template"]
        self.run("git", "reset", "-q", "--hard")
        self.run("git", "fetch", "-q", "origin")
        self.run("git", "switch", "-q", "-C", "update", "origin/main")
        answers = path / ".brigade/copier/answers.yml"
        answers.write_text(answers.read_text().replace(template, str(up.ROOT)))
        self.run("git", "commit", "-qam", "ci: brigade from the checkout")
        data_file = path / ".brigade/copier/data.yml"
        text = data_file.read_text()
        if ci != forge.ci:
            assert f'ci: "{ci}"' in text, text
            text = text.replace(f'ci: "{ci}"', f'ci: "{forge.ci}"')
        if state["cli_later"]:
            text = text.replace("tools:\n", f'tools:\n  - "{forge.cli}"\n', 1)
        data_file.write_text(text)
        self.run(
            "mise", "run", "brigade:update", "--", "--defaults", "--vcs-ref", "HEAD"
        )
        if state["cli_later"]:
            self.cli_settings()
        if ci != forge.ci:  # Copier moved the workflows
            assert (path / f".{forge.ci}/workflows/lint.yml").exists()
            assert not (path / f".{ci}/workflows").exists()
        assert f"_commit: {state['start']}\n" not in answers.read_text(), (
            "HEAD is the tag"
        )
        self.run("git", "add", "-A")
        self.run("git", "commit", "-qm", "ci: update brigade")
        self.run("git", "push", "-q", "-f", "-u", "origin", "update")
        number = forge.open_pr(state["repo"], "update", "ci: update brigade")
        return [number, self.run("git", "rev-parse", "HEAD").strip()]

    def verify(self) -> None:
        """What came out: the published release, the deploys on their target."""
        project, tag = self.project, self.state.get("tag")
        if not self.full:
            return
        assert tag, "no release yet: converge first"
        if project.published:  # else nothing to publish (ansible)
            with self.step("published", go_on=True):
                url, text = project.published
                page = wait_for("published release", lambda: fetch(url), 120)
                assert text.format(tag=tag) in page, page
        if project.target:
            with self.step(project.target, go_on=True):
                for env in project.data["environments"]:
                    self.check_target(env["name"], tag)

    def check_target(self, name: str, tag: str) -> None:
        """One environment's deploy: running in its namespace (cluster), or the
        playbook's file (ssh: environment, commit, vault secret)."""
        server = self.forge.server
        if self.project.target == "cluster":
            rollout = ("rollout", "status", "deployment/demo", "--timeout=180s")
            up.kubectl(server, "--namespace", name, *rollout)
            if self.project.image:  # the image publish pushed
                jsonpath = "{.spec.template.spec.containers[0].image}"
                get = ("get", "deployment/demo", "-o", f"jsonpath={jsonpath}")
                found = up.kubectl(server, "--namespace", name, *get)
                assert found == self.project.image.format(tag=tag), found
        else:
            found = up.ssh_target(server, "cat", f"/srv/{name}/version")
            expected = f"{name} {self.state['tag_sha']} from the vault\n"
            assert found == expected, found


def converge(forge: str, types: list[str]) -> int:
    """Each type in turn: prepared when not, converged, verified (a type stops
    at its first failing phase); 1 when one failed."""
    found = up.ensure(FORGES[forge].server)
    print(f"{found['url']}: {found['user']} / {up.PASSWORD}", flush=True)
    client = FORGES[forge](**found)
    code = 0
    for case in types or CASES:
        scenario = Scenario(client, case)
        prepared = not scenario.todo("settings")  # its push done
        for phase in ("converge", "verify") if prepared else PHASES:
            if "skipped" in scenario.state:
                break
            print(f"{scenario.title}: {phase}", flush=True)
            scenario.failed = []
            try:
                getattr(scenario, phase)()
            except Exception:  # noqa: BLE001  # the next type goes on
                traceback.print_exc()
                scenario.failed.append(phase)
            if scenario.failed:
                print(f"{scenario.title}: {phase} failed: {scenario.failed}")
                code = 1
                break
    return code


PHASES = ("prepare", "converge", "verify")


def destroy(forge: str, types: list[str]) -> None:
    """The types' state and projects (their notes stay); without types, every
    type of the forge's server, and the forge itself."""
    server = FORGES[forge].server
    forges = [f for f, kind in FORGES.items() if kind.server == server]
    titles = [f"{forge}-{t}" for t in types] or [f"{f}-*" for f in forges]
    for title in titles:
        for state in up.STATE.glob(f"{title}.json"):
            state.unlink()
        for project in up.WORK.glob(title):
            shutil.rmtree(project, ignore_errors=True)
    if not types:
        up.down(server)


def test(forge: str, types: list[str]) -> int:
    """The types started over, converged, then the forge destroyed, even after
    a failure."""
    destroy(forge, list(types or CASES))
    try:
        return converge(forge, types)
    finally:
        destroy(forge, [])


def summary(since: float) -> str:
    """The notes written since a time, as one table forge x type: passed, the
    first failed step, skipped, or error (no step: stopped before the first),
    with the type's time; then the run's time, since then. Written to
    .forges/summary.md (both replaced by the next run)."""
    results: dict[str, dict[str, str]] = {}
    for note in up.STATE.glob("*-*.md"):  # <forge>-<type>.md
        if note.stat().st_mtime < since:
            continue
        text = note.read_text()
        forge, kind = text.splitlines()[0][2:].split(" (")[0].split("-", 1)
        row = r"^\| ([a-z ]+) \| (passed|failed|skipped) \| (\d+)s \|"
        found = re.findall(row, text, re.MULTILINE)
        steps = [(name, result) for name, result, _ in found]
        failed = [name for name, result in steps if result == "failed"]
        result = (
            f"failed: {failed[0]}" if failed
            else "error" if not steps  # stopped before its first step
            else "skipped" if all(r == "skipped" for _, r in steps)
            else "passed"
        )  # fmt: skip
        if any(r != "skipped" for _, r in steps):
            result += f" ({duration(sum(int(t) for *_, t in found))})"
        results.setdefault(kind, {})[forge] = result
    lines = ["| Type | " + " | ".join(FORGES) + " |", "|---" * (len(FORGES) + 1) + "|"]
    for kind in (k for k in CASES if k in results):
        cells = (results[kind].get(f, "") for f in FORGES)
        lines.append(f"| {kind} | " + " | ".join(cells) + " |")
    lines += ["", f"Time: {duration(time.time() - since)}"]
    table = "\n".join(lines) + "\n"
    (up.STATE / "summary.md").write_text(table)
    return table


def test_all(types: list[str]) -> int:
    """Every forge in turn (github on Gitea's server, before it goes down),
    then the big cleanup and the summary, even after a failure."""
    results: dict[str, int] = {}
    start = time.time()
    try:
        for server in dict.fromkeys(kind.server for kind in FORGES.values()):
            up.ensure(server)
            try:
                for forge in (f for f, kind in FORGES.items() if kind.server == server):
                    destroy(forge, list(types or CASES))
                    results[forge] = converge(forge, types)
            finally:
                destroy(forge, [])
    finally:
        up.clean()
        print(summary(start))
        for forge, code in results.items():
            print(f"{forge}: {'passed' if code == 0 else 'failed'}")
    return max(results.values(), default=0)


def main(args: list[str]) -> int:
    commands = {"converge": converge, "test": test}
    if args[:2] == ["test", "all"]:
        return test_all(args[2:])
    if len(args) < 2 or args[0] not in (*commands, "destroy") or args[1] not in FORGES:
        sys.exit(
            f"usage: phases.py <converge|destroy|test> <{'|'.join(FORGES)}> [type...]\n"
            "       phases.py test all [type...]"
        )
    command, forge, types = args[0], args[1], args[2:]
    unknown = set(types) - set(CASES)
    if unknown:
        sys.exit(f"unknown types {sorted(unknown)}: {', '.join(CASES)}")
    if command == "destroy":
        destroy(forge, types)
        return 0
    return commands[command](forge, types)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
