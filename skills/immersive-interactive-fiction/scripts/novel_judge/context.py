from __future__ import annotations

from typing import Any

from .capacity import capacity_budget
from .canonical import deep_copy, sha256_json
from .epistemic import filter_private, visible_facts
from .reality import build_reality_card
from .memory import compile_memory_context
from .author_corrections import infer_project_root, attach_author_corrections


def build_context(state: dict[str, Any], *, audience: str = "reader", actor_id: str | None = None) -> dict[str, Any]:
    """Build a permission-first, reproducible context pack for rendering."""
    facts = visible_facts(state, audience=audience, actor_id=actor_id)
    context: dict[str, Any] = {
        "schema": "minis.interactive-context.v2", "audience": audience, "actor_id": actor_id,
        "clock": deep_copy(state.get("clock", {})), "facts": filter_private(facts),
        "world_public": filter_private(state.get("world_public", {})), "actors": {}, "objects": {},
        "relations": filter_private(state.get("relations", {})),
        "storylets": {"active": state.get("storylets", {}).get("active", [])},
        "threads": deep_copy(state.get("threads", {})), "excluded": [],
        "provenance": {"state_hash": state.get("state_hash"), "branch_id": state.get("branch_id"), "revision": state.get("revision")},
    }
    if actor_id and actor_id in state.get("actors", {}):
        actor = state["actors"][actor_id]
        here = actor.get("location")
        context["self"] = filter_private(actor)
        context["reality_card"] = build_reality_card(state, actor_id)
        context["cognitive_budget"] = capacity_budget(state, actor_id)
        memory_query = " ".join(str(x) for x in (actor.get("immediate_goal"), here) if x)
        context["memory_context"] = compile_memory_context(state, actor_id, query=memory_query, top_k=6)
        context["location"] = filter_private(state.get("world_truth", {}).get("locations", {}).get(here, {}))
        for aid, record in state.get("actors", {}).items():
            if aid == actor_id or record.get("location") == here:
                context["actors"][aid] = filter_private(record)
        for oid, obj in state.get("world_truth", {}).get("objects", {}).items():
            if obj.get("location") == here or obj.get("holder") == actor_id:
                context["objects"][oid] = filter_private(obj)
        context["excluded"].append("actors/knowledge, actors/secrets, object/use_effects")
    project_root = infer_project_root(state)
    character_ids = list(context.get("actors") or {})
    if actor_id:
        character_ids = list(dict.fromkeys([actor_id, *character_ids]))
    scene_kind = state.get("scene_kind") or (state.get("scene") or {}).get("kind")
    attach_author_corrections(
        context,
        project_root,
        character_ids=character_ids or None,
        scene_kind=scene_kind,
    )
    context["context_hash"] = sha256_json({k: v for k, v in context.items() if k != "context_hash"})
    return context


def build_context_pack(state: dict[str, Any], *, actor_id: str | None = None,
                       audience: str | None = None, permission: dict[str, Any] | None = None) -> dict[str, Any]:
    """Plan-level alias; permission is provenance metadata, not an override."""
    if audience is None:
        audience = "player" if actor_id in {"player", "user"} else "npc"
    result = build_context(state, audience=audience, actor_id=actor_id)
    if permission is not None:
        result["permission_report"] = deep_copy(permission)
        result["context_hash"] = sha256_json({k: v for k, v in result.items() if k != "context_hash"})
    return result
