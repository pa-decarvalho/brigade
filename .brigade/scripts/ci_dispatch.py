"""Start a workflow on this CI run's ref (workflow_dispatch), with the job token.

brigade-owned: updated by mise run brigade:update, do not edit.
Usage: ci_dispatch.py WORKFLOW [NAME=VALUE...] (a file of the forge's workflow folder:
deploy.yml; its inputs)
Run in CI (GitHub, Gitea, Forgejo): the API is GITHUB_API_URL (Gitea and Forgejo's
/api/v1 too), the repository GITHUB_REPOSITORY, the ref GITHUB_REF (a tag:
refs/tags/X.Y.Z, the full ref Gitea and Forgejo need), the token TOKEN. A run
started this way does start, even with the workflow token.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) < 2 or not all("=" in a for a in sys.argv[2:]):
        print(__doc__, file=sys.stderr)
        return 2
    workflow = sys.argv[1]
    inputs = dict(a.split("=", 1) for a in sys.argv[2:])
    env = os.environ
    url = f"{env['GITHUB_API_URL']}/repos/{env['GITHUB_REPOSITORY']}/actions/workflows/{workflow}/dispatches"
    request = urllib.request.Request(
        url,
        data=json.dumps({"ref": env["GITHUB_REF"], "inputs": inputs}).encode(),
        headers={
            "Authorization": f"token {env['TOKEN']}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            print(
                f"ci_dispatch.py: {workflow} started on {env['GITHUB_REF']} ({response.status})"
            )
    except urllib.error.HTTPError as error:
        print(
            f"ci_dispatch.py: {workflow}: {error.code} {error.read().decode()}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
