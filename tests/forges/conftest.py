"""Local forges: a client per forge, the shared state, and the note.

The tests run in the workstation container (compose.yml), on the forges'
network: FORGE and FORGE_TOKEN come from run.py. Each test is one step of the
scenario; a failed step skips the next ones. The note, /notes/<date>-<forge>.md
(.forges/ in the repository), lists each step's result, the failed jobs' last
log lines, and what the scenario had to do by hand.
"""

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest  # ty: ignore[import-not-found]  # run with uv run --with pytest (run.py)

RUN = time.strftime("%m%d%H%M%S")
WORK = Path("/work")


class Forge:
    """What the scenario needs from a forge; one subclass per API."""

    name = ""  # forge under test: gitea, github (on Gitea), forgejo, gitlab
    host = ""  # service name and port on the network
    user = ""  # the seeded admin
    ci = ""  # the ci answer
    cli = ""  # the forge's CLI tool, "" when none fits
    releasaurus_secret = ""

    def __init__(self, token: str) -> None:
        self.token = token
        self.notes: list[str] = []  # manual steps and workarounds
        self.logs: list[str] = []  # failed jobs' log excerpts
        self.links: dict[str, str] = {}  # step -> link

    # -- HTTP ------------------------------------------------------------

    def headers(self) -> dict[str, str]:
        raise NotImplementedError

    def api(self, method: str, path: str, body: object = None) -> object:
        """JSON API call; raises with the response body on HTTP errors."""
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"http://{self.host}{self.api_root}{path}",
            data=data,
            method=method,
            headers={**self.headers(), "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                text = response.read().decode()
        except urllib.error.HTTPError as error:
            raise AssertionError(
                f"{method} {path}: {error.code} {error.read().decode()[:500]}"
            ) from None
        return json.loads(text) if text.strip().startswith(("{", "[")) else text

    api_root = ""

    def remote(self, repo: str) -> str:
        return f"http://{self.user}:{self.token}@{self.host}/{self.user}/{repo}.git"

    def src_path(self, repo: str) -> str:
        """brigade's mirror, as Copier and the CI jobs reach it."""
        return f"http://{self.host}/{self.user}/{repo}.git"

    # -- per forge -----------------------------------------------------------

    def create_repo(self, repo: str) -> None:
        raise NotImplementedError

    def set_secret(self, repo: str, name: str, value: str) -> None:
        raise NotImplementedError

    def disable_ci(self, repo: str) -> None:
        """No CI on the repository (brigade's mirror: its own workflows)."""

    def login(self) -> list[str]:
        """The CLI's login command."""
        raise NotImplementedError

    def open_pr(self, repo: str, branch: str, title: str) -> str:
        raise NotImplementedError

    def find_pr(self, repo: str, match: str) -> tuple[str, str, str] | None:
        """An open PR whose title or branch matches: (id, title, head sha)."""
        raise NotImplementedError

    def merge_pr(self, repo: str, pr: str, title: str) -> None:
        raise NotImplementedError

    def runs(self, repo: str, sha: str) -> list[dict]:
        """CI runs of a commit: name, event, status (running/success/failure)."""
        raise NotImplementedError

    def failed_log(self, repo: str, run: dict) -> str:
        raise NotImplementedError

    def run_operate(self, repo: str) -> None:
        raise NotImplementedError

    def tags(self, repo: str) -> list[str]:
        raise NotImplementedError

    def file(self, repo: str, path: str) -> str:
        raise NotImplementedError

    def head(self, repo: str) -> str:
        """The default branch's last commit."""
        raise NotImplementedError

    # -- shared ------------------------------------------------------------

    PYPI = "http://pypi:8080"  # compose.yml's index, for every forge

    def packages(self, name: str) -> str:
        """The index's page of a package ("" when absent)."""
        try:
            with urllib.request.urlopen(
                f"{self.PYPI}/simple/{name}/", timeout=30
            ) as page:
                return page.read().decode()
        except urllib.error.HTTPError:
            return ""

    def wait_runs(
        self, repo: str, sha: str, event: str, timeout: int = 1200, names=()
    ) -> list[dict]:
        """Wait for the commit's runs of an event (and the named ones) to end.

        Fails with the failed jobs' logs; returns the runs.
        """
        deadline = time.time() + timeout
        runs: list[dict] = []
        while time.time() < deadline:
            runs = [r for r in self.runs(repo, sha) if r["event"] == event]
            started = all(any(n in r["name"].lower() for r in runs) for n in names)
            if runs and started and all(r["status"] != "running" for r in runs):
                break
            time.sleep(10)
        else:
            raise AssertionError(
                f"{event} runs of {sha[:8]} not done after {timeout}s: "
                f"{[(r['name'], r['status']) for r in runs]}"
            )
        failed = [r for r in runs if r["status"] != "success"]
        for run in failed:
            log = self.failed_log(repo, run)
            self.logs.append(
                f"### {run['name']} ({event}, {sha[:8]})\n\n```\n{log}\n```"
            )
        assert not failed, f"failed: {[(r['name'], r['status']) for r in failed]}"
        return runs

    def wait_for(self, what: str, check, timeout: int = 900):
        deadline = time.time() + timeout
        while time.time() < deadline:
            found = check()
            if found:
                return found
            time.sleep(10)
        raise AssertionError(f"no {what} after {timeout}s")


class Gitea(Forge):
    """Gitea and Forgejo: GitHub-like API, Actions."""

    name = "gitea"
    host = "gitea:3000"
    user = "brigade"
    ci = "gitea"
    cli = "tea"
    releasaurus_secret = "RELEASAURUS_GITEA_TOKEN"
    api_root = "/api/v1"

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"token {self.token}"}

    def create_repo(self, repo: str) -> None:
        self.api("POST", "/user/repos", {"name": repo, "private": False})

    def disable_ci(self, repo: str) -> None:
        self.api("PATCH", f"/repos/{self.user}/{repo}", {"has_actions": False})

    def set_secret(self, repo: str, name: str, value: str) -> None:
        path = f"/repos/{self.user}/{repo}/actions/secrets/{name}"
        self.api("PUT", path, {"data": value})

    def login(self) -> list[str]:
        url = f"http://{self.host}"
        return [
            "tea",
            "login",
            "add",
            "--name",
            "local",
            "--url",
            url,
            "--token",
            self.token,
        ]

    def open_pr(self, repo: str, branch: str, title: str) -> str:
        body = {"head": branch, "base": "main", "title": title}
        pr = self.api("POST", f"/repos/{self.user}/{repo}/pulls", body)
        assert isinstance(pr, dict)
        return str(pr["number"])

    def find_pr(self, repo: str, match: str) -> tuple[str, str, str] | None:
        prs = self.api("GET", f"/repos/{self.user}/{repo}/pulls?state=open")
        assert isinstance(prs, list)
        for pr in prs:
            if re.search(match, pr["title"]) or re.search(match, pr["head"]["ref"]):
                return str(pr["number"]), pr["title"], pr["head"]["sha"]
        return None

    def merge_pr(self, repo: str, pr: str, title: str) -> None:
        body = {"Do": "squash", "merge_title_field": title}
        self.api("POST", f"/repos/{self.user}/{repo}/pulls/{pr}/merge", body)

    def runs(self, repo: str, sha: str) -> list[dict]:
        found = self.api(
            "GET", f"/repos/{self.user}/{repo}/actions/runs?head_sha={sha}"
        )
        assert isinstance(found, dict)
        return [
            {
                "id": r["id"],
                # Gitea: path (file@ref) and GitHub's status/conclusion;
                # Forgejo: workflow_id and the result as status.
                "name": (r.get("path") or r["workflow_id"])
                .split("@")[0]
                .rsplit("/")[-1],
                "event": r["event"],
                "status": run_state(r),
                "url": r["html_url"],
            }
            for r in found.get("workflow_runs") or []
        ]

    def failed_log(self, repo: str, run: dict) -> str:
        base = f"/repos/{self.user}/{repo}/actions/runs/{run['id']}/jobs"
        try:
            jobs = self.api("GET", base)
            if isinstance(jobs, dict):  # Gitea; Forgejo: a list
                jobs = jobs["jobs"]
            assert isinstance(jobs, list)
            parts = []
            for job in jobs:
                if run_state(job) != "success":
                    log = self.api(
                        "GET",
                        f"/repos/{self.user}/{repo}/actions/jobs/{job['id']}/logs",
                    )
                    parts.append(f"{job['name']}:\n{excerpt(str(log), "exitcode '")}")
            return "\n".join(parts) or f"no failed job ({run['url']})"
        except AssertionError as error:
            return f"logs unavailable ({run['url']}): {error}"

    def run_operate(self, repo: str) -> None:
        path = f"/repos/{self.user}/{repo}/actions/workflows/operate.yml/dispatches"
        self.api("POST", path, {"ref": "main"})

    def tags(self, repo: str) -> list[str]:
        found = self.api("GET", f"/repos/{self.user}/{repo}/tags")
        assert isinstance(found, list)
        return [t["name"] for t in found]

    def file(self, repo: str, path: str) -> str:
        return str(self.api("GET", f"/repos/{self.user}/{repo}/raw/{path}?ref=main"))

    def head(self, repo: str) -> str:
        branch = self.api("GET", f"/repos/{self.user}/{repo}/branches/main")
        assert isinstance(branch, dict)
        return branch["commit"]["id"]


class GitHubOnGitea(Gitea):
    """A ci: github project on Gitea: its workflows, not GitHub's API."""

    name = "github"
    ci = "github"
    cli = ""


class Forgejo(Gitea):
    name = "forgejo"
    host = "forgejo:3000"
    cli = ""  # tea fails to install in Forgejo's CI (test_2_project)


class GitLab(Forge):
    name = "gitlab"
    host = "gitlab"
    user = "root"
    ci = "gitlab"
    cli = "glab"
    releasaurus_secret = "RELEASAURUS_GITLAB_TOKEN"
    api_root = "/api/v4"

    def headers(self) -> dict[str, str]:
        return {"PRIVATE-TOKEN": self.token}

    def project(self, repo: str) -> str:
        return urllib.parse.quote(f"{self.user}/{repo}", safe="")

    def create_repo(self, repo: str) -> None:
        self.api("POST", "/projects", {"name": repo, "visibility": "public"})

    def set_secret(self, repo: str, name: str, value: str) -> None:
        # GitLab masks values of 8 characters or more only.
        body = {"key": name, "value": value, "masked": len(value) >= 8}
        self.api("POST", f"/projects/{self.project(repo)}/variables", body)

    def login(self) -> list[str]:
        return [
            "glab", "auth", "login", "--hostname", self.host, "--token", self.token,
            "--api-protocol", "http", "--git-protocol", "http",
        ]  # fmt: skip

    def open_pr(self, repo: str, branch: str, title: str) -> str:
        body = {"source_branch": branch, "target_branch": "main", "title": title}
        mr = self.api("POST", f"/projects/{self.project(repo)}/merge_requests", body)
        assert isinstance(mr, dict)
        return str(mr["iid"])

    def find_pr(self, repo: str, match: str) -> tuple[str, str, str] | None:
        path = f"/projects/{self.project(repo)}/merge_requests?state=opened"
        mrs = self.api("GET", path)
        assert isinstance(mrs, list)
        for mr in mrs:
            if re.search(match, mr["title"]) or re.search(match, mr["source_branch"]):
                return str(mr["iid"]), mr["title"], mr["sha"]
        return None

    def merge_pr(self, repo: str, pr: str, title: str) -> None:
        path = f"/projects/{self.project(repo)}/merge_requests/{pr}/merge"
        self.api("PUT", path, {"squash": True, "squash_commit_message": title})

    def runs(self, repo: str, sha: str) -> list[dict]:
        found = self.api("GET", f"/projects/{self.project(repo)}/pipelines?sha={sha}")
        assert isinstance(found, list)
        # GitLab's pipeline sources, as Gitea's events.
        events = {"merge_request_event": "pull_request"}
        done = {"success", "failed", "canceled", "skipped", "manual"}
        return [
            {
                "id": p["id"],
                "name": f"pipeline {p['id']} ({p['ref']})",
                "event": events.get(p["source"], p["source"]),
                "status": "running" if p["status"] not in done
                else ("success" if p["status"] in ("success", "skipped", "manual") else p["status"]),
                "url": p["web_url"],
            }
            for p in found
        ]  # fmt: skip

    def failed_log(self, repo: str, run: dict) -> str:
        base = f"/projects/{self.project(repo)}"
        jobs = self.api("GET", f"{base}/pipelines/{run['id']}/jobs")
        assert isinstance(jobs, list)
        parts = []
        for job in jobs:
            if job["status"] == "failed":
                log = self.api("GET", f"{base}/jobs/{job['id']}/trace")
                parts.append(
                    f"{job['name']}:\n{excerpt(str(log), 'ERROR: Job failed')}"
                )
        return "\n".join(parts) or f"no failed job ({run['url']})"

    def run_operate(self, repo: str) -> None:
        # brigade's operate job runs on scheduled pipelines.
        base = f"/projects/{self.project(repo)}/pipeline_schedules"
        body = {"description": "operate", "ref": "main", "cron": "0 5 * * 1"}
        schedule = self.api("POST", base, body)
        assert isinstance(schedule, dict)
        self.api("POST", f"{base}/{schedule['id']}/play")

    def tags(self, repo: str) -> list[str]:
        found = self.api("GET", f"/projects/{self.project(repo)}/repository/tags")
        assert isinstance(found, list)
        return [t["name"] for t in found]

    def file(self, repo: str, path: str) -> str:
        quoted = urllib.parse.quote(path, safe="")
        return str(
            self.api(
                "GET",
                f"/projects/{self.project(repo)}/repository/files/{quoted}/raw?ref=main",
            )
        )

    def head(self, repo: str) -> str:
        path = f"/projects/{self.project(repo)}/repository/branches/main"
        branch = self.api("GET", path)
        assert isinstance(branch, dict)
        return branch["commit"]["id"]


FORGES = {f.name: f for f in (Gitea, GitHubOnGitea, Forgejo, GitLab)}


def run_state(run: dict) -> str:
    """A Gitea or Forgejo run or job: running, success, or how it failed."""
    status = run["status"]
    if status == "completed":
        status = run["conclusion"]
    if status in ("success", "skipped"):
        return "success"
    running = ("queued", "in_progress", "running", "waiting", "blocked", "unknown")
    return "running" if status in running else status


def excerpt(log: str, marker: str, size: int = 30) -> str:
    """The lines before the first failure marker (the job's cleanup comes after)."""
    lines = log.splitlines()
    end = next((i for i, line in enumerate(lines) if marker in line), len(lines))
    return "\n".join(lines[max(0, end - size) : end + 1])


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--forge", choices=sorted(FORGES), required=True)


@pytest.fixture(scope="session")
def forge(request: pytest.FixtureRequest) -> Forge:
    return request.config.stash[FORGE_KEY]


@pytest.fixture(scope="session")
def state() -> dict:
    """What the steps hand over: repository names, versions, SHAs."""
    return {"run": RUN}


def sh(*command: str, cwd: Path | str = WORK, env: dict | None = None) -> str:
    """Run a command; fails with its output's end."""
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


# -- one forge per session, a failed step skips the next ones -------------

FORGE_KEY = pytest.StashKey[Forge]()
STEPS: list[tuple[str, str, float, str]] = []  # name, outcome, seconds, message
_failed: list[str] = []


def pytest_configure(config: pytest.Config) -> None:
    name = config.getoption("--forge")
    config.stash[FORGE_KEY] = FORGES[name](os.environ["FORGE_TOKEN"])


def pytest_runtest_setup(item: pytest.Item) -> None:
    if _failed:
        pytest.skip(f"after the failed step {_failed[0]}")


# Steps the next ones do not depend on: their failure skips nothing.
LEAVES = {"test_6_deploy"}


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    step = report.nodeid.split("::")[-1]
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        message = ""
        if report.failed:
            if step not in LEAVES:
                _failed.append(step)
            message = str(report.longrepr.reprcrash.message)  # type: ignore[union-attr]
        elif report.skipped and isinstance(report.longrepr, tuple):
            message = report.longrepr[2]
        STEPS.append((step, report.outcome, report.duration, message))


def pytest_sessionfinish(session: pytest.Session) -> None:
    forge = session.config.stash[FORGE_KEY]
    lines = [
        f"# {forge.name}: brigade end to end ({time.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"Forge: http://{forge.host} (from the host: see compose.yml's ports).",
        "",
        "| Step | Result | Time | Detail |",
        "|---|---|---|---|",
    ]
    for step, outcome, seconds, message in STEPS:
        detail = " ".join(message.split())[:300].replace("|", "\\|")
        link = forge.links.get(step, "")
        lines.append(f"| {step} | {outcome} | {seconds:.0f}s | {detail} {link} |")
    if forge.logs:
        lines += ["", "## Failed jobs", "", *forge.logs]
    if forge.notes:
        lines += ["", "## Done by hand or worked around", ""]
        lines += [f"- {note}" for note in forge.notes]
    lines += ["", "## To improve", "", "-", ""]
    Path("/notes").mkdir(exist_ok=True)
    note = Path("/notes") / f"{time.strftime('%Y%m%d-%H%M')}-{forge.name}.md"
    note.write_text("\n".join(lines))
    print(f"\nnote: .forges/{note.name}")
