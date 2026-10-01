from __future__ import annotations

"""Deterministic runtime observability; no model is required to self-report."""

from collections import Counter
from typing import Any
from .canonical import sha256_json


def runtime_metrics(turns: list[dict[str, Any]], *, model_tasks: list[dict[str, Any]] | None = None,
                    memory_queries: list[dict[str, Any]] | None = None,
                    storylet_reports: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    verdicts = Counter(str(x.get("verdict", "unknown")) for x in turns)
    gate_codes = Counter()
    repairs = 0
    for turn in turns:
        gate = turn.get("narrative_gate") or {}
        for item in gate.get("errors", []):
            gate_codes[str(item.get("code", item)) if isinstance(item, dict) else str(item)] += 1
        repairs += int(turn.get("repair_count", 0) or 0)
    tasks = model_tasks or []; task_counts = Counter(str(x.get("task", "unknown")) for x in tasks)
    stale_tasks = sum(any(e.get("code") == "MODEL_RESULT_STALE_TASK" for e in x.get("errors", []) if isinstance(e, dict)) for x in tasks)
    memories = memory_queries or []; hits = sum(int(x.get("hit_count", len(x.get("memories", [])))) for x in memories)
    activities = model_tasks or []; activity_counts = Counter(str(x.get("status", "unknown")) for x in activities if x.get("schema") == "minis.model-activity.v1")
    report = {"schema": "minis.runtime-metrics.v2", "turn_count": len(turns), "verdicts": dict(verdicts),
              "gate_taxonomy": dict(gate_codes), "repair_count": repairs, "model_tasks": dict(task_counts),
              "stale_model_results": stale_tasks, "model_activity_status": dict(activity_counts), "memory_queries": len(memories), "memory_hits": hits,
              "storylet_reports": len(storylet_reports or []),
              "storylet_starvation": sum(bool(x.get("starved")) for x in (storylet_reports or []))}
    report["report_hash"] = sha256_json(report)
    return report
