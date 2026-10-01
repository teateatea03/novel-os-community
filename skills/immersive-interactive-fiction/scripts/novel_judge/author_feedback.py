from __future__ import annotations

"""Append-only, non-canonical author feedback evidence.

Feedback calibrates generation quality but never grants canon authority. Canon
still crosses only through ProjectRuntimeAdapter.commit and Gate authorization.
"""

import json, os
from pathlib import Path
from typing import Any
from .canonical import now_iso, sha256_json

SCHEMA = "minis.author-feedback-event.v1"
LEDGER_SCHEMA = "minis.author-feedback-ledger.v1"
DECISIONS = {"accept", "revise", "reject"}
TAXONOMY = {"character_voice", "human_voice", "pacing", "sensory_sound", "agency", "continuity", "clarity", "behavior", "world_rules", "other"}


def _paths(store: Any) -> tuple[Path, Path]:
    root = store.base / "quality"; return root / "author-feedback.jsonl", root / "author-feedback-manifest.json"


def read_author_feedback(store: Any) -> list[dict[str, Any]]:
    ledger, _ = _paths(store)
    if not ledger.is_file(): return []
    rows = []
    for number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip(): continue
        value = json.loads(line)
        if value.get("schema") != SCHEMA: raise ValueError(f"feedback schema mismatch at line {number}")
        expected = sha256_json({k: v for k, v in value.items() if k != "event_hash"})
        if value.get("event_hash") != expected: raise ValueError(f"feedback hash mismatch at line {number}")
        previous = rows[-1].get("event_hash") if rows else None
        if value.get("previous_event_hash") != previous: raise ValueError(f"feedback chain mismatch at line {number}")
        rows.append(value)
    return rows


def feedback_status(store: Any) -> dict[str, Any]:
    ledger, manifest_path = _paths(store); errors = []
    try: rows = read_author_feedback(store)
    except Exception as exc: rows = []; errors.append(str(exc))
    manifest = store._read_json(manifest_path, {}) or {}
    expected = {"event_count": len(rows), "head_event_hash": rows[-1]["event_hash"] if rows else None,
                "ledger_sha256": sha256_json(rows)}
    if manifest_path.is_file():
        for key, value in expected.items():
            if manifest.get(key) != value: errors.append(f"manifest_{key}_mismatch")
    elif ledger.is_file(): errors.append("missing_feedback_manifest")
    return {"schema": LEDGER_SCHEMA, "status": "pass" if not errors else "fail", "errors": errors,
            **expected, "explicit_count": sum(bool(x.get("explicit")) for x in rows), "events": rows}


def append_author_feedback(store: Any, *, decision: str, author_id: str, candidate_hash: str,
                           source_state_hash: str, source_event_head: str | None,
                           turn_id: str | None = None, scene_id: str | None = None,
                           reason_codes: list[str] | None = None, reason: str | None = None,
                           changed_spans: list[dict[str, Any]] | None = None,
                           revision_round: int | None = None, explicit: bool = True,
                           gate_pass: bool | None = None,
                           provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    if decision not in DECISIONS: raise ValueError("unsupported author feedback decision")
    if not candidate_hash or not source_state_hash: raise ValueError("feedback requires candidate and source-state hashes")
    codes = list(dict.fromkeys(str(x) for x in (reason_codes or [])))
    unknown = [x for x in codes if x not in TAXONOMY]
    if unknown: raise ValueError("unknown feedback reason codes: " + ",".join(unknown))
    ledger, manifest_path = _paths(store); ledger.parent.mkdir(parents=True, exist_ok=True)
    with store.transaction_lock():
        rows = read_author_feedback(store); previous = rows[-1]["event_hash"] if rows else None
        core = {"decision": decision, "author_id": str(author_id), "candidate_hash": str(candidate_hash),
                "source_state_hash": str(source_state_hash), "source_event_head": source_event_head,
                "turn_id": turn_id, "scene_id": scene_id, "reason_codes": codes,
                "reason": str(reason) if reason is not None else None,
                "changed_spans": list(changed_spans or []), "revision_round": revision_round,
                "explicit": bool(explicit), "gate_pass": gate_pass, "provenance": dict(provenance or {})}
        event_id = "feedback-" + sha256_json(core).split(":")[-1][:24]
        for row in rows:
            if row.get("event_id") == event_id:
                if any(row.get(k) != v for k, v in core.items()): raise ValueError("feedback idempotency conflict")
                return row
        event = {"schema": SCHEMA, "event_id": event_id, **core,
                 "previous_event_hash": previous, "created_at": now_iso()}
        event["event_hash"] = sha256_json(event)
        with open(ledger, "ab") as fh:
            fh.write((json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")); fh.flush(); os.fsync(fh.fileno())
        rows.append(event)
        manifest = {"schema": LEDGER_SCHEMA, "event_count": len(rows), "head_event_hash": event["event_hash"],
                    "ledger_sha256": sha256_json(rows), "updated_at": now_iso()}
        manifest["manifest_hash"] = sha256_json(manifest); store._atomic_json(manifest_path, manifest)
        return event


def record_command_feedback(adapter: Any, command: dict[str, Any], candidate: dict[str, Any], *, decision: str) -> dict[str, Any]:
    payload = command.get("request", {}).get("payload", {}) or {}
    feedback = payload.get("author_feedback", {}) if isinstance(payload.get("author_feedback"), dict) else {}
    codes = list(feedback.get("reason_codes") or [])
    reason = feedback.get("reason") or command["request"].get("reason")
    if decision == "accept" and not codes:
        codes = ["other"]
    if decision in {"revise", "reject"} and not codes and not (reason and str(reason).strip()):
        raise ValueError("revise/reject command feedback requires reason_codes or reason")
    return append_author_feedback(
        adapter.store, decision=decision, author_id=command["request"].get("author_id", "author"),
        candidate_hash=candidate["candidate_hash"], source_state_hash=candidate["source_state_hash"],
        source_event_head=candidate.get("source_event_head"), turn_id=candidate.get("turn_id"),
        scene_id=candidate.get("scene_id"), reason_codes=codes,
        reason=reason,
        changed_spans=feedback.get("changed_spans", []), revision_round=feedback.get("revision_round"),
        explicit=True, gate_pass=(True if decision == "accept" and command.get("authorization_hash") else feedback.get("gate_pass")),
        provenance={"command_id": command.get("command_id"), "command_kind": command.get("kind"),
                    "authority_layer": "AUTHOR_DECISION",
                    "reluctant_accept": bool(feedback.get("reluctant_accept")),
                    "confidence": feedback.get("confidence") or "high"})
