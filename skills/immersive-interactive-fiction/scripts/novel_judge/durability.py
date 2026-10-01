from __future__ import annotations

"""Small durability primitives shared by the file runtime.

SIGKILL failpoints are inert unless an exact test-only environment variable is
set.  They let subprocess tests exercise real process death between fsync and
rename/manifest phases instead of simulating crashes with exceptions.
"""

import os
from pathlib import Path


def fsync_directory(path: str | Path) -> None:
    directory = Path(path)
    fd = os.open(str(directory), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def crash_failpoint(name: str) -> None:
    if os.environ.get("NOVEL_JUDGE_SIGKILL_AT") == name:
        os.kill(os.getpid(), 9)
