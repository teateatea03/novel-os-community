from __future__ import annotations

"""Durable host-side lifecycle for external model microtasks.

Every non-v2 record passes an explicit migration registry before use.  A v1
running lease is invalidated and rescheduled; no legacy worker can complete it.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json
from .durability import crash_failpoint
from .model_tasks import validate_model_result

TERMINAL = {"completed", "failed", "cancelled", "stale"}
ACTIVITY_SCHEMA = "minis.model-activity.v2"


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _activity_path(store: Any, activity_id: str) -> Path:
    activity_id = store._safe_segment(activity_id, "activity_id")
    return store.base / "model-activities" / f"{activity_id}.json"


def _migrate_v1_to_v2(rec: dict[str, Any]) -> dict[str, Any]:
    old_hash = sha256_json(rec); out = dict(rec); old_status = str(out.get("status", "scheduled"))
    if old_status not in TERMINAL | {"scheduled", "running"}:
        raise ValueError(f"unsupported v1 activity status: {old_status}")
    out["schema"] = ACTIVITY_SCHEMA
    if old_status == "running":
        out["status"] = "scheduled"
        out["lease_owner"] = None; out["lease_expires_at"] = None
        out["failure_code"] = "LEGACY_V1_LEASE_INVALIDATED"
    out["lease_token"] = None
    out["migrated_from"] = "minis.model-activity.v1"
    out["migration_version"] = "activity-v1-to-v2-lease-invalidation-v1"
    out["migration_source_hash"] = old_hash; out["migrated_at"] = now_iso(); out["updated_at"] = now_iso()
    out.setdefault("history", []).append({"status": out.get("status"), "at": out["updated_at"], "reason": "migrated_v1_to_v2", "legacy_status": old_status})
    return out


MIGRATIONS = {"minis.model-activity.v1": _migrate_v1_to_v2}


def _load(store: Any, activity_id: str, *, persist_migration: bool = True) -> dict[str, Any]:
    path = _activity_path(store, activity_id); value = store._read_json(path)
    if value is None: raise FileNotFoundError(activity_id)
    schema = value.get("schema")
    if schema == ACTIVITY_SCHEMA: return value
    migrate = MIGRATIONS.get(str(schema))
    if migrate is None: raise ValueError(f"unsupported model activity schema: {schema}")
    value = migrate(value)
    if persist_migration:
        store._atomic_json(path, value); crash_failpoint("activity_after_migration")
    return value


def schedule_model_activity(store: Any, packet: dict[str, Any], *, max_attempts: int = 3) -> dict[str, Any]:
    activity_id = "activity-" + sha256_json([store.project_id, store.session_id, store.branch_id, packet.get("task_hash")]).split(":")[-1][:24]
    path = _activity_path(store, activity_id)
    with store.transaction_lock():
        existing = store._read_json(path)
        if existing: return _load(store, activity_id)
        rec = {"schema": ACTIVITY_SCHEMA, "activity_id": activity_id,
               "project_id": store.project_id, "session_id": store.session_id, "branch_id": store.branch_id,
               "task": packet.get("task"), "task_hash": packet.get("task_hash"),
               "source_state_hash": packet.get("source_state_hash"), "packet": packet,
               "status": "scheduled", "attempt": 0, "max_attempts": max(1, int(max_attempts)),
               "lease_owner": None, "lease_token": None, "lease_expires_at": None, "result": None, "validation": None,
               "created_at": now_iso(), "updated_at": now_iso(), "history": [{"status": "scheduled", "at": now_iso()}]}
        store._atomic_json(path, rec); crash_failpoint("activity_after_schedule"); return rec


def claim_model_activity(store: Any, activity_id: str, *, worker_id: str, lease_seconds: int = 120) -> dict[str, Any]:
    with store.transaction_lock():
        rec = _load(store, activity_id); now = datetime.now(timezone.utc)
        if rec["status"] in TERMINAL: raise ValueError(f"activity is terminal: {rec['status']}")
        expiry = rec.get("lease_expires_at")
        if rec["status"] == "running" and expiry and _parse(expiry) > now:
            raise ValueError("activity lease is already held")
        if int(rec.get("attempt", 0)) >= int(rec.get("max_attempts", 1)):
            rec["status"] = "failed"; rec["failure_code"] = "MAX_ATTEMPTS_EXCEEDED"
        else:
            rec["status"] = "running"; rec["attempt"] = int(rec.get("attempt", 0)) + 1
            rec["lease_owner"] = worker_id
            rec["lease_token"] = sha256_json([rec["activity_id"], rec["attempt"], worker_id, now.isoformat()])
            rec["lease_expires_at"] = (now + timedelta(seconds=max(1, int(lease_seconds)))).isoformat().replace("+00:00", "Z")
        rec["updated_at"] = now_iso(); rec.setdefault("history", []).append({"status": rec["status"], "at": rec["updated_at"], "worker_id": worker_id, "attempt": rec["attempt"]})
        store._atomic_json(_activity_path(store, activity_id), rec); crash_failpoint("activity_after_claim"); return rec


def complete_model_activity(store: Any, activity_id: str, *, worker_id: str, result: dict[str, Any], lease_token: str | None = None) -> dict[str, Any]:
    with store.transaction_lock():
        rec = _load(store, activity_id)
        if rec.get("schema") != ACTIVITY_SCHEMA: raise ValueError("activity must be migrated to v2")
        if rec.get("status") != "running" or rec.get("lease_owner") != worker_id: raise ValueError("worker does not own the running activity")
        if not rec.get("lease_token") or lease_token != rec.get("lease_token"):
            raise ValueError("stale or missing activity lease token")
        expiry = rec.get("lease_expires_at")
        if not expiry or _parse(expiry) <= datetime.now(timezone.utc): raise ValueError("activity lease has expired")
        validation = validate_model_result(rec["packet"], result)
        current = store.load_state(); current_hash = (current or {}).get("state_hash")
        if current_hash != rec.get("source_state_hash"):
            rec["status"] = "stale"; validation.setdefault("errors", []).append({"code": "MODEL_ACTIVITY_SOURCE_STATE_STALE", "expected": rec.get("source_state_hash"), "actual": current_hash}); validation["ok"] = False; validation["status"] = "fail"
        elif validation.get("ok"): rec["status"] = "completed"; rec["result"] = result
        elif int(rec.get("attempt", 0)) >= int(rec.get("max_attempts", 1)): rec["status"] = "failed"; rec["failure_code"] = "INVALID_MODEL_RESULT"
        else: rec["status"] = "scheduled"; rec["failure_code"] = "RETRY_INVALID_MODEL_RESULT"
        rec["validation"] = validation; rec["lease_owner"] = None; rec["lease_token"] = None; rec["lease_expires_at"] = None; rec["updated_at"] = now_iso()
        rec.setdefault("history", []).append({"status": rec["status"], "at": rec["updated_at"], "attempt": rec["attempt"]})
        store._atomic_json(_activity_path(store, activity_id), rec); crash_failpoint("activity_after_complete"); return rec


def cancel_model_activity(store: Any, activity_id: str, *, reason: str) -> dict[str, Any]:
    with store.transaction_lock():
        rec = _load(store, activity_id)
        if rec["status"] in TERMINAL: return rec
        rec.update({"status": "cancelled", "cancel_reason": reason, "lease_owner": None, "lease_token": None, "lease_expires_at": None, "updated_at": now_iso()})
        rec.setdefault("history", []).append({"status": "cancelled", "at": rec["updated_at"], "reason": reason})
        store._atomic_json(_activity_path(store, activity_id), rec); return rec


def recover_model_activities(store: Any, *, at: str | None = None) -> dict[str, Any]:
    with store.transaction_lock():
        now = _parse(at) if at else datetime.now(timezone.utc); recovered = []; blocked = []
        directory = store.base / "model-activities"
        for path in sorted(directory.glob("*.json")) if directory.exists() else []:
            rec = _load(store, path.stem)
            if rec.get("status") == "running" and rec.get("lease_expires_at") and _parse(rec["lease_expires_at"]) <= now:
                if int(rec.get("attempt", 0)) >= int(rec.get("max_attempts", 1)): rec["status"] = "failed"; rec["failure_code"] = "LEASE_EXPIRED_MAX_ATTEMPTS"
                else: rec["status"] = "scheduled"
                rec["lease_owner"] = None; rec["lease_token"] = None; rec["lease_expires_at"] = None; rec["updated_at"] = now_iso(); rec.setdefault("history", []).append({"status": rec["status"], "at": rec["updated_at"], "reason": "lease_expired"}); store._atomic_json(path, rec); recovered.append(rec["activity_id"])
            if rec.get("status") in {"scheduled", "running"}: blocked.append(rec["activity_id"])
        return {"schema": "minis.model-activity-recovery.v2", "recovered": recovered, "pending": blocked, "status": "pass" if not blocked else "pending"}


def model_activity_health(store: Any) -> dict[str, Any]:
    directory = store.base / "model-activities"; counts: dict[str, int] = {}; pending = []; incompatible = []
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        rec = store._read_json(path); schema = rec.get("schema")
        if schema not in {ACTIVITY_SCHEMA, "minis.model-activity.v1"}: incompatible.append(path.stem)
        status = str(rec.get("status", "unknown")); counts[status] = counts.get(status, 0) + 1
        if status in {"scheduled", "running"}: pending.append(rec.get("activity_id"))
    return {"schema": "minis.model-activity-health.v2", "counts": counts, "pending": pending, "incompatible": incompatible, "status": "blocked" if incompatible else ("pass" if not pending else "pending")}
