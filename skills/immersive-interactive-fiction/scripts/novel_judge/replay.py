from __future__ import annotations

from typing import Any

from .engine import replay_events


def replay(initial_state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    return replay_events(initial_state, events)


def verify_replay(initial_state: dict[str, Any], events: list[dict[str, Any]], expected_hash: str | None = None) -> dict[str, Any]:
    state = replay(initial_state, events)
    return {"ok": expected_hash is None or state.get("state_hash") == expected_hash,
            "state_hash": state.get("state_hash"), "expected_hash": expected_hash,
            "event_count": len(events)}
