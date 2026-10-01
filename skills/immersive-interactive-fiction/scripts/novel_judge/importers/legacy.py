from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..canonical import now_iso, refresh_state_hash, sha256_json
from ..state import empty_state


def import_legacy_state(legacy: dict[str, Any], *, project_id: str, session_id: str,
                        branch_id: str = "legacy-import-20260803") -> dict[str, Any]:
    """Convert the old interactive fixture without fabricating missing transitions."""
    session = legacy.get("session", {}); world = legacy.get("world", {})
    state = empty_state(project_id, session_id, branch_id, now=str(world.get("now", "")))
    state["canon_scope"] = session.get("canon_scope", "session")
    state["revision"] = int(session.get("turn", 0) or 0)
    loc = world.get("location", "unknown")
    state["world_truth"]["locations"][loc] = {"connections": {x: {"to": x, "open": True} for x in world.get("exits", [])}}
    for actor_id in [session.get("player_character", "player")]:
        state["actors"][actor_id] = {"kind": "player", "location": loc,
                                      "status": {"condition": legacy.get("player", {}).get("condition")},
                                      "commitments": legacy.get("player", {}).get("commitments", [])}
    for n in legacy.get("npcs", {}).get("characters", []):
        if not isinstance(n, dict) or not n.get("id"): continue
        state["actors"][n["id"]] = {"kind": "npc", "location": loc,
                                      "status": {}, "commitments": [],
                                      "goal": n.get("immediate_goal")}
    state["world_public"] = {"atmosphere": world.get("atmosphere"), "present": world.get("present", []),
                             "pressures": world.get("pressures", [])}
    state["threads"] = legacy.get("threads", state["threads"])
    state["metadata"].update({"imported_from": "legacy.interactive_state.v1", "imported_at": now_iso(),
                               "legacy_turn": session.get("turn", 0), "legacy_event_count": len(legacy.get("events", []))})
    state["metadata"]["source_hash"] = sha256_json(legacy)
    state["events_head"] = None
    return refresh_state_hash(state)


def import_markdown_baseline(project_root: str | Path, *, project_id: str,
                              session_id: str, branch_id: str = "legacy-import-20260803") -> dict[str, Any]:
    root = Path(project_root)
    current = root / "current-state.md"
    if not current.exists(): raise FileNotFoundError(current)
    text = current.read_text(encoding="utf-8")
    state = empty_state(project_id, session_id, branch_id)
    state["metadata"].update({"imported_from": str(current), "source_hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
                               "imported_at": now_iso(), "provenance_only": True,
                               "note": "Markdown baseline imported as provenance; no missing transitions fabricated."})
    return refresh_state_hash(state)
