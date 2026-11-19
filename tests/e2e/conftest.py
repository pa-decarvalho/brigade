"""brigade end to end on a local forge: the forge, the steps, the note.

Run on this machine: pytest tests/e2e --forge <gitea|github|forgejo|gitlab>
(mise run forges:test). The forge starts on first use (up.py) and stays up.
Each test writes .forges/<date>-<forge>-<project>.md: every step's result and
time, and the failed jobs' last log lines.
"""

import contextlib
import os
import subprocess
import time
from pathlib import Path

import pytest  # ty: ignore[import-not-found]  # run with uv run --with pytest
import up
from forges import FORGES, Forge


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--forge", choices=sorted(FORGES), required=True)


@pytest.fixture(scope="session")
def forge(request: pytest.FixtureRequest) -> Forge:
    kind = FORGES[request.config.getoption("--forge")]
    return kind(**up.ensure(kind.server))


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


class Note:
    """A test's steps, timed; written to .forges/ at the end."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.steps: list[tuple[str, str, float, str]] = []
        self.failed: list[str] = []  # steps that failed but let the test go on

    @contextlib.contextmanager
    def step(self, name: str, *, go_on: bool = False):
        """One step; with go_on, its failure is noted and the next steps run."""
        start = time.time()
        try:
            yield
        except pytest.skip.Exception as skip:
            self.steps.append((name, "skipped", time.time() - start, str(skip)))
            if not go_on:
                raise
        except Exception as error:  # noted, then raised or kept
            self.steps.append((name, "failed", time.time() - start, str(error)))
            if not go_on:
                raise
            self.failed.append(name)
        else:
            self.steps.append((name, "passed", time.time() - start, ""))

    def skip(self, *names: str, reason: str) -> None:
        self.steps += [(name, "skipped", 0.0, reason) for name in names]

    def write(self, forge: Forge, path: Path) -> Path:
        lines = [f"# {self.title} ({time.strftime('%Y-%m-%d %H:%M')})", ""]
        lines += [f"Forge: {forge.url}; project: {path}", ""]
        lines += ["| Step | Result | Time | Detail |", "|---|---|---|---|"]
        for name, outcome, seconds, message in self.steps:
            detail = " ".join(message.split())[:300].replace("|", "\\|")
            lines.append(f"| {name} | {outcome} | {seconds:.0f}s | {detail} |")
        if forge.logs:
            lines += ["", "## Failed jobs", "", *forge.logs]
        lines += ["", "## To improve", "", "-", ""]
        note = up.STATE / f"{time.strftime('%Y%m%d-%H%M')}-{self.title}.md"
        note.write_text("\n".join(lines))
        return note


@pytest.fixture
def note(request: pytest.FixtureRequest, forge: Forge, tmp_path: Path):
    record = Note(f"{forge.name}-{request.node.callspec.id}")
    forge.logs.clear()
    yield record
    print(f"\nnote: {record.write(forge, tmp_path)}")
