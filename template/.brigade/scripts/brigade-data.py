"""Runs brigade_data.py: kept for the first brigade:update from brigade 0.19 or earlier.

brigade-owned: updated by mise run brigade:update, do not edit.
That update runs the old brigade-update.py, which calls this name once Copier is done.
To remove in a later release.
"""

import runpy

runpy.run_path(".brigade/scripts/brigade_data.py", run_name="__main__")
