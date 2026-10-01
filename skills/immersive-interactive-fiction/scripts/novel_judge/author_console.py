from __future__ import annotations

"""Small deterministic author console report for branch/runtime health."""

from pathlib import Path
from typing import Any
import json

from .branches import branch_affected
from .event_log import inspect_jsonl, load_log_manifest, verify_event_log_integrity
from .longform_projector import projection_status
from .memory import memory_health
from .model_activities import model_activity_health
from .random_events import random_event_health
from .runtime_versioning import replay_compatibility_report


def author_console_report(store: Any, *, parent_store: Any | None = None, project_root: str | Path | None = None) -> dict[str, Any]:
    state = store.load_state(); manifest = store.load_manifest() or {}; journal = store.load_journal()
    events = inspect_jsonl(store.events_path)
    actor_memory = {}
    if state:
        for actor_id in sorted(state.get("actors", {})): actor_memory[actor_id] = memory_health(state, actor_id)
    report = {"schema": "minis.author-console-report.v1", "project_id": store.project_id, "session_id": store.session_id,
              "branch_id": store.branch_id, "head": {"state_hash": (state or {}).get("state_hash"), "revision": (state or {}).get("revision"),
              "event_id": manifest.get("head_event_id"), "manifest_hash": manifest.get("head_state_hash")},
              "head_consistent": bool(state) and manifest.get("head_state_hash") in {None, state.get("state_hash")},
              "integrity_profile": {"level": "local-integrity", "malicious_full_write_resistance": "not_claimed", "external_anchor": False},
              "journal": {"pending": journal is not None, "phase": (journal or {}).get("phase")},
              "event_log": {"status": events["status"], "active_records": len(events["records"]), "manifest": load_log_manifest(store), "integrity": verify_event_log_integrity(store)},
              "replay_compatibility": replay_compatibility_report(store.read_events()) if events["status"] == "clean" else {"status": "blocked", "errors": [{"code": "EVENT_LOG_CORRUPTION"}]},
              "model_activities": model_activity_health(store),
              "random_events": random_event_health(store),
              "projection": projection_status(store, project_root or store.root) if store.namespace == "runtime" else {"status": "not_applicable", "stale": False},
              "memory": actor_memory}
    if parent_store is not None and state is not None and parent_store.load_state() is not None:
        report["branch_diff"] = branch_affected(parent_store.load_state(), state)
    blockers = []
    if not report["head_consistent"]: blockers.append("HEAD_STATE_MISMATCH")
    if report["journal"]["pending"]: blockers.append("PENDING_TRANSACTION_JOURNAL")
    if report["event_log"]["status"] != "clean": blockers.append("EVENT_LOG_CORRUPTION")
    if report["event_log"].get("integrity", {}).get("status") != "pass": blockers.append("EVENT_HISTORY_INTEGRITY_FAILURE")
    if report["replay_compatibility"].get("status") != "pass": blockers.append("REPLAY_CONTRACT_INCOMPATIBLE")
    if report["model_activities"].get("pending"): blockers.append("PENDING_MODEL_ACTIVITY")
    if report["random_events"].get("malformed_audit_records"): blockers.append("RANDOM_EVENT_AUDIT_INTEGRITY_WARNING")
    if report["projection"].get("stale"): blockers.append("STALE_LONGFORM_PROJECTION")
    report["blockers"] = blockers; report["status"] = "pass" if not blockers else "blocked"
    return report


def render_author_console_markdown(report: dict[str, Any]) -> str:
    lines = ["# Novel OS Author Console", "", f"- Status：**{report.get('status')}**", f"- Project／Session／Branch：`{report.get('project_id')}`／`{report.get('session_id')}`／`{report.get('branch_id')}`",
             f"- Revision：{report.get('head', {}).get('revision')}", f"- State hash：`{report.get('head', {}).get('state_hash')}`",
             f"- Event log：{report.get('event_log', {}).get('status')}", f"- Replay contract：{report.get('replay_compatibility', {}).get('status')}", f"- Model activities：{report.get('model_activities', {}).get('status')}", f"- Random events：{report.get('random_events', {}).get('mode')}（non-canonical suggestions: {report.get('random_events', {}).get('noncanonical_audit_records')}）", f"- Projection：{report.get('projection', {}).get('status')}", "", "## Blockers"]
    blockers = report.get("blockers", []); lines.extend(f"- {x}" for x in blockers)
    if not blockers: lines.append("- 無。")
    if report.get("branch_diff"):
        lines += ["", "## Branch Diff", "", f"- Changes：{report['branch_diff'].get('change_count')}", f"- Entities：{', '.join(report['branch_diff'].get('entities', []))}"]
    return "\n".join(lines) + "\n"
