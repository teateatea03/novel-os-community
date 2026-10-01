from __future__ import annotations

"""Rebuild all disposable author-facing surfaces from canonical production data."""

from pathlib import Path
from typing import Any

from .author_workbench import build_workbench_report
from .author_workbench_html import render_workbench_html
from .canonical import now_iso, sha256_json
from .graph_projector import rebuild_projection
from .longform_projector import _atomic_text, project_longform_markdown
from .project_readiness import project_readiness_report
from .production_inputs import refresh_production_writing_inputs


def refresh_production_projections(adapter: Any) -> dict[str, Any]:
    graph = rebuild_projection(adapter.store, adapter.project_root / "graphify-out" / "interactive")
    longform = project_longform_markdown(adapter.store, adapter.project_root)
    writing_inputs = refresh_production_writing_inputs(adapter)
    from .author_quality_eval import refresh_quality_evaluation
    quality = refresh_quality_evaluation(adapter)
    state = adapter.store.load_state() or {}; events = adapter.store.read_events()
    source = {"state_hash": state.get("state_hash"), "event_head": state.get("events_head"),
              "event_count": len(events),
              "runtime_head_hash": adapter.store._read_json(adapter.runtime_head_path, {}).get("head_hash")}
    readiness = project_readiness_report(adapter, workbench_source=source, kernel_report={"status": "pass", "source": "post_commit_authority"})
    workbench = build_workbench_report(adapter, readiness=readiness)
    workbench_dir = adapter.project_root / "workbench"; workbench_dir.mkdir(parents=True, exist_ok=True)
    adapter.store._atomic_json(workbench_dir / "report.json", workbench)
    _atomic_text(workbench_dir / "index.html", render_workbench_html(workbench))
    # The report was built after Graph/long-form refresh and with its own
    # source tuple treated as the just-generated workbench source. Reuse that
    # deep readiness computation instead of replaying the full history twice.
    readiness = workbench["readiness"]
    readiness_dir = adapter.store.base / "readiness"; readiness_dir.mkdir(parents=True, exist_ok=True)
    adapter.store._atomic_json(readiness_dir / "report.json", readiness)
    result = {"schema": "minis.production-projection-refresh.v1", "generated_at": now_iso(),
              "source": readiness.get("source"), "graph": graph, "longform": longform, "writing_inputs": writing_inputs,
              "quality": {"path": str(adapter.project_root / "benchmarks" / "author-quality-hidden" / "baseline-report.json"),
                          "report_hash": quality.get("report_hash"), "explicit_author_pass_at_1": quality.get("metrics", {}).get("explicit_author_pass_at_1")},
              "workbench": {"path": str(workbench_dir / "index.html"),
                            "report_path": str(workbench_dir / "report.json"),
                            "report_hash": workbench.get("report_hash")},
              "readiness": {"path": str(readiness_dir / "report.json"), "status": readiness.get("status"),
                            "ready_for_generation": readiness.get("ready_for_generation"),
                            "ready_for_commands": readiness.get("ready_for_commands"),
                            "report_hash": readiness.get("report_hash")}}
    result["refresh_hash"] = sha256_json(result)
    adapter.store._atomic_json(adapter.store.base / "projection-refresh.json", result)
    return result
