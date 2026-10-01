from __future__ import annotations

"""Author Resume Card: one-screen recovery for a single-author workflow."""

import json
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json
from .production import ProjectRuntimeAdapter

RESUME_SCHEMA = "minis.author-resume-card.v1"


def load_project_adapter(root: str | Path) -> ProjectRuntimeAdapter:
    """Resolve project.json without hard-coding a novel slug."""
    root = Path(root)
    meta: dict[str, Any] = {}
    pointer = root / "project.json"
    if pointer.is_file():
        try:
            loaded = json.loads(pointer.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meta = loaded
        except (OSError, ValueError):
            meta = {}
    project_id = str(meta.get("project_id") or root.name)
    ir = meta.get("interactive_runtime") if isinstance(meta.get("interactive_runtime"), dict) else {}
    auth = meta.get("production_authority") if isinstance(meta.get("production_authority"), dict) else {}
    session_id = str(ir.get("session_id") or auth.get("session_id") or meta.get("session_id") or "main")
    branch_id = str(ir.get("branch") or auth.get("branch_id") or "main")
    declared = str(ir.get("namespace") or auth.get("namespace") or meta.get("namespace") or "").strip()
    def _live(ns: str) -> bool:
        base = root / ns / "sessions" / session_id / "branches" / branch_id
        return (base / "state" / "current.json").is_file() or (base / "production-authority.json").is_file()
    if declared in {"interactive", "runtime"} and _live(declared):
        namespace = declared
    elif _live("runtime"):
        namespace = "runtime"
    elif _live("interactive"):
        namespace = "interactive"
    elif (root / "runtime" / "sessions" / session_id).exists():
        namespace = "runtime"
    elif (root / "interactive" / "sessions" / session_id).exists():
        namespace = "interactive"
    else:
        namespace = declared or "interactive"
    return ProjectRuntimeAdapter(root, project_id, session_id, branch_id, namespace=namespace)


def _freeze_record(project_root: Path) -> dict[str, Any] | None:
    path = project_root / "PROJECT-FROZEN.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "UNREADABLE", "path": str(path)}
    if not isinstance(value, dict):
        return {"status": "UNREADABLE", "path": str(path)}
    return value


def _open_threads(state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for raw in (state.get("threads") or {}).get("open") or []:
        if not isinstance(raw, dict):
            continue
        rows.append({
            "id": raw.get("id"),
            "status": raw.get("status"),
            "question": raw.get("question") or raw.get("pressure"),
        })
    return rows[:12]


def _next_action(*, frozen: bool, freeze: dict[str, Any] | None,
                 readiness: dict[str, Any], head_turn: str | None) -> str:
    if frozen:
        cond = (freeze or {}).get("resume_condition") or "需要作者明確指示解凍／繼續"
        return f"專案已凍結。{cond}"
    blockers = list(readiness.get("generation_blockers") or [])
    if blockers:
        return "先解除生成阻擋：" + ", ".join(blockers)
    if not head_turn:
        return "尚無 HEAD。可用 premise／story bible 寫第一場（bootstrap）。"
    return f"從 HEAD {head_turn} 的下一場繼續；先看恢復卡與 context 預覽。"


def build_resume_card(adapter: Any, *, state: dict[str, Any] | None = None,
                      head: dict[str, Any] | None = None,
                      readiness: dict[str, Any] | None = None,
                      events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a compact, non-canonical recovery card. Never writes canon."""
    store = adapter.store
    state = state if state is not None else (store.load_state() or {})
    events = events if events is not None else store.read_events()
    head = head if head is not None else (store._read_json(adapter.runtime_head_path, {}) or {})
    if readiness is None:
        from .project_readiness import project_readiness_report
        readiness = project_readiness_report(adapter)
    freeze = _freeze_record(Path(adapter.project_root))
    frozen = bool(freeze and str(freeze.get("status", "")).upper() == "FROZEN")
    last_event = events[-1] if events else {}
    semantic = last_event.get("semantic_delta") if isinstance(last_event.get("semantic_delta"), dict) else {}
    scene = last_event.get("scene") if isinstance(last_event.get("scene"), dict) else {}
    writing = (readiness.get("writing_inputs") or {}).get("memory") or {}
    quality = readiness.get("quality") or {}
    head_turn = head.get("last_turn_id") or state.get("last_turn_id")
    card = {
        "schema": RESUME_SCHEMA,
        "generated_at": now_iso(),
        "project_id": getattr(adapter, "project_id", state.get("project_id")),
        "session_id": getattr(adapter, "session_id", state.get("session_id")),
        "branch_id": getattr(adapter, "branch_id", state.get("branch_id")),
        "frozen": frozen,
        "freeze": {
            "status": (freeze or {}).get("status"),
            "reason": (freeze or {}).get("reason"),
            "canonical_head": ((freeze or {}).get("freeze_scope") or {}).get("canonical_head"),
            "resume_condition": (freeze or {}).get("resume_condition"),
        } if freeze else None,
        "now": {
            "head_turn": head_turn,
            "revision": head.get("revision") if head.get("revision") is not None else state.get("revision"),
            "scene_id": head.get("scene_id"),
            "scene_path": head.get("scene_path"),
            "event_count": len(events),
            "state_hash": state.get("state_hash"),
            "last_summary": semantic.get("summary") or scene.get("summary"),
        },
        "open_threads": _open_threads(state),
        "readiness": {
            "status": readiness.get("status"),
            "ready_for_generation": readiness.get("ready_for_generation"),
            "ready_for_commands": readiness.get("ready_for_commands"),
            "generation_blockers": list(readiness.get("generation_blockers") or []),
            "command_blockers": list(readiness.get("command_blockers") or []),
            "warnings": list(readiness.get("warnings") or []),
        },
        "writing_inputs": {
            "memory_status": writing.get("status"),
            "episodes": writing.get("episodes"),
            "stale": writing.get("stale"),
        },
        "quality": {
            "explicit_author_pass_at_1": quality.get("explicit_author_pass_at_1"),
            "explicit_feedback_count": quality.get("explicit_feedback_count"),
            "status": quality.get("status"),
        },
        "next_action": _next_action(frozen=frozen, freeze=freeze, readiness=readiness, head_turn=head_turn),
        "continue_command": (
            "作者必須先明確指示解凍／繼續"
            if frozen else
            f"novel-judge resume {adapter.project_root}"
        ),
        "canon_write": False,
    }
    card["report_hash"] = sha256_json({k: v for k, v in card.items() if k != "report_hash"})
    return card
