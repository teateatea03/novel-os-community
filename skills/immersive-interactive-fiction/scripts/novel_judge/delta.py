from __future__ import annotations

from typing import Any

from .canonical import deep_copy, stable_id
from .contracts import DELTA_SCHEMA, validate_delta
from .errors import DELTA_PATH_FORBIDDEN, JudgeError, PLAYER_SOVEREIGNTY, PRECONDITION_FAILED
from .state import actor

# Only these domains may be changed by a candidate transition. Structural
# identity, hashes, revision and event pointers belong to the commit layer.
ALLOWED_PREFIXES = (
    "/clock/", "/actors/", "/world_truth/objects/", "/world_truth/events/",
    "/world_truth/locations/", "/world_public/", "/relations/", "/knowledge/player/",
    "/knowledge/npcs/", "/knowledge/reader/", "/reality/", "/storylets/", "/clocks/",
    "/threads/", "/plans/", "/memory/",
)
FORBIDDEN_PREFIXES = (
    "/schema", "/project_id", "/session_id", "/branch_id", "/canon_scope",
    "/revision", "/state_hash", "/events_head", "/last_turn_id", "/metadata",
    "/knowledge/truth", "/world_truth/rules",
)


def _tokens(path: str) -> list[str]:
    if not isinstance(path, str) or not path.startswith("/"):
        raise JudgeError(DELTA_PATH_FORBIDDEN, "delta path must be a JSON pointer", details={"path": path})
    return [x.replace("~1", "/").replace("~0", "~") for x in path[1:].split("/") if x != ""]


def validate_operation(op: dict[str, Any], *, source: str = "system") -> None:
    if not isinstance(op, dict) or op.get("op") not in {"add", "replace", "remove"}:
        raise JudgeError(DELTA_PATH_FORBIDDEN, "unsupported delta operation", details={"operation": op})
    path = op.get("path", "")
    if any(path == p or path.startswith(p + "/") for p in FORBIDDEN_PREFIXES):
        raise JudgeError(DELTA_PATH_FORBIDDEN, "delta cannot modify protected state metadata", details={"path": path})
    if not any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise JudgeError(DELTA_PATH_FORBIDDEN, "delta path is outside allowed domains", details={"path": path})
    # A model/NPC proposal cannot modify the player's authoritative action or
    # hidden truth. The player may only be changed by explicit player input.
    parts = _tokens(path)
    if source in {"model", "npc_plan", "world_tick"} and len(parts) >= 2:
        if parts[0] == "actors" and parts[1] in {"player", "user"}:
            raise JudgeError(PLAYER_SOVEREIGNTY, "non-player proposal cannot mutate player state", details={"path": path})
        if parts[:2] == ["knowledge", "truth"]:
            raise JudgeError(DELTA_PATH_FORBIDDEN, "proposal cannot mutate canonical truth facts", details={"path": path})
        if parts and parts[0] == "memory":
            raise JudgeError(DELTA_PATH_FORBIDDEN, "model/NPC/world proposals cannot directly write durable memory", details={"path": path})
    if op["op"] != "remove" and "value" not in op:
        raise JudgeError(DELTA_PATH_FORBIDDEN, "add/replace requires value", details={"path": path})


def validate_delta_paths(delta: dict[str, Any], *, source: str | None = None) -> None:
    source = source or delta.get("source", "system")
    for op in delta.get("operations", []):
        validate_operation(op, source=source)


def _resolve_parent(root: Any, tokens: list[str]) -> tuple[Any, str]:
    if not tokens:
        raise JudgeError(DELTA_PATH_FORBIDDEN, "root replacement is forbidden")
    cur = root
    for token in tokens[:-1]:
        if isinstance(cur, list):
            try:
                cur = cur[int(token)]
            except (ValueError, IndexError) as exc:
                raise JudgeError(DELTA_PATH_FORBIDDEN, "list path does not exist", details={"token": token}) from exc
        elif isinstance(cur, dict) and token in cur:
            cur = cur[token]
        else:
            raise JudgeError(DELTA_PATH_FORBIDDEN, "delta parent path does not exist", details={"token": token})
    return cur, tokens[-1]


def apply_operations(state: dict[str, Any], operations: list[dict[str, Any]], *, source: str = "system") -> dict[str, Any]:
    result = deep_copy(state)
    for op in operations:
        validate_operation(op, source=source)
        parent, key = _resolve_parent(result, _tokens(op["path"]))
        if isinstance(parent, list):
            if key == "-" and op["op"] == "add":
                parent.append(deep_copy(op["value"]))
            else:
                try: index = int(key)
                except ValueError as exc: raise JudgeError(DELTA_PATH_FORBIDDEN, "invalid list index") from exc
                if op["op"] == "remove": parent.pop(index)
                elif op["op"] in {"add", "replace"}:
                    if op["op"] == "add": parent.insert(index, deep_copy(op["value"]))
                    else: parent[index] = deep_copy(op["value"])
            continue
        if not isinstance(parent, dict):
            raise JudgeError(DELTA_PATH_FORBIDDEN, "delta parent is not a container")
        if op["op"] == "remove":
            if key not in parent: raise JudgeError(DELTA_PATH_FORBIDDEN, "remove target does not exist", details={"path": op["path"]})
            del parent[key]
        elif op["op"] == "replace":
            if key not in parent: raise JudgeError(DELTA_PATH_FORBIDDEN, "replace target does not exist", details={"path": op["path"]})
            parent[key] = deep_copy(op["value"])
        else:
            if key in parent: raise JudgeError(DELTA_PATH_FORBIDDEN, "add target already exists", details={"path": op["path"]})
            parent[key] = deep_copy(op["value"])
    return result


def propose_delta(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    """Produce a deterministic, bounded candidate delta from a validated intent."""
    from .preflight import preflight_intent
    preflight_intent(state, intent)
    actor_id = intent["actor_id"]
    typ = intent["type"]
    params = intent.get("parameters", {})
    targets = intent.get("targets", [])
    operations: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    delayed_effects: list[dict[str, Any]] = []
    def target(name: str = "target") -> str | None:
        return params.get(name) or (targets[0] if targets else None)
    if typ == "move":
        operations.append({"op": "replace", "path": f"/actors/{actor_id}/location", "value": target()})
    elif typ == "move_short":
        operations.append({"op": "replace", "path": f"/actors/{actor_id}/location", "value": target()})
        costs.append({"actor_id": actor_id, "action_type": typ, "cost": {"movement": "short", "fatigue": "increases"}})
    elif typ == "take":
        oid = target("object_id") or target()
        if typ == "take":
            operations += [
                {"op": "replace", "path": f"/world_truth/objects/{oid}/holder", "value": actor_id},
                {"op": "replace", "path": f"/world_truth/objects/{oid}/location", "value": None},
                {"op": "replace" if "inventory" in actor(state, actor_id) else "add", "path": f"/actors/{actor_id}/inventory", "value": list(actor(state, actor_id).get("inventory", [])) + ([oid] if oid not in actor(state, actor_id).get("inventory", []) else [])},
            ]
    elif typ == "drop":
        oid = target("object_id") or target()
        here = actor(state, actor_id).get("location")
        operations += [
            {"op": "replace", "path": f"/world_truth/objects/{oid}/holder", "value": None},
            {"op": "replace", "path": f"/world_truth/objects/{oid}/location", "value": here},
            {"op": "replace", "path": f"/actors/{actor_id}/inventory", "value": [x for x in actor(state, actor_id).get("inventory", []) if x != oid]},
        ]
    elif typ in {"open", "close"}:
        via = target("via") or target()
        here = actor(state, actor_id).get("location")
        value = typ == "open"
        operations.append({"op": "replace", "path": f"/world_truth/locations/{here}/connections/{via}/open", "value": value})
    elif typ == "wait":
        seconds = int(params.get("seconds", 60))
        old = int(state.get("clock", {}).get("tick", 0))
        operations.append({"op": "replace", "path": "/clock/tick", "value": old + seconds})
        delayed_effects.append({"kind": "world_tick_eligible", "after_seconds": seconds})
    elif typ == "rest_awake":
        seconds = int(params.get("seconds", 60))
        old = int(state.get("clock", {}).get("tick", 0))
        operations.append({"op": "replace", "path": "/clock/tick", "value": old + seconds})
        costs.append({"actor_id": actor_id, "action_type": typ, "cost": {"time": seconds, "cold_exposure": "may_increase", "sleep": "awake_rest"}})
    elif typ in {"observe", "observe_local", "inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment"}:
        # These actions are intentionally bounded: without an explicit
        # transition, they create only an event and cannot invent inventory,
        # safety, full counts, or movement across zones.
        if typ in {"inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment"}:
            costs.append({"actor_id": actor_id, "action_type": typ, "cost": {"attention": "local", "scope": "one_object"}})
        elif typ == "observe_local":
            costs.append({"actor_id": actor_id, "action_type": typ, "cost": {"attention": "local", "scope": "one_local_zone"}})
    elif typ == "hide":
        operations.append({"op": "replace", "path": f"/actors/{actor_id}/status/hidden", "value": True})
    elif typ == "promise":
        text = params.get("text")
        if not isinstance(text, str) or not text.strip():
            raise JudgeError(PRECONDITION_FAILED, "promise requires explicit text")
        commitments = list(actor(state, actor_id).get("commitments", []))
        commitments.append({"text": text, "turn_id": intent["turn_id"]})
        path = f"/actors/{actor_id}/commitments"
        operations.append({"op": "replace" if "commitments" in actor(state, actor_id) else "add", "path": path, "value": commitments})
    elif typ == "use":
        oid = target("object_id") or target()
        obj = state["world_truth"]["objects"][oid]
        for op in obj.get("use_effects", []): operations.append(deep_copy(op))
    if typ in {"world_tick", "npc_act", "scene_commit", "chapter_commit", "artifact_revision", "semantic_correction", "meta"}:
        for op in params.get("operations", []): operations.append(deep_copy(op))
    reality_rec = state.get("reality", {}).get("actors", {}).get(actor_id, {})
    action_cost = reality_rec.get("action_costs", {}).get(typ, {}) if isinstance(reality_rec, dict) else {}
    if action_cost:
        costs.append({"actor_id": actor_id, "action_type": typ, "cost": deep_copy(action_cost)})
    # observe, speak, ask, attempt and meta deliberately create an event but
    # do not invent a world mutation.
    delta = {
        "schema": DELTA_SCHEMA,
        "delta_id": stable_id("delta", state.get("state_hash"), intent["intent_id"], operations),
        "turn_id": intent["turn_id"],
        "source_intent_id": intent["intent_id"],
        "source": intent.get("source", "system"),
        "operations": operations,
        "costs": costs,
        "delayed_effects": delayed_effects,
        "preconditions": [],
        "candidate": bool(intent.get("model_generated") or intent.get("source") == "model"),
        "pre_state_hash": state.get("state_hash"),
    }
    validate_delta(delta); validate_delta_paths(delta, source=delta["source"])
    return delta
