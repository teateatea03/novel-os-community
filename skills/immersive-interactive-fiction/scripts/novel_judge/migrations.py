from __future__ import annotations

"""Explicit, pure state migrations for the model-independent runtime."""

from pathlib import Path
from typing import Any, Callable
import json

from .canonical import deep_copy, now_iso, sha256_json

CURRENT_STATE_SCHEMA = "minis.interactive-state.v3"
Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _v1_to_v2(source: dict[str, Any]) -> dict[str, Any]:
    state = deep_copy(source)
    state["schema"] = "minis.interactive-state.v2"
    state.setdefault("world_public", {})
    state.setdefault("relations", {})
    state.setdefault("storylets", {"active": [], "cooldowns": {}, "beats": {}})
    state.setdefault("clocks", {})
    state.setdefault("threads", {"open": [], "resolved": []})
    state.setdefault("plans", {"npcs": {}, "world": {}})
    memory = state.setdefault("memory", {"schema": "minis.actor-memory.v2", "episodic": {}, "reflections": {}, "working": {}, "archive": {}})
    if isinstance(memory, dict):
        memory["schema"] = "minis.actor-memory.v2"
        memory.setdefault("episodic", {}); memory.setdefault("reflections", {}); memory.setdefault("working", {}); memory.setdefault("archive", {})
    state.setdefault("last_turn_id", None)
    state.setdefault("metadata", {})
    state.pop("state_hash", None)
    return state


def _v2_to_v3(source: dict[str, Any]) -> dict[str, Any]:
    state = deep_copy(source)
    state["schema"] = CURRENT_STATE_SCHEMA
    memory = state.setdefault("memory", {})
    if not isinstance(memory, dict):
        memory = {}; state["memory"] = memory
    memory["schema"] = "minis.actor-memory.v2"
    memory.setdefault("episodic", {}); memory.setdefault("reflections", {}); memory.setdefault("working", {}); memory.setdefault("archive", {})
    plans = state.setdefault("plans", {"npcs": {}, "world": {}})
    if isinstance(plans, dict):
        plans.setdefault("npcs", {}); plans.setdefault("world", {})
    state.setdefault("metadata", {})
    state.pop("state_hash", None)
    return state


REGISTRY: dict[str, tuple[str, Migration]] = {
    "minis.interactive-state.v1": ("minis.interactive-state.v2", _v1_to_v2),
    "minis.interactive-state.v2": (CURRENT_STATE_SCHEMA, _v2_to_v3),
}


def migration_path(source_schema: str, target_schema: str = CURRENT_STATE_SCHEMA) -> list[str]:
    path: list[str] = []
    seen: set[str] = set()
    current = source_schema
    while current != target_schema:
        if current in seen or current not in REGISTRY:
            raise ValueError(f"no safe migration path: {source_schema} -> {target_schema}")
        seen.add(current)
        nxt, _ = REGISTRY[current]
        path.append(f"{current}->{nxt}")
        current = nxt
    return path


def migrate_state(source: dict[str, Any], *, target_schema: str = CURRENT_STATE_SCHEMA) -> tuple[dict[str, Any], dict[str, Any]]:
    state = deep_copy(source)
    source_schema = str(state.get("schema", ""))
    source_hash = sha256_json(source)
    steps: list[dict[str, Any]] = []
    seen: set[str] = set()
    while state.get("schema") != target_schema:
        schema = str(state.get("schema", ""))
        if schema in seen or schema not in REGISTRY:
            raise ValueError(f"unsupported state schema: {schema or '<missing>'}")
        seen.add(schema)
        nxt, fn = REGISTRY[schema]
        before = sha256_json(state)
        state = fn(state)
        if state.get("schema") != nxt:
            raise RuntimeError(f"migration did not produce {nxt}")
        steps.append({"from": schema, "to": nxt, "before_hash": before, "after_hash": sha256_json(state), "lossy": False})
    report = {
        "schema": "minis.schema-migration-report.v1",
        "source_schema": source_schema,
        "target_schema": target_schema,
        "source_hash": source_hash,
        "target_hash": sha256_json(state),
        "steps": steps,
        "lossy": any(x["lossy"] for x in steps),
    }
    if steps:
        metadata = state.setdefault("metadata", {})
        history = list(metadata.get("migration_history", []))
        history.append({"source_schema": source_schema, "target_schema": target_schema, "source_hash": source_hash, "steps": [x["from"] + "->" + x["to"] for x in steps]})
        metadata["migration_history"] = history[-20:]
        state.pop("state_hash", None)
        report["target_hash"] = sha256_json(state)
    return state, report


def migrate_state_file(path: str | Path, *, backup_dir: str | Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    src = Path(path)
    original = json.loads(src.read_text(encoding="utf-8"))
    migrated, report = migrate_state(original)
    if not report["steps"] or dry_run:
        return {**report, "written": False, "path": str(src)}
    backup_root = Path(backup_dir) if backup_dir else src.parent / "migration-backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / f"{src.name}.{report['source_hash'].split(':')[-1][:16]}.bak"
    backup.write_text(json.dumps(original, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp = src.with_suffix(src.suffix + ".migrating")
    tmp.write_text(json.dumps(migrated, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(src)
    manifest = backup_root / "migration-manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**report, "path": str(src), "backup": str(backup), "migrated_at": now_iso()}, ensure_ascii=False, sort_keys=True) + "\n")
    return {**report, "written": True, "path": str(src), "backup": str(backup), "manifest": str(manifest)}
