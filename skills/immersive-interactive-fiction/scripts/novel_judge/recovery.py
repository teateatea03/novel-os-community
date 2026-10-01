from __future__ import annotations

from typing import Any

from .errors import RECOVERY_REQUIRED
from .engine import recover_store
from .store import FileStore


def recover(store: FileStore) -> dict[str, Any]:
    return recover_store(store)


def require_clean(store: FileStore) -> dict[str, Any]:
    report = recover_store(store)
    if report.get("status") not in {"clean", "reconciled", "rolled_back_to_last_state"}:
        raise Exception(RECOVERY_REQUIRED)
    return report
