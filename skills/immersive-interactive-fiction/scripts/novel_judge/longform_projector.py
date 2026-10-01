from __future__ import annotations

"""Deterministic Markdown projections from long-form event/state authority."""

from pathlib import Path
from typing import Any
import json
import os
import tempfile

from .canonical import now_iso, sha256_json


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _scene(event: dict[str, Any]) -> dict[str, Any]:
    meta = event.get("scene") if isinstance(event.get("scene"), dict) else {}
    semantic = event.get("semantic_delta") if isinstance(event.get("semantic_delta"), dict) else {}
    return {"scene_id": meta.get("scene_id") or event.get("turn_id"), "chapter_id": meta.get("chapter_id") or "UNKNOWN",
            "summary": semantic.get("summary") or meta.get("summary") or "（事件未提供摘要）", "semantic_kind": semantic.get("semantic_kind"), "source_artifact_hash": meta.get("source_artifact_hash"),
            "event_id": event.get("event_id"), "created_at": event.get("created_at"), "revision": event.get("after_revision")}


def render_current_state(state: dict[str, Any]) -> str:
    lines = ["# Current State｜事件核心投影", "", "> AUTO-GENERATED；請勿直接作為機器正本。", "",
             f"- Project：`{state.get('project_id')}`", f"- Session／Branch：`{state.get('session_id')}`／`{state.get('branch_id')}`",
             f"- Revision：{state.get('revision')}", f"- State hash：`{state.get('state_hash')}`",
             f"- 最後事件：`{state.get('events_head')}`", f"- 最後場景：`{state.get('last_turn_id')}`",
             f"- 時鐘：`{json.dumps(state.get('clock', {}), ensure_ascii=False, sort_keys=True)}`", "", "## 人物狀態", ""]
    actors = state.get("actors", {})
    if actors:
        lines += ["| 人物 | 類型 | 位置 | 狀態 |", "|---|---|---|---|"]
        for aid, actor in sorted(actors.items()):
            lines.append(f"| {aid} | {actor.get('kind', '')} | {actor.get('location', '')} | {json.dumps(actor.get('status', {}), ensure_ascii=False, sort_keys=True)} |")
    else: lines.append("- 尚無人物狀態事件。")
    lines += ["", "## 開放線", ""]
    for item in state.get("threads", {}).get("open", []): lines.append(f"- {item}")
    if not state.get("threads", {}).get("open", []): lines.append("- 無。")
    return "\n".join(lines) + "\n"


def render_timeline(events: list[dict[str, Any]]) -> str:
    lines = ["# Timeline｜事件核心投影", "", "> AUTO-GENERATED from append-only events.", "", "| Revision | 場景 | 章 | 摘要 | Event | 時間 |", "|---:|---|---|---|---|---|"]
    for event in events:
        if event.get("verdict") not in {"allow", "allow_with_cost", "partial", "meta"}: continue
        scene = _scene(event); summary = str(scene["summary"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {scene['revision']} | {scene['scene_id']} | {scene['chapter_id']} | {summary} | `{scene['event_id']}` | {scene['created_at']} |")
    return "\n".join(lines) + "\n"


def render_chapter_index(events: list[dict[str, Any]]) -> str:
    chapters: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("verdict") not in {"allow", "allow_with_cost", "partial", "meta"}: continue
        scene = _scene(event); chapters.setdefault(str(scene["chapter_id"]), []).append(scene)
    lines = ["# Chapter Index｜事件核心投影", "", "> AUTO-GENERATED；正典權限仍由核准事件與來源正文共同決定。", "", "| 章 | 場景數 | 起始場景 | 結尾場景 | 最新摘要 | 狀態 |", "|---|---:|---|---|---|---|"]
    for chapter, scenes in sorted(chapters.items()):
        latest = str(scenes[-1]["summary"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {chapter} | {len(scenes)} | {scenes[0]['scene_id']} | {scenes[-1]['scene_id']} | {latest} | [CANON-EVENT] |")
    return "\n".join(lines) + "\n"


def project_longform_markdown(store: Any, project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root else store.root
    state = store.load_state(); events = store.read_events()
    if state is None: raise ValueError("long-form store has no state")
    outputs = {"current-state.md": render_current_state(state), "timeline.md": render_timeline(events), "chapter-index.md": render_chapter_index(events)}
    written = {}
    for name, text in outputs.items():
        path = root / name; _atomic_text(path, text); written[name] = {"path": str(path), "sha256": sha256_json(text), "bytes": len(text.encode("utf-8"))}
    manifest = {"schema": "minis.longform-projection-manifest.v1", "source_state_hash": state.get("state_hash"),
                "source_events_hash": sha256_json(events), "generated_at": now_iso(), "outputs": written}
    store._atomic_json(store.base / "projection-manifest.json", manifest)
    return manifest


def projection_status(store: Any, project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root else store.root; manifest_path = store.base / "projection-manifest.json"
    if not manifest_path.exists(): return {"status": "missing", "stale": True}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); state = store.load_state(); events = store.read_events(); errors = []
    if manifest.get("source_state_hash") != (state or {}).get("state_hash"): errors.append("state_hash_stale")
    if manifest.get("source_events_hash") != sha256_json(events): errors.append("events_hash_stale")
    for name, meta in manifest.get("outputs", {}).items():
        path = root / name
        if not path.exists(): errors.append(f"missing:{name}")
        elif sha256_json(path.read_text(encoding="utf-8")) != meta.get("sha256"): errors.append(f"modified:{name}")
    return {"status": "pass" if not errors else "stale", "stale": bool(errors), "errors": errors, "manifest": manifest}
