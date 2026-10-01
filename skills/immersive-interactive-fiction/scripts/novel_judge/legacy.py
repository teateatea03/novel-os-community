"""Compatibility adapters for prototype hosts and legacy v1 states."""
from __future__ import annotations
from typing import Any
from .canonical import canonical_json, sha256_json, state_hash
from .importers.legacy import import_legacy_state, import_markdown_baseline
from .compat import judge_action

def replay(initial_state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    from .engine import replay_events
    return replay_events(initial_state, events)

__all__ = ["canonical_json", "sha256_json", "state_hash", "judge_action", "replay", "import_legacy_state", "import_markdown_baseline"]
