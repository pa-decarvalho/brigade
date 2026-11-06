"""Copy the files tracked by git (uncommitted changes included) into .ctt/src for ctt.

ponytail: works around ctt 3.0.0 on Windows. ctt streams `git archive` into tarfile
(mode "r|"), stops reading before git is done writing, and git fails on the closed
pipe ("Failed to snapshot the template source"). Reading the whole archive first
avoids it; running ctt on a non-git directory makes it skip its own snapshot.
Remove when ctt drains the pipe.
"""

import io
import shutil
import subprocess
import tarfile
from pathlib import Path

shutil.rmtree(".ctt", ignore_errors=True)
ref = subprocess.run(["git", "stash", "create"], capture_output=True, text=True, check=True).stdout.strip()
archive = subprocess.run(["git", "archive", ref or "HEAD"], capture_output=True, check=True).stdout
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(Path(".ctt/src"), filter="data")
