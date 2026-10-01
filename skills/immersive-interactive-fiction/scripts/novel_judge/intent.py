from __future__ import annotations

import re
from typing import Any

from .canonical import new_id
from .capacity import capacity_budget, capacity_summary, is_ai_autonomous_protagonist
from .contracts import INTENT_SCHEMA, validate_intent
from .errors import JudgeError, SCHEMA_ERROR, MACRO_INTENT_REQUIRES_EXPANSION


def make_intent(actor_id: str, action_type: str, *, turn_id: str | None = None,
                targets: list[str] | None = None, parameters: dict[str, Any] | None = None,
                source: str = "player_input", raw_input: str | None = None,
                player_authored: bool | None = None, model_generated: bool = False,
                intent_id: str | None = None) -> dict[str, Any]:
    if player_authored is None:
        player_authored = source in {"player_input", "author"}
    intent = {
        "schema": INTENT_SCHEMA,
        "intent_id": intent_id or new_id("intent"),
        "turn_id": turn_id or new_id("turn"),
        "actor_id": actor_id,
        "source": source,
        "raw_input": raw_input,
        "type": action_type,
        "targets": list(targets or []),
        "parameters": dict(parameters or {}),
        "claimed_effects": [],
        "player_authored": bool(player_authored),
        "model_generated": bool(model_generated),
        "seed": None,
    }
    validate_intent(intent)
    return intent


def _first_target(text: str) -> str | None:
    match = re.search(r"(?:to|toward|towards|at|拿|取|放到|走到|前往|詢問|問)\s*[:：]?\s*([\w:.-]+)", text, re.I)
    return match.group(1) if match else None


def parse_player_text(actor_id: str, raw_input: str, *, turn_id: str | None = None) -> dict[str, Any]:
    text = raw_input.strip()
    low = text.lower()
    if not text:
        raise JudgeError(SCHEMA_ERROR, "player input is empty")
    if low in {"observe", "look", "look around", "觀察", "看看", "環顧"}:
        return make_intent(actor_id, "observe", turn_id=turn_id, raw_input=raw_input)
    if low in {"wait", "等待", "等一下", "休息"}:
        return make_intent(actor_id, "wait", turn_id=turn_id, raw_input=raw_input)
    if any(x in low for x in ("move ", "go ", "walk ", "走到", "前往", "移動到")):
        target = _first_target(text) or text.split()[-1]
        return make_intent(actor_id, "move", turn_id=turn_id, targets=[target], raw_input=raw_input)
    if any(x in low for x in ("take ", "get ", "pick up", "拿", "取")):
        target = _first_target(text) or text.split()[-1]
        return make_intent(actor_id, "take", turn_id=turn_id, targets=[target], raw_input=raw_input)
    if any(x in low for x in ("drop ", "放下", "放")):
        target = _first_target(text) or text.split()[-1]
        return make_intent(actor_id, "drop", turn_id=turn_id, targets=[target], raw_input=raw_input)
    if any(x in low for x in ("ask ", "詢問", "問")):
        return make_intent(actor_id, "ask", turn_id=turn_id, targets=[_first_target(text) or ""], parameters={"text": text}, raw_input=raw_input)
    return make_intent(actor_id, "speak", turn_id=turn_id, parameters={"text": text}, raw_input=raw_input)


def normalize_intent(value: str | dict[str, Any], actor_id: str | None = None, *, turn_id: str | None = None,
                     source: str = "player_input") -> dict[str, Any]:
    if isinstance(value, str):
        if not actor_id:
            raise JudgeError(SCHEMA_ERROR, "actor_id is required when normalizing text")
        return parse_player_text(actor_id, value, turn_id=turn_id)
    intent = dict(value)
    intent.setdefault("schema", INTENT_SCHEMA)
    intent.setdefault("turn_id", turn_id or new_id("turn"))
    intent.setdefault("source", source)
    intent.setdefault("targets", [])
    intent.setdefault("parameters", {})
    intent.setdefault("claimed_effects", [])
    intent.setdefault("player_authored", intent.get("source") in {"player_input", "author"})
    intent.setdefault("model_generated", intent.get("source") == "model")
    intent.setdefault("seed", None)
    # A stable intent id is derived from the semantic action when callers omit it.
    # This makes retries with the same turn id idempotent without relying on UUIDs.
    intent.setdefault("intent_id", "intent_" + __import__("hashlib").sha256(
        __import__("json").dumps({"turn_id": intent["turn_id"], "actor_id": intent.get("actor_id"),
                                  "type": intent.get("type"), "targets": intent.get("targets", []),
                                  "parameters": intent.get("parameters", {})},
                                 ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24])
    validate_intent(intent)
    return intent
