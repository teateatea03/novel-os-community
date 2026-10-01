from __future__ import annotations

"""Durable, source-bound author command executor with lease fencing."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import re

from .branches import fork_branch
from .canonical import now_iso, sha256_json
from .gate_authority import make_author_override

COMMAND_SCHEMA = "minis.author-command.v2"
CANDIDATE_SCHEMA = "minis.author-command-candidate.v1"
TERMINAL = {"completed", "committed", "rejected", "cancelled", "failed", "stale"}
ACTIVE = {"pending", "claimed", "validating_source", "candidate_created", "gates_pending", "authorized"}
ALLOWED = {"create_candidate", "request_revision", "request_approval", "request_override", "request_branch", "request_promotion"}


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _path(store: Any, command_id: str) -> Path:
    return store.base / "commands" / f"{store._safe_segment(command_id, 'command_id')}.json"


def _record_hash(record: dict[str, Any]) -> str:
    return sha256_json({k: v for k, v in record.items() if k != "record_hash"})


def _request_hash_v1(record: dict[str, Any]) -> str:
    return sha256_json({k: v for k, v in record.items() if k != "request_hash"})


def _history(record: dict[str, Any], status: str, **details: Any) -> None:
    record.setdefault("history", []).append({"status": status, "at": now_iso(), **details})


def _seal(record: dict[str, Any]) -> dict[str, Any]:
    record["updated_at"] = now_iso(); record["record_hash"] = _record_hash(record); return record


def _validate(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema") != COMMAND_SCHEMA: raise ValueError("unsupported author command schema")
    if record.get("kind") not in ALLOWED: raise ValueError("unsupported author command kind")
    if record.get("status") not in TERMINAL | ACTIVE: raise ValueError("unsupported author command status")
    if record.get("record_hash") != _record_hash(record): raise ValueError("author command record hash mismatch")
    request = record.get("request")
    if not isinstance(request, dict) or request.get("request_hash") != sha256_json({k: v for k, v in request.items() if k != "request_hash"}):
        raise ValueError("author command immutable request hash mismatch")
    return record


def _migrate_v1(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema") != "minis.author-command-request.v1": raise ValueError("unsupported legacy command schema")
    if record.get("request_hash") != _request_hash_v1(record): raise ValueError("legacy author command request hash mismatch")
    request = {k: record.get(k) for k in ("author_id", "reason", "source_state_hash", "source_event_head", "payload", "created_at")}
    request["request_hash"] = sha256_json(request)
    out = {"schema": COMMAND_SCHEMA, "command_id": record.get("command_id"), "kind": record.get("kind"),
           "status": record.get("status", "pending"), "request": request,
           "attempt": 0, "max_attempts": 3, "lease_owner": None, "lease_token": None,
           "lease_expires_at": None, "candidate_id": None, "authorization_hash": None,
           "result": None, "failure_code": None, "created_at": record.get("created_at"),
           "migrated_from": "minis.author-command-request.v1", "migration_source_hash": sha256_json(record),
           "history": [{"status": record.get("status", "pending"), "at": record.get("created_at"), "reason": "legacy_request"},
                       {"status": record.get("status", "pending"), "at": now_iso(), "reason": "migrated_v1_to_v2"}]}
    return _seal(out)


def load_author_command(store: Any, command_id: str, *, persist_migration: bool = True) -> dict[str, Any]:
    path = _path(store, command_id); value = store._read_json(path)
    if value is None: raise FileNotFoundError(command_id)
    if value.get("schema") == "minis.author-command-request.v1":
        value = _migrate_v1(value)
        if persist_migration: store._atomic_json(path, value)
    return _validate(value)


def make_author_command(*, kind: str, author_id: str, reason: str, source_state_hash: str,
                        source_event_head: str | None, payload: dict[str, Any], created_at: str | None = None) -> dict[str, Any]:
    if kind not in ALLOWED: raise ValueError("unsupported controlled command kind")
    created = created_at or now_iso()
    request = {"author_id": str(author_id), "reason": str(reason), "source_state_hash": source_state_hash,
               "source_event_head": source_event_head, "payload": dict(payload), "created_at": created}
    request["request_hash"] = sha256_json(request)
    command_id = "author-command-" + sha256_json([kind, request["request_hash"]]).split(":")[-1][:24]
    record = {"schema": COMMAND_SCHEMA, "command_id": command_id, "kind": kind, "status": "pending",
              "request": request, "attempt": 0, "max_attempts": 3, "lease_owner": None,
              "lease_token": None, "lease_expires_at": None, "candidate_id": None,
              "authorization_hash": None, "result": None, "failure_code": None,
              "created_at": created, "history": [{"status": "pending", "at": created}]}
    return _seal(record)


def write_author_command(store: Any, record: dict[str, Any]) -> dict[str, Any]:
    _validate(record); path = _path(store, record["command_id"]); path.parent.mkdir(parents=True, exist_ok=True)
    with store.transaction_lock():
        if path.exists():
            existing = load_author_command(store, record["command_id"])
            if existing["request"]["request_hash"] != record["request"]["request_hash"]: raise FileExistsError(path)
            return existing
        store._atomic_json(path, record)
    return record


def _mark_stale(store: Any, record: dict[str, Any], actual_hash: str | None) -> dict[str, Any]:
    record.update({"status": "stale", "failure_code": "COMMAND_SOURCE_STATE_STALE",
                   "lease_owner": None, "lease_token": None, "lease_expires_at": None,
                   "result": {"expected_state_hash": record["request"].get("source_state_hash"), "actual_state_hash": actual_hash}})
    _history(record, "stale", reason="source_state_changed", actual_state_hash=actual_hash)
    _seal(record); store._atomic_json(_path(store, record["command_id"]), record); return record


def claim_author_command(store: Any, command_id: str, *, worker_id: str, lease_seconds: int = 120) -> dict[str, Any]:
    with store.transaction_lock():
        record = load_author_command(store, command_id); current = store.load_state() or {}; now = datetime.now(timezone.utc)
        if record["status"] in TERMINAL: raise ValueError(f"command is terminal: {record['status']}")
        if record["request"].get("source_state_hash") != current.get("state_hash"):
            return _mark_stale(store, record, current.get("state_hash"))
        expiry = record.get("lease_expires_at")
        if record["status"] == "claimed" and expiry and _parse(expiry) > now: raise ValueError("command lease is already held")
        if int(record.get("attempt", 0)) >= int(record.get("max_attempts", 1)):
            record["status"] = "failed"; record["failure_code"] = "MAX_ATTEMPTS_EXCEEDED"
        else:
            record["status"] = "claimed"; record["attempt"] = int(record.get("attempt", 0)) + 1
            record["lease_owner"] = str(worker_id)
            record["lease_token"] = sha256_json([command_id, record["attempt"], worker_id, now.isoformat()])
            record["lease_expires_at"] = (now + timedelta(seconds=max(1, int(lease_seconds)))).isoformat().replace("+00:00", "Z")
        _history(record, record["status"], worker_id=worker_id, attempt=record["attempt"])
        _seal(record); store._atomic_json(_path(store, command_id), record); return record


def _owned(store: Any, command_id: str, worker_id: str, lease_token: str) -> dict[str, Any]:
    record = load_author_command(store, command_id)
    if record.get("status") != "claimed" or record.get("lease_owner") != worker_id: raise ValueError("worker does not own claimed command")
    if not record.get("lease_token") or record.get("lease_token") != lease_token: raise ValueError("stale or missing command lease token")
    if not record.get("lease_expires_at") or _parse(record["lease_expires_at"]) <= datetime.now(timezone.utc): raise ValueError("command lease expired")
    return record


def _candidate_from_payload(adapter: Any, record: dict[str, Any]) -> dict[str, Any]:
    payload = record["request"].get("payload") or {}; raw = payload.get("candidate", payload)
    if not isinstance(raw, dict): raise ValueError("candidate payload must be an object")
    turn_id = adapter.store._safe_segment(raw.get("turn_id"), "turn_id")
    operations = raw.get("operations", [])
    if not isinstance(operations, list) or not all(isinstance(x, dict) for x in operations): raise ValueError("candidate operations must be a list of objects")
    scene_sha = str(raw.get("scene_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", scene_sha): raise ValueError("candidate scene_sha256 is malformed")
    candidate = {"schema": CANDIDATE_SCHEMA, "candidate_id": "command-candidate-" + record["command_id"].split("-")[-1],
                 "command_id": record["command_id"], "turn_id": turn_id,
                 "source_state_hash": record["request"]["source_state_hash"], "source_event_head": record["request"].get("source_event_head"),
                 "operations": operations, "actor_id": str(raw.get("actor_id", "world")),
                 "action_type": str(raw.get("action_type", "world_tick")), "source": str(raw.get("source", "author")),
                 "semantic_kind": raw.get("semantic_kind"), "semantic_effects": raw.get("semantic_effects"),
                 "summary": raw.get("summary"), "scene_id": raw.get("scene_id"), "chapter_id": raw.get("chapter_id"),
                 "source_artifact_hash": raw.get("source_artifact_hash"), "source_artifact_path": raw.get("source_artifact_path"),
                 "scene_sha256": scene_sha, "created_at": now_iso()}
    candidate["candidate_hash"] = sha256_json(candidate)
    return candidate


def _candidate_path(store: Any, candidate_id: str) -> Path:
    return store.base / "command-candidates" / f"{store._safe_segment(candidate_id, 'candidate_id')}.json"


def _finish(store: Any, record: dict[str, Any], status: str, result: dict[str, Any], *, reason: str | None = None) -> dict[str, Any]:
    record.update({"status": status, "result": result, "lease_owner": None, "lease_token": None, "lease_expires_at": None})
    _history(record, status, **({"reason": reason} if reason else {})); _seal(record); store._atomic_json(_path(store, record["command_id"]), record); return record


def execute_author_command(adapter: Any, command_id: str, *, worker_id: str, lease_token: str) -> dict[str, Any]:
    store = adapter.store
    try:
        return _execute_author_command(adapter, command_id, worker_id=worker_id, lease_token=lease_token)
    except Exception as exc:
        # Once execution has started, deterministic validation/Gate failures
        # become durable terminal command evidence. Ownership/fencing errors
        # remain exceptions and never mutate a command owned by another worker.
        try:
            record = load_author_command(store, command_id)
            if record.get("lease_owner") == worker_id and record.get("lease_token") == lease_token and record.get("status") not in TERMINAL:
                with store.transaction_lock():
                    record = load_author_command(store, command_id)
                    record["failure_code"] = "COMMAND_EXECUTION_FAILED"
                    _finish(store, record, "failed", {"error_type": type(exc).__name__, "error": str(exc)}, reason=str(exc))
        except Exception: pass
        raise


def _execute_author_command(adapter: Any, command_id: str, *, worker_id: str, lease_token: str) -> dict[str, Any]:
    store = adapter.store
    with store.transaction_lock():
        record = _owned(store, command_id, worker_id, lease_token); current = store.load_state() or {}
        if record["request"].get("source_state_hash") != current.get("state_hash"): return _mark_stale(store, record, current.get("state_hash"))
        record["status"] = "validating_source"; _history(record, "validating_source"); _seal(record); store._atomic_json(_path(store, command_id), record)
        kind = record["kind"]; payload = record["request"].get("payload") or {}
        if kind in {"create_candidate", "request_revision", "request_approval"}:
            candidate = _candidate_from_payload(adapter, record); cpath = _candidate_path(store, candidate["candidate_id"])
            if cpath.exists():
                old = store._read_json(cpath)
                if old.get("candidate_hash") != candidate.get("candidate_hash"): raise ValueError("candidate idempotency conflict")
            else: store._atomic_json(cpath, candidate)
            record["candidate_id"] = candidate["candidate_id"]; record["status"] = "candidate_created"
            _history(record, "candidate_created", candidate_id=candidate["candidate_id"], candidate_hash=candidate["candidate_hash"])
            _seal(record); store._atomic_json(_path(store, command_id), record)
        else: candidate = None
    if kind == "create_candidate":
        with store.transaction_lock(): return _finish(store, load_author_command(store, command_id), "completed", {"candidate": candidate})
    if kind == "request_revision":
        with store.transaction_lock(): done = _finish(store, load_author_command(store, command_id), "completed", {"revised_candidate": candidate})
        from .author_feedback import record_command_feedback
        done["author_feedback"] = record_command_feedback(adapter, done, candidate, decision="revise")
        return done
    if kind == "request_override":
        envelope = payload.get("envelope"); codes = payload.get("finding_codes")
        if not isinstance(envelope, dict): raise ValueError("override command requires envelope")
        override = make_author_override(envelope=envelope, author_id=record["request"]["author_id"], reason=record["request"]["reason"], finding_codes=codes)
        with store.transaction_lock(): return _finish(store, load_author_command(store, command_id), "completed", {"override": override})
    if kind == "request_branch":
        child_id = store._safe_segment(payload.get("branch_id"), "branch_id")
        child = fork_branch(store, child_id, checkpoint_id=payload.get("checkpoint_id"), scope=str(payload.get("scope", "experiment")))
        with store.transaction_lock(): return _finish(store, load_author_command(store, command_id), "completed", {"branch_id": child.branch_id, "path": str(child.base)})
    if kind == "request_promotion":
        decision = str(payload.get("author_decision", "reject"))
        if decision not in {"approve", "reject"}: raise ValueError("author_decision must be approve or reject")
        report = {"schema": "minis.canon-promotion-request.v1", "project_id": store.project_id,
                  "session_id": store.session_id, "branch_id": store.branch_id,
                  "source_state_hash": record["request"]["source_state_hash"],
                  "target_scope": str(payload.get("target_scope", "candidate-canon")),
                  "author_decision": decision, "canon_write": "not_performed", "created_at": now_iso()}
        report["request_hash"] = sha256_json(report)
        with store.transaction_lock(): return _finish(store, load_author_command(store, command_id), "completed", {"promotion_request": report})
    # Approval is the only command permitted to cross the canonical boundary.
    with store.transaction_lock():
        record = load_author_command(store, command_id); record["status"] = "gates_pending"; _history(record, "gates_pending"); _seal(record); store._atomic_json(_path(store, command_id), record)
    envelopes = payload.get("envelopes"); overrides = payload.get("overrides", [])
    if not isinstance(envelopes, list): raise ValueError("approval command requires gate envelopes")
    from .production import make_candidate_binding
    from .semantic_events import compile_semantic_delta
    semantic = compile_semantic_delta(turn_id=candidate["turn_id"], actor_id=candidate["actor_id"], action_type=candidate["action_type"], operations=candidate["operations"], summary=candidate.get("summary"), scene_id=candidate.get("scene_id"), declared_effects=candidate.get("semantic_effects"), semantic_kind=candidate.get("semantic_kind"))
    binding = make_candidate_binding(turn_id=candidate["turn_id"], operations=candidate["operations"],
        actor_id=candidate["actor_id"], action_type=candidate["action_type"], summary=candidate.get("summary"),
        scene_id=candidate.get("scene_id"), chapter_id=candidate.get("chapter_id"),
        scene_sha256=candidate["scene_sha256"], semantic_hash=semantic["semantic_hash"])
    authorization = adapter.approve_gate_bundle(turn_id=candidate["turn_id"], scene_sha256=candidate["scene_sha256"],
                                                source_state_hash=candidate["source_state_hash"], envelopes=envelopes, overrides=overrides,
                                                candidate_binding=binding)
    with store.transaction_lock():
        record = load_author_command(store, command_id); record["status"] = "authorized"; record["authorization_hash"] = authorization["authorization_hash"]
        _history(record, "authorized", authorization_hash=authorization["authorization_hash"]); _seal(record); store._atomic_json(_path(store, command_id), record)
    result = adapter.commit(turn_id=candidate["turn_id"], operations=candidate["operations"], expected_state_hash=candidate["source_state_hash"],
                            actor_id=candidate["actor_id"], action_type=candidate["action_type"], source=candidate["source"],
                            summary=candidate.get("summary"), scene_id=candidate.get("scene_id"), chapter_id=candidate.get("chapter_id"),
                            source_artifact_hash=candidate.get("source_artifact_hash"), source_artifact_path=candidate.get("source_artifact_path"),
                            semantic_kind=candidate.get("semantic_kind"), semantic_effects=candidate.get("semantic_effects"),
                            scene_sha256=candidate["scene_sha256"])
    with store.transaction_lock():
        record = load_author_command(store, command_id)
        final = _finish(store, record, "committed", {"candidate_id": candidate["candidate_id"], "event_id": result["event"]["event_id"],
                                                      "after_state_hash": result.get("post_state_hash"), "authorization_hash": authorization["authorization_hash"]})
    from .author_feedback import record_command_feedback
    feedback_event = record_command_feedback(adapter, final, candidate, decision="accept")
    final["author_feedback"] = feedback_event
    # The commit refresh observed an intermediate authorized command. Refresh
    # once more so the workbench sees the terminal command state.
    try:
        from .production_projections import refresh_production_projections
        refresh_production_projections(adapter)
    except Exception: pass
    return final


def fail_author_command(store: Any, command_id: str, *, worker_id: str, lease_token: str, reason: str) -> dict[str, Any]:
    with store.transaction_lock():
        record = _owned(store, command_id, worker_id, lease_token); record["failure_code"] = "COMMAND_EXECUTION_FAILED"
        return _finish(store, record, "failed", {"reason": str(reason)}, reason=str(reason))


def recover_author_commands(store: Any, *, at: str | None = None) -> dict[str, Any]:
    now = _parse(at) if at else datetime.now(timezone.utc); recovered=[]; stale=[]; pending=[]
    with store.transaction_lock():
        directory = store.base / "commands"
        for path in sorted(directory.glob("*.json")) if directory.exists() else []:
            record = load_author_command(store, path.stem); current = store.load_state() or {}
            if record["status"] in ACTIVE and record["request"].get("source_state_hash") != current.get("state_hash"):
                _mark_stale(store, record, current.get("state_hash")); stale.append(record["command_id"]); continue
            if record["status"] == "claimed" and record.get("lease_expires_at") and _parse(record["lease_expires_at"]) <= now:
                if int(record.get("attempt",0)) >= int(record.get("max_attempts",1)):
                    record["status"]="failed";record["failure_code"]="LEASE_EXPIRED_MAX_ATTEMPTS"
                else: record["status"]="pending"
                record["lease_owner"]=None;record["lease_token"]=None;record["lease_expires_at"]=None
                _history(record,record["status"],reason="lease_expired");_seal(record);store._atomic_json(path,record);recovered.append(record["command_id"])
            if record["status"] in ACTIVE: pending.append(record["command_id"])
    return {"schema":"minis.author-command-recovery.v2","recovered":recovered,"stale":stale,"pending":pending,
            "status":"pass" if not pending else "pending"}


def author_command_health(store: Any) -> dict[str, Any]:
    counts={};active=[];stale=[];incompatible=[];directory=store.base/"commands"
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        try: record=load_author_command(store,path.stem,persist_migration=False)
        except Exception: incompatible.append(path.stem);continue
        status=record["status"];counts[status]=counts.get(status,0)+1
        if status in ACTIVE:active.append(record["command_id"])
        if status=="stale":stale.append(record["command_id"])
    return {"schema":"minis.author-command-health.v2","counts":counts,"active":active,"stale":stale,"incompatible":incompatible,
            "status":"blocked" if incompatible else ("pending" if active else "pass")}
