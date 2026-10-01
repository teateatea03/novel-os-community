from __future__ import annotations

"""Project-level readiness: kernel health is necessary, never sufficient."""

import json
from pathlib import Path
from typing import Any

from .author_quality_eval import production_quality_telemetry, refresh_quality_evaluation
from .canonical import now_iso, sha256_json
from .longform_projector import projection_status
from .memory import memory_health
from .semantic_invariants import inspect_state

READINESS_SCHEMA = "minis.project-readiness-report.v1"
LEGACY_UNBOUND_SURFACES = (
    "reader-ledger.md", "knowledge-matrix.md", "workflow-state.json", "graphify-out/graph.json",
)


def _json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def _workbench_freshness(adapter: Any, source_override: dict[str, Any] | None = None) -> dict[str, Any]:
    state = adapter.store.load_state() or {}; events = adapter.store.read_events()
    head = adapter.store._read_json(adapter.runtime_head_path, {})
    path = adapter.project_root / "workbench" / "report.json"
    report = {"source": source_override} if source_override is not None else _json(path, {})
    source = (report or {}).get("source", {})
    errors = []
    checks = {
        "state_hash": (source.get("state_hash"), state.get("state_hash")),
        "event_head": (source.get("event_head"), state.get("events_head")),
        "event_count": (source.get("event_count"), len(events)),
        "runtime_head_hash": (source.get("runtime_head_hash"), head.get("head_hash")),
    }
    for key, (actual, expected) in checks.items():
        if actual != expected: errors.append(f"{key}_stale")
    if source_override is None and not path.is_file(): errors.insert(0, "missing_workbench_report")
    return {"status": "pass" if not errors else "stale", "stale": bool(errors),
            "errors": errors, "path": str(path), "source": source, "expected": {k: v[1] for k, v in checks.items()}}


def _graph_freshness(adapter: Any) -> dict[str, Any]:
    events = adapter.store.read_events(); expected = sha256_json(events)
    path = adapter.project_root / "graphify-out" / "interactive" / f"{adapter.session_id}-{adapter.branch_id}.json"
    graph = _json(path, {})
    actual = ((graph or {}).get("graph") or {}).get("source_hash")
    errors = []
    if not path.is_file(): errors.append("missing_graph_projection")
    if actual != expected: errors.append("events_hash_stale")
    return {"status": "pass" if not errors else "stale", "stale": bool(errors), "errors": errors,
            "path": str(path), "source_events_hash": actual, "expected_events_hash": expected}


def _memory_readiness(adapter: Any, state: dict[str, Any]) -> dict[str, Any]:
    from .production_inputs import production_writing_inputs_status
    status = production_writing_inputs_status(adapter)
    episode_count=status.get("episode_count",0);actor_count=status.get("actor_count",0)
    event_count=len(adapter.store.read_events())
    empty_bad=actor_count>0 and episode_count==0 and event_count>0
    bootstrap=event_count==0
    return {"status":"bootstrap" if bootstrap else ("unexpectedly_empty" if empty_bad else status["status"]),
            "stale":empty_bad or (status.get("stale",False) and not bootstrap),
            "bootstrap": bootstrap,
            "episodes":episode_count, "reflections":0,
            "actors":actor_count, "projection":status,
            "reason": None if bootstrap else ("event-derived production memory missing or stale" if empty_bad or status.get("status")!="pass" else None)}


def _context_readiness(adapter: Any) -> dict[str, Any]:
    from .production_inputs import production_writing_inputs_status
    status=production_writing_inputs_status(adapter)
    ok=status.get("status")=="pass" and status.get("context_count")==status.get("actor_count")
    return {"status":"pass" if ok else "stale", "stale":not ok,
            "context_count":status.get("context_count",0), "actor_count":status.get("actor_count",0),
            "projection":status}


def _storylet_readiness(adapter: Any, state: dict[str, Any]) -> dict[str, Any]:
    from .production_inputs import production_writing_inputs_status
    status=production_writing_inputs_status(adapter);ok=status.get("status")=="pass"
    return {"status":"pass" if ok else "unproven", "stale":not ok,
            "active_count":status.get("storylet_count",0), "blocking":False,
            "projection":status, "reason":None if ok else "production storylet availability projection missing or stale"}


def _command_readiness(adapter: Any) -> dict[str, Any]:
    from .command_executor import author_command_health, load_author_command
    state = adapter.store.load_state() or {}; root = adapter.store.base / "commands"; rows = []
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            try: value = load_author_command(adapter.store, path.stem, persist_migration=False)
            except Exception:
                rows.append({"command_id": path.stem, "kind": None, "status": "incompatible", "stale": False,
                             "path": str(path.relative_to(adapter.project_root))}); continue
            request = value.get("request", {})
            status = value.get("status")
            stale = status in {"pending", "claimed", "validating_source", "candidate_created", "gates_pending", "authorized"} and request.get("source_state_hash") != state.get("state_hash")
            rows.append({"command_id": value.get("command_id"), "kind": value.get("kind"), "status": status,
                         "source_state_hash": request.get("source_state_hash"), "stale": stale,
                         "path": str(path.relative_to(adapter.project_root))})
    health = author_command_health(adapter.store)
    pending = [x for x in rows if x.get("status") in {"pending", "claimed", "validating_source", "candidate_created", "gates_pending", "authorized"}]
    stale = [x for x in pending if x["stale"]]
    incompatible = [x for x in rows if x.get("status") == "incompatible"]
    status = "incompatible" if incompatible else ("stale_pending" if stale else ("pending" if pending else "pass"))
    return {"status": status, "blocking": bool(pending or incompatible), "pending_count": len(pending),
            "stale_pending_count": len(stale), "incompatible_count": len(incompatible), "health": health, "commands": rows}


def _quality_readiness(adapter: Any) -> dict[str, Any]:
    telemetry = production_quality_telemetry(adapter.project_root)
    state = adapter.store.load_state() or {}
    path = adapter.project_root / "benchmarks" / "author-quality-hidden" / "baseline-report.json"
    report = _json(path, {}) or {}
    covered = telemetry.get("coverage_last_turn")
    current = state.get("last_turn_id")
    source_stale = report.get("source_state_hash") != state.get("state_hash") or report.get("source_event_head") != state.get("events_head")
    partial = bool(current and covered != current) or source_stale
    explicit_count = int(telemetry.get("explicit_feedback_count", 0))
    typed_activated = (adapter.authority_record() or {}).get("typed_semantic_events_activated_at")
    after_activation = [e for e in adapter.store.read_events()
                        if e.get("verdict") in {"allow", "allow_with_cost", "partial", "meta"}
                        and typed_activated and str(e.get("created_at") or "") >= str(typed_activated)]
    typed_errors = []
    if after_activation:
        from .semantic_events import validate_semantic_delta
        for event in after_activation:
            try: validate_semantic_delta(event.get("semantic_delta"), event.get("operations", []))
            except (TypeError, ValueError): typed_errors.append(str(event.get("event_id")))
    typed_status = "pass" if after_activation and not typed_errors else ("awaiting_first_post_activation_event" if not after_activation else "fail")
    return {"status": "partial_coverage" if partial else ("baseline_no_explicit_feedback" if explicit_count == 0 or typed_status != "pass" else "pass"),
            "blocking": False, "source_state_hash": state.get("state_hash"),
            "coverage_last_turn": covered, "current_turn": current,
            "coverage_gap": partial, "explicit_feedback_count": explicit_count,
            "explicit_author_pass_at_1": telemetry.get("explicit_author_pass_at_1"),
            "workflow_proxy_separated": True, "typed_semantic_events": {"status": typed_status,
                "activated_at": typed_activated, "post_activation_event_count": len(after_activation),
                "invalid_event_ids": typed_errors}, "telemetry": telemetry,
            "evaluation_path": str(path), "evaluation_report_hash": report.get("report_hash")}


def _legacy_surfaces(adapter: Any) -> dict[str, Any]:
    rows = []
    for name in LEGACY_UNBOUND_SURFACES:
        path = adapter.project_root / name
        if path.exists(): rows.append({"path": name, "status": "legacy_unbound_excluded_from_current_context"})
    return {"status": "excluded" if rows else "not_present", "blocking": False, "surfaces": rows,
            "policy": "unbound legacy surfaces must not be loaded as current context"}


def project_readiness_report(adapter: Any, *, workbench_source: dict[str, Any] | None = None,
                             kernel_report: dict[str, Any] | None = None) -> dict[str, Any]:
    state = adapter.store.load_state() or {}
    core = kernel_report if kernel_report is not None else adapter.status()
    longform = projection_status(adapter.store, adapter.project_root)
    graph = _graph_freshness(adapter)
    workbench = _workbench_freshness(adapter, workbench_source)
    memory = _memory_readiness(adapter, state)
    context = _context_readiness(adapter)
    storylets = _storylet_readiness(adapter, state)
    commands = _command_readiness(adapter)
    quality = _quality_readiness(adapter)
    debt = inspect_state(state)
    legacy = _legacy_surfaces(adapter)
    generation_blockers = []
    command_blockers = []
    if core.get("status") != "pass":
        generation_blockers.append("KERNEL_CONFORMANCE_FAILED"); command_blockers.append("KERNEL_CONFORMANCE_FAILED")
    if longform.get("stale"): generation_blockers.append("STALE_LONGFORM_PROJECTION")
    if graph.get("stale"): generation_blockers.append("STALE_GRAPH_PROJECTION")
    if memory.get("stale"): generation_blockers.append("UNEXPECTEDLY_EMPTY_OR_STALE_PRODUCTION_MEMORY")
    if context.get("stale") and not memory.get("bootstrap"): generation_blockers.append("STALE_OR_MISSING_CONTEXT_PACK")
    if workbench.get("stale"): command_blockers.append("STALE_WORKBENCH")
    if commands.get("blocking"): command_blockers.append("PENDING_AUTHOR_COMMAND")
    freeze_path = Path(adapter.project_root) / "PROJECT-FROZEN.json"
    if freeze_path.is_file():
        freeze_status = str((_json(freeze_path, {}) or {}).get("status") or "").upper()
        if freeze_status == "FROZEN":
            generation_blockers.append("PROJECT_FROZEN")
            command_blockers.append("PROJECT_FROZEN")
    warnings = []
    if memory.get("bootstrap"): warnings.append("BOOTSTRAP_FIRST_SCENE")
    if storylets.get("status") != "pass": warnings.append("STORYLET_AVAILABILITY_UNPROVEN")

    if quality.get("status") != "pass": warnings.append("QUALITY_TELEMETRY_PARTIAL_COVERAGE")
    if debt.get("issues"): warnings.append("SEMANTIC_MIGRATION_DEBT_PRESENT")
    if legacy.get("surfaces"): warnings.append("LEGACY_UNBOUND_SURFACES_EXCLUDED")
    ready_generation = not generation_blockers; ready_commands = not command_blockers
    report = {"schema": READINESS_SCHEMA, "generated_at": now_iso(),
              "source": {"state_hash": state.get("state_hash"), "event_head": state.get("events_head"),
                         "last_turn_id": state.get("last_turn_id"), "revision": state.get("revision"),
                         "event_count": len(adapter.store.read_events())},
              "kernel": core, "projections": {"longform": longform, "graph": graph, "workbench": workbench,
                                                "legacy_unbound": legacy},
              "writing_inputs": {"memory": memory, "context": context, "storylets": storylets},
              "commands": commands, "quality": quality,
              "semantic_debt": {"counts": debt.get("counts", {}), "issue_count": len(debt.get("issues", [])),
                                  "report_hash": debt.get("report_hash")},
              "generation_blockers": generation_blockers, "command_blockers": command_blockers,
              "warnings": warnings, "ready_for_generation": ready_generation,
              "ready_for_commands": ready_commands,
              "status": "ready" if ready_generation and ready_commands else "blocked"}
    report["report_hash"] = sha256_json(report)
    return report
