#!/usr/bin/env python3
from __future__ import annotations

"""Non-canonical author-correction cards and conservative promotion.

These cards never grant canon authority. Promotion only writes quality
artifacts or returns a patch plan; it does not commit world state.
"""

import json
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json

SCHEMA = "minis.author-correction.v1"
LEDGER_SCHEMA = "minis.author-correction-ledger.v1"
STATUSES = {"note", "promoted", "rejected", "superseded"}
ACTIONS = {"note", "character_guard", "rejected_fixture", "gate", "workflow_change", "reject"}
TAXONOMY = {
    "character_voice",
    "human_voice",
    "pacing",
    "sensory_sound",
    "agency",
    "continuity",
    "clarity",
    "behavior",
    "world_rules",
    "other",
}


def project_quality_dir(project_root: str | Path) -> Path:
    root = Path(project_root)
    if (root / "quality").exists() or (root / "turns").exists() or (root / "events.jsonl").exists():
        return root / "quality"
    found = sorted(root.glob("interactive/sessions/*/branches/*/quality"))
    if found:
        return found[0]
    interactive = root / "interactive"
    if interactive.exists():
        pingjie = interactive / "sessions/pingjie-main/branches/main/quality"
        if pingjie.exists() or pingjie.parent.exists():
            return pingjie
        sessions = sorted(interactive.glob("sessions/*/branches/*"))
        if sessions:
            return sessions[0] / "quality"
        return interactive / "sessions/default/branches/main/quality"
    return root / "quality"


def _paths(project_root: str | Path) -> tuple[Path, Path]:
    quality = project_quality_dir(project_root)
    return quality / "author-corrections.jsonl", quality / "author-corrections-manifest.json"


def read_corrections(project_root: str | Path) -> list[dict[str, Any]]:
    ledger, _ = _paths(project_root)
    if not ledger.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get("schema") != SCHEMA:
            raise ValueError(f"correction schema mismatch at line {number}")
        expected = sha256_json({k: v for k, v in value.items() if k != "event_hash"})
        if value.get("event_hash") != expected:
            raise ValueError(f"correction hash mismatch at line {number}")
        previous = rows[-1].get("event_hash") if rows else None
        if value.get("previous_event_hash") != previous:
            raise ValueError(f"correction chain mismatch at line {number}")
        rows.append(value)
    return rows


def recommend_action(card: dict[str, Any]) -> str:
    codes = set(card.get("reason_codes") or [])
    if card.get("one_off"):
        return "note"
    if "continuity" in codes or card.get("character_id"):
        if card.get("bad_excerpt") and card.get("accepted_excerpt"):
            return "character_guard"
    if "human_voice" in codes or "pacing" in codes:
        if card.get("bad_excerpt") and card.get("accepted_excerpt"):
            return "rejected_fixture"
    if card.get("machine_checkable") and card.get("recurrence", 0) >= 2:
        return "gate"
    if card.get("recurrence", 0) < 2:
        return "note"
    return "note"


def active_guards(
    project_root: str | Path,
    *,
    character_id: str | None = None,
    scene_kind: str | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    rows = [x for x in read_corrections(project_root) if x.get("status") == "promoted"]
    out = []
    for row in rows:
        applies = row.get("applies_when") or {}
        applies_character = applies.get("character_id")
        applies_scene = applies.get("scene_kind")
        if applies_character and applies_character != character_id:
            continue
        if applies_scene and applies_scene != scene_kind:
            continue
        out.append(row)
    return out[-limit:]


def append_correction(project_root: str | Path, card: dict[str, Any]) -> dict[str, Any]:
    status = card.get("status") or "note"
    action = card.get("recommended_action") or recommend_action(card)
    if status not in STATUSES:
        raise ValueError("unsupported correction status")
    if action not in ACTIONS:
        raise ValueError("unsupported recommended_action")
    codes = list(dict.fromkeys(str(x) for x in (card.get("reason_codes") or [])))
    unknown = [x for x in codes if x not in TAXONOMY]
    if unknown:
        raise ValueError("unknown reason codes: " + ",".join(unknown))
    if not card.get("title") or not card.get("rule"):
        raise ValueError("correction requires title and rule")
    ledger, manifest_path = _paths(project_root)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    rows = read_corrections(project_root)
    previous = rows[-1]["event_hash"] if rows else None
    core = {
        "title": str(card["title"]),
        "rule": str(card["rule"]),
        "if_condition": card.get("if_condition"),
        "must_not": card.get("must_not"),
        "should": card.get("should"),
        "reason_codes": codes,
        "character_id": card.get("character_id"),
        "turn_id": card.get("turn_id"),
        "scene_id": card.get("scene_id"),
        "bad_excerpt": card.get("bad_excerpt"),
        "accepted_excerpt": card.get("accepted_excerpt"),
        "recommended_action": action,
        "status": status,
        "recurrence": int(card.get("recurrence") or 1),
        "one_off": bool(card.get("one_off")),
        "machine_checkable": bool(card.get("machine_checkable")),
        "applies_when": dict(card.get("applies_when") or {}),
        "promotion_target": card.get("promotion_target"),
        "author_id": card.get("author_id") or "project-author",
        "feedback_event_id": card.get("feedback_event_id"),
        "provenance": dict(card.get("provenance") or {}),
    }
    event_id = "correction-" + sha256_json(core).split(":")[-1][:24]
    for row in rows:
        if row.get("event_id") == event_id:
            return row
    event = {
        "schema": SCHEMA,
        "event_id": event_id,
        **core,
        "previous_event_hash": previous,
        "created_at": now_iso(),
    }
    event["event_hash"] = sha256_json(event)
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    rows.append(event)
    manifest = {
        "schema": LEDGER_SCHEMA,
        "event_count": len(rows),
        "head_event_hash": event["event_hash"],
        "promoted_count": sum(1 for x in rows if x.get("status") == "promoted"),
        "updated_at": now_iso(),
    }
    manifest["manifest_hash"] = sha256_json(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return event


def render_preflight_notes(cards: list[dict[str, Any]]) -> str:
    lines = []
    for card in cards:
        rule = str(card.get("rule") or "").strip()
        if not rule:
            continue
        who = card.get("character_id") or "scene"
        lines.append(f"- [{who}] {rule}")
    return "\n".join(lines)


def compact_guard(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": card.get("event_id"),
        "title": card.get("title"),
        "rule": card.get("rule"),
        "must_not": card.get("must_not"),
        "should": card.get("should"),
        "character_id": card.get("character_id"),
        "reason_codes": list(card.get("reason_codes") or []),
    }


def infer_project_root(state: dict[str, Any] | None) -> str | None:
    if not isinstance(state, dict):
        return None
    for key in ("_production_project_root", "project_root"):
        value = state.get(key)
        if value:
            return str(value)
    return None


def attach_author_corrections(
    context: dict[str, Any],
    project_root: str | Path | None,
    *,
    character_ids: list[str] | None = None,
    scene_kind: str | None = None,
    limit: int = 6,
) -> dict[str, Any]:
    if not project_root:
        return context
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    targets = list(character_ids or []) or [None]
    for character_id in targets:
        for card in active_guards(project_root, character_id=character_id, scene_kind=scene_kind, limit=limit):
            event_id = str(card.get("event_id") or "")
            if event_id in seen:
                continue
            seen.add(event_id)
            cards.append(card)
    if not cards:
        return context
    context["author_corrections"] = [compact_guard(card) for card in cards[:limit]]
    notes = render_preflight_notes(cards[:limit])
    if notes:
        context["author_correction_notes"] = notes
    return context
