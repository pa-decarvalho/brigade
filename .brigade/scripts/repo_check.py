"""<cli>:check: check the repository's settings that the selected tools need.

brigade-owned: updated by mise run brigade:update, do not edit.
Reads them with the forge's CLI (gh, glab or tea, with your login) and changes
nothing. Arguments: the CLI, then the checks besides the merge method
(releasaurus, renovate, automerge, pages). Fails when a required setting
is missing; a secret it cannot read (not an admin) is unknown, a recommended one
only advised.
"""

import json
import re
import subprocess
import sys

missing = 0


def report(ok: bool | None, what: str, fix: str, required: bool = True) -> None:
    """Print one setting: ok, missing (fails), advised, or unknown."""
    global missing
    if ok:
        print(f"ok       {what}")
    elif ok is None:
        print(f"unknown  {what}: {fix}")
    elif required:
        missing += 1
        print(f"missing  {what}: {fix}")
    else:
        print(f"advised  {what}: {fix}")


def api(cli: str, path: str) -> dict | list | None:
    """GET an API path with the CLI; None when it fails (missing or forbidden)."""
    command = [cli, "api", path]
    if cli == "tea":
        command.insert(2, "-i")  # tea exits 0 on errors: read the status
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode or (cli == "tea" and " 200 " not in result.stderr):
        return None
    return json.loads(result.stdout)


def names(*lists: dict | list | None) -> set[str] | None:
    """Secret or variable names from API lists; None when the first is unreadable."""
    if lists[0] is None:
        return None
    found = set()
    for items in lists:
        if isinstance(items, dict):  # GitHub: {"secrets": [...]}
            items = items["secrets"]
        for item in items or []:
            found.add(item.get("name") or item.get("key"))
    return found


def has(secrets: set[str] | None, name: str) -> bool | None:
    return None if secrets is None else name in secrets


def github(checks: set[str]) -> None:
    repo = api("gh", "repos/{owner}/{repo}")
    if not isinstance(repo, dict):
        sys.exit("gh:check: no GitHub repository here (gh auth login?)")
    url = f"{repo['html_url']}/settings"
    print(f"{repo['full_name']}, default branch {repo['default_branch']}")
    report(
        repo["allow_squash_merge"]
        and not repo["allow_merge_commit"]
        and not repo["allow_rebase_merge"]
        and repo["squash_merge_commit_title"] == "PR_TITLE",
        "squash merge only, with the pull request title",
        f"{url} > Pull Requests",
    )
    secrets = names(
        api("gh", "repos/{owner}/{repo}/actions/secrets"),
        api("gh", "repos/{owner}/{repo}/actions/organization-secrets"),
    )
    if "releasaurus" in checks:
        workflow = api("gh", "repos/{owner}/{repo}/actions/permissions/workflow")
        token = has(secrets, "RELEASAURUS_GITHUB_TOKEN")
        allowed = isinstance(workflow, dict) and workflow.get(
            "can_approve_pull_request_reviews"
        )
        report(
            True if token or allowed else token,
            "release PRs: RELEASAURUS_GITHUB_TOKEN secret, or Actions allowed to"
            " create pull requests",
            f"gh secret set RELEASAURUS_GITHUB_TOKEN, or {url}/actions >"
            " Workflow permissions",
        )
    if "renovate" in checks:
        report(
            has(secrets, "RENOVATE_TOKEN"),
            "RENOVATE_TOKEN secret",
            "gh secret set RENOVATE_TOKEN",
        )
    if "automerge" in checks:
        report(
            repo["allow_auto_merge"],
            "auto-merge allowed (renovate_automerge)",
            f"{url} > Pull Requests > Allow auto-merge",
        )
    if "pages" in checks:
        pages = api("gh", "repos/{owner}/{repo}/pages")
        report(
            isinstance(pages, dict) and pages["source"]["branch"] == "gh-pages",
            "Pages published from the gh-pages branch",
            f"{url}/pages > Deploy from a branch: gh-pages (after the first deploy)",
        )


def gitlab(checks: set[str]) -> None:
    project = api("glab", "projects/:id")
    if not isinstance(project, dict):
        sys.exit("glab:check: no GitLab project here (glab auth login?)")
    url = f"{project['web_url']}/-/settings"
    print(
        f"{project['path_with_namespace']}, default branch {project['default_branch']}"
    )
    report(
        project["squash_option"] == "always",
        "squash commits always (the merge request title is the commit)",
        f"{url}/merge_requests > Squash commits when merging: Require",
    )
    namespace = project["namespace"]
    group = (
        api("glab", f"groups/{namespace['id']}/variables")
        if namespace["kind"] == "group"
        else []
    )
    variables = names(api("glab", "projects/:id/variables"), group)
    if "releasaurus" in checks:
        report(
            has(variables, "RELEASAURUS_GITLAB_TOKEN"),
            "RELEASAURUS_GITLAB_TOKEN CI/CD variable",
            "glab variable set RELEASAURUS_GITLAB_TOKEN --masked",
        )
    if "renovate" in checks:
        report(
            has(variables, "RENOVATE_TOKEN"),
            "RENOVATE_TOKEN CI/CD variable",
            "glab variable set RENOVATE_TOKEN --masked",
        )
        report(
            has(variables, "RENOVATE_GITHUB_COM_TOKEN"),
            "RENOVATE_GITHUB_COM_TOKEN CI/CD variable (lookups, release notes)",
            "glab variable set RENOVATE_GITHUB_COM_TOKEN --masked",
            required=False,
        )
        schedules = api("glab", "projects/:id/pipeline_schedules")
        report(
            None if schedules is None else any(s["active"] for s in schedules),
            "an active pipeline schedule (Renovate runs on schedules)",
            f"{project['web_url']}/-/pipeline_schedules",
            required=False,
        )
    if "pages" in checks:
        report(
            project["pages_access_level"] != "disabled",
            "Pages enabled",
            f"{url} > Visibility > Pages",
        )


def gitea(checks: set[str]) -> None:
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", remote)
    repo = api("tea", f"repos/{match[1]}") if match else None
    if not isinstance(repo, dict):
        sys.exit("tea:check: no Gitea repository at origin (tea login add?)")
    path = f"repos/{repo['full_name']}"
    url = f"{repo['html_url']}/settings"
    print(f"{repo['full_name']}, default branch {repo['default_branch']}")
    report(
        repo["allow_squash_merge"]
        and not repo["allow_merge_commits"]
        and not repo["allow_rebase"]
        and not repo["allow_rebase_explicit"]
        and not repo["allow_fast_forward_only_merge"],
        "squash merge only",
        f"{url} > Pull Requests",
    )
    owner = repo["owner"]["login"]
    secrets = names(
        api("tea", f"{path}/actions/secrets"),
        api("tea", f"orgs/{owner}/actions/secrets"),
    )
    if "releasaurus" in checks:
        report(
            has(secrets, "RELEASAURUS_GITEA_TOKEN"),
            "RELEASAURUS_GITEA_TOKEN secret (else the CI token: release PRs start"
            " no checks, tags no deploy)",
            f"{url}/actions/secrets",
            required=False,
        )
    if "renovate" in checks:
        report(
            has(secrets, "RENOVATE_TOKEN"),
            "RENOVATE_TOKEN secret",
            f"{url}/actions/secrets",
        )
        report(
            has(secrets, "RENOVATE_GITHUB_COM_TOKEN"),
            "RENOVATE_GITHUB_COM_TOKEN secret (lookups, release notes)",
            f"{url}/actions/secrets",
            required=False,
        )


def main() -> int:
    cli, *checks = sys.argv[1:]
    {"gh": github, "glab": gitlab, "tea": gitea}[cli](set(checks))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
