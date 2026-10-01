from __future__ import annotations
from typing import Any
from .canonical import sha256_json
from .engine import replay_events

def synchronization_report(initial_state: dict[str, Any], events: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any]:
    replayed = replay_events(initial_state, events)
    return {"status": "pass" if replayed.get("state_hash") == current.get("state_hash") else "fail",
            "event_count": len(events), "replayed_state_hash": replayed.get("state_hash"),
            "current_state_hash": current.get("state_hash"),
            "hash_match": replayed.get("state_hash") == current.get("state_hash")}

def turn_metrics(turns: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for t in turns:
        k = str(t.get("verdict", "unknown")); counts[k] = counts.get(k, 0) + 1
    return {"turn_count": len(turns), "verdicts": counts,
            "hard_errors": sum(t.get("status") == "error" for t in turns),
            "report_hash": sha256_json({"turns": len(turns), "verdicts": counts})}
