"""The local forges' APIs: what the tests need, one client per API.

Gitea and Forgejo share Gitea's API (Forgejo differs in its Actions runs);
github is a ci: github project on Gitea; GitLab has its own. Calls go to the
forge as seen from this machine (localhost, up.py's URL).
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request


class Forge:
    name = ""  # gitea, github (on Gitea), forgejo, gitlab
    server = ""  # its compose file in tests/fixtures/, for up.py
    ci = ""  # the ci answer
    cli = ""  # the forge's CLI tool, "" when none fits
    releasaurus_secret = ""
    api_root = ""

    def __init__(self, url: str, user: str, token: str) -> None:
        self.url, self.user, self.token = url, user, token
        self.logs: list[str] = []  # failed jobs' log excerpts, for the note

    def headers(self) -> dict[str, str]:
        raise NotImplementedError

    def api(self, method: str, path: str, body: object = None) -> object:
        """JSON API call; fails with the response body on HTTP errors."""
        request = urllib.request.Request(
            f"{self.url}{self.api_root}{path}",
            data=None if body is None else json.dumps(body).encode(),
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

    def remote(self, repo: str) -> str:
        host = self.url.split("://")[1]
        return f"http://{self.user}:{self.token}@{host}/{self.user}/{repo}.git"

    # -- per API ---------------------------------------------------------------

    def create_repo(self, repo: str) -> None:
        raise NotImplementedError

    def set_secret(self, repo: str, name: str, value: str) -> None:
        raise NotImplementedError

    def login(self) -> list[str]:
        """The CLI's login command."""
        raise NotImplementedError

    def open_pr(self, repo: str, branch: str, title: str) -> str:
        raise NotImplementedError

    def find_pr(self, repo: str, match: str) -> tuple[str, str, str] | None:
        """An open PR whose title matches: (id, title, head sha)."""
        raise NotImplementedError

    def merge_pr(self, repo: str, pr: str, title: str) -> None:
        raise NotImplementedError

    def runs(self, repo: str, sha: str) -> list[dict]:
        """A commit's CI runs: name, event, status (running, success, or else)."""
        raise NotImplementedError

    def failed_log(self, repo: str, run: dict) -> str:
        raise NotImplementedError

    def tags(self, repo: str) -> list[str]:
        raise NotImplementedError

    def head(self, repo: str) -> str:
        """The default branch's last commit."""
        raise NotImplementedError

    def tag_sha(self, repo: str, tag: str) -> str:
        """The commit a tag points to."""
        raise NotImplementedError

    # -- shared ----------------------------------------------------------------

    def wait_runs(
        self, repo: str, sha: str, event: str, names=(), timeout: int = 1200
    ) -> None:
        """Wait for a commit's runs of an event (the named ones started) to end.

        Fails with the failed jobs' last log lines, also kept for the note.
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

    def moved(self, repo: str, before: str) -> str:
        """The default branch's new commit after a merge (forges update it async)."""
        return wait_for(
            "merge commit", lambda: self.head(repo) != before and self.head(repo), 120
        )


class Gitea(Forge):
    name = server = ci = "gitea"
    cli = "tea"
    releasaurus_secret = "RELEASAURUS_GITEA_TOKEN"
    api_root = "/api/v1"

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"token {self.token}"}

    def create_repo(self, repo: str) -> None:
        self.api("POST", "/user/repos", {"name": repo, "private": False})

    def set_secret(self, repo: str, name: str, value: str) -> None:
        self.api(
            "PUT", f"/repos/{self.user}/{repo}/actions/secrets/{name}", {"data": value}
        )

    def login(self) -> list[str]:
        return [
            "tea",
            "login",
            "add",
            "--name",
            "local",
            "--url",
            self.url,
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
            if re.search(match, pr["title"]):
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
                # Gitea: path (file@ref); Forgejo: workflow_id.
                "name": (r.get("path") or r["workflow_id"])
                .split("@")[0]
                .rsplit("/")[-1],
                # Forgejo leaves a dispatched run's event empty.
                "event": r["event"] or "workflow_dispatch",
                "status": run_state(r),
            }
            for r in found.get("workflow_runs") or []
        ]

    def failed_log(self, repo: str, run: dict) -> str:
        base = f"/repos/{self.user}/{repo}/actions"
        try:
            jobs = self.api("GET", f"{base}/runs/{run['id']}/jobs")
            if isinstance(jobs, dict):  # Gitea; Forgejo: a list
                jobs = jobs["jobs"]
            assert isinstance(jobs, list)
            parts = []
            for job in jobs:
                if run_state(job) != "success":
                    log = self.api("GET", f"{base}/jobs/{job['id']}/logs")
                    parts.append(f"{job['name']}:\n{excerpt(str(log), "exitcode '")}")
            return "\n".join(parts) or "no failed job"
        except AssertionError as error:
            return f"logs unavailable: {error}"

    def tags(self, repo: str) -> list[str]:
        found = self.api("GET", f"/repos/{self.user}/{repo}/tags")
        assert isinstance(found, list)
        return [t["name"] for t in found]

    def tag_sha(self, repo: str, tag: str) -> str:
        found = self.api("GET", f"/repos/{self.user}/{repo}/tags/{tag}")
        assert isinstance(found, dict)
        return found["commit"]["sha"]

    def head(self, repo: str) -> str:
        branch = self.api("GET", f"/repos/{self.user}/{repo}/branches/main")
        assert isinstance(branch, dict)
        return branch["commit"]["id"]


class GitHubOnGitea(Gitea):
    """A ci: github project on Gitea: its workflows, not GitHub's API."""

    name = ci = "github"
    cli = ""  # gh calls GitHub's API


class Forgejo(Gitea):
    name = server = ci = "forgejo"
    releasaurus_secret = "RELEASAURUS_FORGEJO_TOKEN"


class GitLab(Forge):
    name = server = ci = "gitlab"
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
        host = self.url.split("://")[1]
        return [
            "glab", "auth", "login", "--hostname", host, "--token", self.token,
            "--api-protocol", "http", "--git-protocol", "http",
        ]  # fmt: skip

    def open_pr(self, repo: str, branch: str, title: str) -> str:
        body = {"source_branch": branch, "target_branch": "main", "title": title}
        path = f"/projects/{self.project(repo)}/merge_requests"
        for _ in range(10):  # GitLab registers a pushed branch asynchronously
            try:
                mr = self.api("POST", path, body)
                break
            except AssertionError as error:
                if "does not exist" not in str(error):
                    raise
                time.sleep(3)
        else:
            raise AssertionError(f"branch {branch} not found after its push")
        assert isinstance(mr, dict)
        return str(mr["iid"])

    def find_pr(self, repo: str, match: str) -> tuple[str, str, str] | None:
        mrs = self.api(
            "GET", f"/projects/{self.project(repo)}/merge_requests?state=opened"
        )
        assert isinstance(mrs, list)
        for mr in mrs:
            if re.search(match, mr["title"]):
                return str(mr["iid"]), mr["title"], mr["sha"]
        return None

    def merge_pr(self, repo: str, pr: str, title: str) -> None:
        path = f"/projects/{self.project(repo)}/merge_requests/{pr}/merge"
        self.api("PUT", path, {"squash": True, "squash_commit_message": title})

    def runs(self, repo: str, sha: str) -> list[dict]:
        found = self.api("GET", f"/projects/{self.project(repo)}/pipelines?sha={sha}")
        assert isinstance(found, list)
        events = {"merge_request_event": "pull_request"}  # as Gitea's events
        ok = {"success", "skipped", "manual"}
        running = {"created", "waiting_for_resource", "preparing", "pending", "running"}
        return [
            {
                "id": p["id"],
                "name": f"pipeline {p['id']} ({p['ref']})",
                "event": events.get(p["source"], p["source"]),
                "status": "running" if p["status"] in running
                else "success" if p["status"] in ok else p["status"],
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
        return "\n".join(parts) or "no failed job"

    def tags(self, repo: str) -> list[str]:
        found = self.api("GET", f"/projects/{self.project(repo)}/repository/tags")
        assert isinstance(found, list)
        return [t["name"] for t in found]

    def tag_sha(self, repo: str, tag: str) -> str:
        path = f"/projects/{self.project(repo)}/repository/tags/{tag}"
        found = self.api("GET", path)
        assert isinstance(found, dict)
        return found["commit"]["id"]

    def head(self, repo: str) -> str:
        branch = self.api(
            "GET", f"/projects/{self.project(repo)}/repository/branches/main"
        )
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


def wait_for(what: str, check, timeout: int = 900):
    """check()'s first truthy result, polled every 10 seconds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = check()
        if found:
            return found
        time.sleep(10)
    raise AssertionError(f"no {what} after {timeout}s")
