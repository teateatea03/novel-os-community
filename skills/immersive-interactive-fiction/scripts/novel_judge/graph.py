from __future__ import annotations
from typing import Any
from .graph_patch import build_graph_patch

def propose_patch(before: dict[str, Any], after: dict[str, Any], *, turn_id: str, event_id: str, branch_id: str) -> dict[str, Any]:
    return build_graph_patch(before, after, turn_id=turn_id, event_id=event_id, branch_id=branch_id)

def validate_patch(patch: dict[str, Any]) -> dict[str, Any]:
    required = {"schema", "patch_id", "turn_id", "event_id", "branch_id", "changes", "requires_promotion"}
    missing = sorted(required - set(patch))
    return {"ok": not missing and patch.get("schema") == "minis.graph-patch.v1", "missing": missing,
            "status": "pass" if not missing and patch.get("schema") == "minis.graph-patch.v1" else "fail"}
