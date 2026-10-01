from __future__ import annotations

"""AUTHOR_DECISION layer helpers.

Explicit author decisions are the only preference truth source. Workflow
commits, observed file revisions and proxy pass@1 never become this layer by
themselves.
"""

from typing import Any

from .author_feedback import DECISIONS, TAXONOMY, append_author_feedback, feedback_status
from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json

SCHEMA = "minis.author-decision-report.v1"


def normalize_author_decision_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    value = dict(payload or {})
    decision = str(value.get("decision") or "").strip().lower()
    if decision not in DECISIONS:
        raise ValueError("author decision must be accept|revise|reject")
    codes = list(dict.fromkeys(str(x) for x in (value.get("reason_codes") or [])))
    unknown = [x for x in codes if x not in TAXONOMY]
    if unknown:
        raise ValueError("unknown feedback reason codes: " + ",".join(unknown))
    if decision in {"revise", "reject"} and not codes and not str(value.get("reason") or "").strip():
        raise ValueError("revise/reject decisions require reason_codes or reason text")
    confidence = str(value.get("confidence") or "high").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "high"
    reluctant = bool(value.get("reluctant_accept") or value.get("begrudging"))
    return {
        "decision": decision,
        "author_id": str(value.get("author_id") or "author"),
        "reason_codes": codes,
        "reason": (str(value["reason"]) if value.get("reason") is not None else None),
        "changed_spans": list(value.get("changed_spans") or []),
        "revision_round": value.get("revision_round"),
        "confidence": confidence,
        "reluctant_accept": reluctant,
        "gate_pass": value.get("gate_pass"),
        "notes": value.get("notes"),
    }


def record_author_decision(
    store: Any,
    *,
    decision: str,
    author_id: str,
    candidate_hash: str,
    source_state_hash: str,
    source_event_head: str | None = None,
    turn_id: str | None = None,
    scene_id: str | None = None,
    reason_codes: list[str] | None = None,
    reason: str | None = None,
    changed_spans: list[dict[str, Any]] | None = None,
    revision_round: int | None = None,
    gate_pass: bool | None = None,
    confidence: str = "high",
    reluctant_accept: bool = False,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = normalize_author_decision_payload({
        "decision": decision,
        "author_id": author_id,
        "reason_codes": reason_codes,
        "reason": reason,
        "changed_spans": changed_spans,
        "revision_round": revision_round,
        "confidence": confidence,
        "reluctant_accept": reluctant_accept,
        "gate_pass": gate_pass,
    })
    event = append_author_feedback(
        store,
        decision=payload["decision"],
        author_id=payload["author_id"],
        candidate_hash=candidate_hash,
        source_state_hash=source_state_hash,
        source_event_head=source_event_head,
        turn_id=turn_id,
        scene_id=scene_id,
        reason_codes=payload["reason_codes"],
        reason=payload["reason"],
        changed_spans=payload["changed_spans"],
        revision_round=payload["revision_round"],
        explicit=True,
        gate_pass=payload["gate_pass"],
        provenance={
            **dict(provenance or {}),
            "confidence": payload["confidence"],
            "reluctant_accept": payload["reluctant_accept"],
            "authority_layer": "AUTHOR_DECISION",
        },
    )
    finding = normalize_finding({
        "layer": "AUTHOR_DECISION",
        "code": f"AUTHOR_{payload['decision'].upper()}",
        "severity": "OK" if payload["decision"] == "accept" and not payload["reluctant_accept"] else "P2",
        "confidence": payload["confidence"],
        "claim": f"author {payload['decision']} recorded",
        "blocks_commit": False,
        "details": {
            "event_id": event.get("event_id"),
            "reason_codes": payload["reason_codes"],
            "reluctant_accept": payload["reluctant_accept"],
        },
    })
    authority = build_authority_report(
        findings=[finding],
        source="author_decision",
        subject={"turn_id": turn_id, "scene_id": scene_id, "candidate_hash": candidate_hash},
    )
    report = {
        "schema": SCHEMA,
        "event": event,
        "authority": authority,
        "status": feedback_status(store)["status"],
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def require_scene_author_decision(
    *,
    scene_id: str | None,
    author_decision: dict[str, Any] | None,
    authority_record: dict[str, Any] | None = None,
    allow_system_commit: bool = True,
) -> dict[str, Any] | None:
    """Return normalized decision when required.

    Policy:
    - non-scene / system commits may omit decision
    - scene-bound production commits require explicit accept decision payload
      when authority.require_author_decision_on_scene_commit is true (default)
    """
    authority_record = authority_record or {}
    required = bool(authority_record.get("require_author_decision_on_scene_commit", True))
    if not scene_id:
        return None if allow_system_commit else normalize_author_decision_payload(author_decision)
    if not required:
        return normalize_author_decision_payload(author_decision) if author_decision else None
    if not author_decision:
        raise ValueError("scene-bound production commit requires explicit author_decision payload")
    payload = normalize_author_decision_payload(author_decision)
    if payload["decision"] != "accept":
        raise ValueError("only decision=accept may accompany a successful canon commit; use reject/revise without commit")
    return payload
