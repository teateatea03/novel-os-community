from __future__ import annotations
"""Read-only author workbench projection plus controlled command requests."""
import json
from pathlib import Path
from typing import Any
from .author_console import author_console_report
from .author_quality_eval import production_quality_telemetry
from .canonical import now_iso, sha256_json
from .semantic_invariants import inspect_state


def build_workbench_report(adapter: Any, *, timeline_limit: int = 100, readiness: dict[str, Any] | None = None) -> dict[str, Any]:
    store = adapter.store
    state = store.load_state()
    events = store.read_events()
    head = store._read_json(adapter.runtime_head_path, {})
    base = author_console_report(store, project_root=store.root)
    timeline = []
    for e in events[-max(1, timeline_limit):]:
        semantic = e.get("semantic_delta") if isinstance(e.get("semantic_delta"), dict) else {}
        scene = e.get("scene") or {}
        timeline.append({
            "event_id": e.get("event_id"),
            "turn_id": e.get("turn_id"),
            "scene_id": scene.get("scene_id"),
            "revision": e.get("after_revision"),
            "action_type": e.get("action_type"),
            "semantic_kind": semantic.get("semantic_kind"),
            "summary": semantic.get("summary") or scene.get("summary"),
            "semantic_delta_hash": e.get("semantic_delta_hash"),
            "source": e.get("source"),
            "state_hash": e.get("after_state_hash"),
            "scene_path": scene.get("source_artifact_path"),
            "scene_sha256": scene.get("source_artifact_hash"),
            "gate_authorized": bool(e.get("gate_authorization_hash")),
            "invariant_checked": bool(e.get("semantic_invariant_report_hash")),
            "migration_provenance": e.get("migration_provenance"),
        })
    actors = [{"id": k, "location": v.get("location"), "condition": v.get("condition"), "active_plan": v.get("active_plan")} for k, v in sorted(state.get("actors", {}).items())]
    objects = [{"id": k, "holder": v.get("holder"), "location": v.get("location"), "condition": v.get("condition")} for k, v in sorted(state.get("world_truth", {}).get("objects", {}).items())]
    gates = (head.get("gate_bundle") or {}).get("gates", [])
    quality_path = store.root / "benchmarks/author-quality-hidden/baseline-report.json"
    quality = json.loads(quality_path.read_text()) if quality_path.is_file() else {"status": "missing"}
    try:
        from .author_feedback import feedback_status as _feedback_status
        quality = {
            **quality,
            "author_feedback_ledger": {
                k: _feedback_status(store).get(k)
                for k in ("status", "event_count", "explicit_count", "errors")
            },
        }
    except Exception as exc:
        quality = {**quality, "author_feedback_ledger": {"status": "unavailable", "error": str(exc)}}
    try:
        quality = {**quality, "production_telemetry": production_quality_telemetry(store.root)}
    except Exception:
        pass
    source = {
        "state_hash": state.get("state_hash"),
        "event_head": state.get("events_head"),
        "event_count": len(events),
        "runtime_head_hash": head.get("head_hash"),
    }
    if readiness is None:
        from .project_readiness import project_readiness_report
        readiness = project_readiness_report(adapter, workbench_source=source)
    commands = readiness["commands"]["commands"]
    from .author_resume import build_resume_card
    from .scene_studio import studio_status
    resume = build_resume_card(adapter, state=state, head=head, readiness=readiness, events=events)
    studio = studio_status(adapter)
    report = {
        "schema": "minis.author-workbench-report.v2",
        "generated_at": now_iso(),
        "source": source,
        "freshness": {"status": "fresh", "stale": False, "errors": []},
        "resume": resume,
        "scene_studio": studio,
        "readiness": readiness,
        "health": base,
        "head": head,
        "timeline": timeline,
        "actors": actors,
        "objects": objects,
        "threads": state.get("threads", {}),
        "gates": gates,
        "semantic_invariants": inspect_state(state),
        "quality": quality,
        "commands": commands,
        "actions": {
            "write_policy": "no_direct_canonical_writes",
            "allowed_request_kinds": [
                "create_candidate", "request_revision", "request_approval",
                "request_override", "request_branch", "request_promotion",
            ],
            "executor": "production candidate bridge / ProjectRuntimeAdapter; separate from UI",
            "enabled": readiness["ready_for_commands"] and not resume.get("frozen"),
            "decision_actions": {
                "record_author_decision": "author_workbench.record_author_decision_action",
                "production_cli": "python -m novel_judge.production_decision_cli",
                "resume": "python -m novel_judge.cli resume <project-root>",
                "scene_studio": "python -m novel_judge.cli scenes <project-root>",
            },
        },
    }
    report["report_hash"] = sha256_json(report)
    return report


def create_command_request(adapter: Any, *, kind: str, payload: dict[str, Any], author_id: str, reason: str) -> dict[str, Any]:
    from .project_readiness import project_readiness_report
    allowed = {
        "create_candidate", "request_revision", "request_approval",
        "request_override", "request_branch", "request_promotion",
    }
    if kind not in allowed:
        raise ValueError("unsupported controlled command kind")
    readiness = project_readiness_report(adapter)
    if not readiness.get("ready_for_commands"):
        raise RuntimeError("author commands are blocked by project readiness: " + ",".join(readiness.get("command_blockers", [])))
    state = adapter.store.load_state()
    from .command_executor import make_author_command, write_author_command
    cmd = make_author_command(
        kind=kind, author_id=author_id, reason=reason,
        source_state_hash=state.get("state_hash"), source_event_head=state.get("events_head"),
        payload=payload,
    )
    cmd = write_author_command(adapter.store, cmd)
    return {
        **cmd,
        "path": str((adapter.store.base / "commands" / f"{cmd['command_id']}.json").relative_to(adapter.store.root)),
    }


def record_author_decision_action(
    adapter: Any, *, decision: str, candidate_hash: str,
    author_id: str = "author", reason: str | None = None,
    reason_codes: list[str] | None = None, turn_id: str | None = None,
    scene_id: str | None = None, revision_round: int | None = None,
    confidence: str = "high", reluctant_accept: bool = False,
) -> dict[str, Any]:
    """Workbench-facing AUTHOR_DECISION writer. Never commits canon by itself."""
    from .author_decision import record_author_decision
    from .author_feedback import feedback_status
    state = adapter.store.load_state() or {}
    codes = list(reason_codes or [])
    if decision == "accept" and not codes:
        codes = ["other"]
    report = record_author_decision(
        adapter.store, decision=decision, author_id=author_id, candidate_hash=candidate_hash,
        source_state_hash=str(state.get("state_hash")), source_event_head=state.get("events_head"),
        turn_id=turn_id, scene_id=scene_id or turn_id, reason_codes=codes, reason=reason,
        revision_round=revision_round, confidence=confidence, reluctant_accept=reluctant_accept,
        provenance={"source": "author_workbench"},
    )
    status = feedback_status(adapter.store)
    return {
        "ok": True,
        "decision": decision,
        "event_id": report["event"]["event_id"],
        "explicit_count": status.get("explicit_count"),
        "authority_layer": "AUTHOR_DECISION",
        "report_hash": report.get("report_hash"),
    }
