"""OS-backed branch locks, released automatically when the process dies."""
from __future__ import annotations
import errno
import math
import os
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None
try:
    import msvcrt
except ImportError:
    msvcrt = None

@contextmanager
def exclusive_file_lock(path: Path, *, timeout: float = 10.0):
    timeout = float(timeout)
    if not math.isfinite(timeout) or timeout < 0:
        raise ValueError("lock timeout must be finite and nonnegative")
    if fcntl is None and msvcrt is None:
        raise RuntimeError("cross-process file locking unavailable; use a supported host")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as fh:
        if fcntl is None:
            if os.fstat(fh.fileno()).st_size == 0:
                fh.write(b"\0")
                fh.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                if fcntl is not None:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EPERM, errno.EDEADLK}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("branch transaction lock timeout") from exc
                time.sleep(0.025)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            else:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
