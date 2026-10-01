from __future__ import annotations

"""Provider-neutral structured-output contracts for weak/local models."""

from typing import Any
from .model_tasks import TASK_SCHEMAS

TYPE_HINTS: dict[str, dict[str, str]] = {
    "intent_extract": {"type": "string", "targets": "array", "parameters": "object", "confidence": "number", "ambiguities": "array"},
    "npc_plan": {"actor_id": "string", "goal": "string", "action_type": "string", "targets": "array", "reason_fact_ids": "array"},
    "scene_manifest": {"scene_function": "string", "focal_change": "string", "beats": "array", "protected_unknowns": "array", "handoff_owner": "string"},
    "render": {"text": "string", "claimed_facts": "array", "action_manifest": "array", "player_actions": "array"},
    "repair": {"text": "string", "fixed_issue_ids": "array"},
    "blind_read": {"status": "string", "issues": "array", "summary": "string"},
}


def json_schema_for_task(task: str, *, task_hash: str | None = None) -> dict[str, Any]:
    if task not in TASK_SCHEMAS: raise ValueError(f"unsupported task: {task}")
    hints = TYPE_HINTS[task]
    properties: dict[str, Any] = {}
    for name in TASK_SCHEMAS[task]["required"]:
        typ = hints.get(name, "string")
        item: dict[str, Any] = {"type": typ}
        if typ == "array": item["items"] = {"type": "string"}
        if typ == "object": item["additionalProperties"] = False
        properties[name] = item
    if task == "intent_extract":
        properties["type"] = {"type": "string", "enum": ["observe", "move", "take", "drop", "ask", "speak", "wait", "open", "close", "use", "meta", "ambiguous_intent"]}
        properties["confidence"] = {"type": "number", "minimum": 0.0, "maximum": 1.0}
        properties["ambiguities"] = {"type": "array", "items": {"type": "string"}, "maxItems": 5}
    elif task == "blind_read":
        properties["status"] = {"type": "string", "enum": ["pass", "warn", "fail"]}
    elif task == "scene_manifest":
        properties["handoff_owner"] = {"type": "string", "minLength": 1}
        properties["beats"] = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    elif task == "render":
        properties["text"] = {"type": "string", "minLength": 1}
    elif task == "repair":
        properties["text"] = {"type": "string", "minLength": 1}
        properties["fixed_issue_ids"] = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    required = list(TASK_SCHEMAS[task]["required"])
    if task_hash is not None:
        properties["task_hash"] = {"type": "string", "const": task_hash}
        required.append("task_hash")
    return {"type": "object", "properties": properties,
            "required": required, "additionalProperties": False}


def adapter_contract(task: str, *, provider: str = "generic", task_hash: str | None = None) -> dict[str, Any]:
    schema = json_schema_for_task(task, task_hash=task_hash)
    modes = {
        "llama.cpp": {"transport": "response_format.json_schema", "fallback": "json_schema_to_grammar.py / GBNF"},
        "ollama": {"transport": "format=json_schema", "fallback": "format=json + host validation"},
        "openai": {"transport": "response_format.json_schema", "fallback": "json_object + host validation"},
        "generic": {"transport": "prompted JSON", "fallback": "extract first JSON object + host validation"},
    }
    return {"schema": "minis.structured-output-adapter.v1", "task": task, "provider": provider,
            "json_schema": schema, "mode": modes.get(provider, modes["generic"]),
            "warning": "grammar guarantees syntax only; host still validates semantics, permissions, hashes and canon authority"}
