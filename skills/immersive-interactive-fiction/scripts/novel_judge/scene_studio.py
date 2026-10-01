from __future__ import annotations

"""Scene Studio: list, context preview, draft/diff, accept-as-candidate.

Drafts are sidecars. Accept never writes canon; it only opens a create_candidate
command. Frozen projects stay preview-only.
"""

import difflib
import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json
from .production_inputs import read_used_sources, resolve_writing_inputs_manifest
from .scene_goals import inspect_scene_goals
from .scene_review import review_scene_text

STUDIO_SCHEMA = "minis.scene-studio.v1"
DRAFT_SCHEMA = "minis.scene-studio-draft.v1"


def _frozen(project_root: Path) -> bool:
    path = project_root / "PROJECT-FROZEN.json"
    if not path.is_file():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return str((value or {}).get("status") or "").upper() == "FROZEN"


def _safe_id(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(value or "scene"))
    return (text or "scene")[:80]


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _resolve_under_root(project_root: Path, relative_path: str) -> Path:
    root = project_root.resolve()
    path = (root / relative_path).resolve()
    if root not in path.parents and path != root:
        raise ValueError("scene path escapes project root")
    return path


def _draft_dir(project_root: Path) -> Path:
    return project_root / "workbench" / "scene-studio" / "drafts"


def _unified_diff(before: str, after: str, *, from_name: str, to_name: str) -> str:
    return "".join(difflib.unified_diff(
        str(before).splitlines(keepends=True),
        str(after).splitlines(keepends=True),
        fromfile=from_name, tofile=to_name, n=3,
    ))


def _read_draft(project_root: Path, draft_id: str) -> dict[str, Any]:
    path = _draft_dir(project_root) / f"{_safe_id(draft_id)}.json"
    if not path.is_file():
        raise FileNotFoundError(draft_id)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("draft is not an object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _iter_prose_files(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for folder, kind in ((project_root / "interactive" / "scenes", "scene"),
                         (project_root / "chapters", "chapter"),
                         (project_root / "scenes", "scene")):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            rows.append({
                "id": path.stem,
                "kind": kind,
                "path": str(path.relative_to(project_root)),
                "chars": len(text),
                "mtime": int(path.stat().st_mtime),
            })
    return rows


def list_scenes(adapter: Any, *, query: str = "", limit: int = 40) -> dict[str, Any]:
    root = Path(adapter.project_root)
    freeze = _frozen(root)
    rows = _iter_prose_files(root)
    q = str(query or "").strip().lower()
    if q:
        rows = [x for x in rows if q in x["id"].lower() or q in x["path"].lower()]
    head = adapter.store._read_json(adapter.runtime_head_path, {}) or {}
    current = str(head.get("scene_id") or head.get("last_turn_id") or "")
    for row in rows:
        row["is_head"] = row["id"] == current or current.startswith(row["id"])
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "list",
        "generated_at": now_iso(),
        "frozen": freeze,
        "write_policy": "read_only_preview" if freeze else "preview_then_candidate",
        "head_id": current,
        "count": len(rows),
        "scenes": rows[: max(1, min(int(limit), 400))],
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def preview_context(adapter: Any, *, actor_id: str) -> dict[str, Any]:
    """Show the verified context pack the model should read. Does not generate."""
    state = adapter.store.load_state() or {}
    working = dict(state)
    working["_production_project_root"] = str(adapter.project_root)
    root, manifest_path = resolve_writing_inputs_manifest(working)
    freeze = _frozen(Path(adapter.project_root))
    if not manifest_path:
        return {
            "schema": STUDIO_SCHEMA, "view": "context_preview", "actor_id": actor_id,
            "status": "unavailable", "frozen": freeze,
            "reason": "verified_writing_inputs_missing",
            "selected_source_ids": [], "used_source_ids": None,
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    meta = (manifest.get("context") or {}).get(actor_id) or {}
    path = Path(adapter.project_root) / meta.get("path", "")
    if not path.is_file():
        return {"schema": STUDIO_SCHEMA, "view": "context_preview", "actor_id": actor_id,
                "status": "missing_pack", "frozen": freeze}
    pack = json.loads(path.read_text(encoding="utf-8"))
    memories = ((pack.get("memory_context") or {}).get("memories") or [])[:8]
    preview = {
        "schema": STUDIO_SCHEMA,
        "view": "context_preview",
        "generated_at": now_iso(),
        "frozen": freeze,
        "status": "ok" if pack.get("context_hash") == meta.get("context_hash") else "hash_mismatch",
        "actor_id": actor_id,
        "manifest_hash": manifest.get("manifest_hash"),
        "context_hash": pack.get("context_hash"),
        "selected_source_ids": list(pack.get("selected_source_ids") or []),
        "addressable_source_ids": list(pack.get("addressable_source_ids") or []),
        "used_source_ids": (read_used_sources(adapter.project_root, actor_id, store=adapter.store, state=working) or {}).get("used_source_ids") or pack.get("used_source_ids"),
        "location": (pack.get("location") or {}).get("id") or pack.get("location"),
        "memory_preview": [{"memory_id": m.get("memory_id"), "text": m.get("text"),
                            "turn_id": m.get("turn_id")} for m in memories if isinstance(m, dict)],
        "excluded": list(pack.get("excluded") or []),
        "author_can_exclude": True,
        "canon_write": False,
    }
    preview["report_hash"] = sha256_json({k: v for k, v in preview.items() if k != "report_hash"})
    return preview


def inspect_scene_file(adapter: Any, *, relative_path: str) -> dict[str, Any]:
    root = Path(adapter.project_root)
    path = _resolve_under_root(root, relative_path)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    review = review_scene_text(text, scene_id=path.stem, source=relative_path)
    freeze = _frozen(root)
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "inspect",
        "generated_at": now_iso(),
        "frozen": freeze,
        "path": relative_path,
        "chars": len(text),
        "scene_goals": review.get("scene_goals"),
        "scene_review": review,
        "narrative_qa": review.get("narrative_qa"),
        "blocks_commit": False,
        "canon_write": False,
        "claims": {
            "machine_prescan_only": True,
            "is_beta_reader": False,
            "is_literary_score": False,
        },
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def save_scene_draft(adapter: Any, *, relative_path: str, text: str,
                     actor_id: str | None = None, note: str | None = None) -> dict[str, Any]:
    """Write a non-canonical draft sidecar and return a unified diff."""
    root = Path(adapter.project_root)
    freeze = _frozen(root)
    if freeze:
        return {"schema": STUDIO_SCHEMA, "view": "draft", "status": "blocked",
                "frozen": True, "reason": "PROJECT_FROZEN", "canon_write": False}
    path = _resolve_under_root(root, relative_path)
    before = path.read_text(encoding="utf-8") if path.is_file() else ""
    after = str(text)
    scene_id = path.stem
    base_hash = _sha256_hex(before)
    draft_hash = _sha256_hex(after)
    draft_id = _safe_id(scene_id)
    review = review_scene_text(after, scene_id=scene_id, source=relative_path)
    goals = review.get("scene_goals") or inspect_scene_goals(after, scene_id=scene_id)
    preview = preview_context(adapter, actor_id=actor_id) if actor_id else {}
    draft = {
        "schema": DRAFT_SCHEMA,
        "draft_id": draft_id,
        "status": "open",
        "scene_id": scene_id,
        "path": relative_path,
        "base_sha256": base_hash,
        "draft_sha256": draft_hash,
        "text": after,
        "chars": len(after),
        "note": note,
        "actor_id": actor_id,
        "used_source_ids": preview.get("used_source_ids") if isinstance(preview, dict) else None,
        "selected_source_ids": preview.get("selected_source_ids") if isinstance(preview, dict) else None,
        "scene_goals": goals,
        "scene_review": {
            "schema": review.get("schema"),
            "narrative_qa": review.get("narrative_qa"),
            "editorial": {
                "status": (review.get("editorial") or {}).get("status"),
                "ticket_count": (review.get("editorial") or {}).get("ticket_count"),
                "strengths": (review.get("editorial") or {}).get("strengths"),
            },
            "blocking_p0_count": review.get("blocking_p0_count"),
            "qa_would_block_later_commit": review.get("qa_would_block_later_commit"),
            "claims": review.get("claims"),
            "report_hash": review.get("report_hash"),
        },
        "source_state_hash": (adapter.store.load_state() or {}).get("state_hash"),
        "updated_at": now_iso(),
        "canon_write": False,
    }
    draft["report_hash"] = sha256_json({k: v for k, v in draft.items() if k not in {"report_hash", "text"}})
    _write_json(_draft_dir(root) / f"{draft_id}.json", draft)
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "draft",
        "status": "saved",
        "frozen": False,
        "draft_id": draft_id,
        "path": relative_path,
        "base_sha256": base_hash,
        "draft_sha256": draft_hash,
        "changed": before != after,
        "diff": _unified_diff(before, after, from_name=relative_path, to_name=f"draft:{draft_id}"),
        "scene_goals": goals,
        "scene_review": draft.get("scene_review"),
        "narrative_qa": (review.get("narrative_qa") or {}),
        "canon_write": False,
        "claims": {"machine_prescan_only": True, "is_beta_reader": False},
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def diff_scene_draft(adapter: Any, *, draft_id: str) -> dict[str, Any]:
    root = Path(adapter.project_root)
    draft = _read_draft(root, draft_id)
    path = _resolve_under_root(root, str(draft.get("path") or ""))
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    current_hash = _sha256_hex(current)
    stale = current_hash != str(draft.get("base_sha256") or "")
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "diff",
        "frozen": _frozen(root),
        "draft_id": draft.get("draft_id"),
        "path": draft.get("path"),
        "status": draft.get("status"),
        "stale_base": stale,
        "current_sha256": current_hash,
        "base_sha256": draft.get("base_sha256"),
        "draft_sha256": draft.get("draft_sha256"),
        "diff": _unified_diff(current, str(draft.get("text") or ""), from_name=str(draft.get("path")), to_name=f"draft:{draft_id}"),
        "scene_goals": draft.get("scene_goals"),
        "canon_write": False,
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def accept_scene_draft(adapter: Any, *, draft_id: str, author_id: str = "author",
                       reason: str | None = None) -> dict[str, Any]:
    """Open a create_candidate command. Does not commit canon or rewrite the scene file."""
    root = Path(adapter.project_root)
    if _frozen(root):
        return {"schema": STUDIO_SCHEMA, "view": "accept", "status": "blocked",
                "frozen": True, "reason": "PROJECT_FROZEN", "canon_write": False}
    draft = _read_draft(root, draft_id)
    if draft.get("status") not in {None, "open"}:
        return {"schema": STUDIO_SCHEMA, "view": "accept", "status": "blocked",
                "reason": f"draft_status_{draft.get('status')}", "canon_write": False}
    path = _resolve_under_root(root, str(draft.get("path") or ""))
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    if _sha256_hex(current) != str(draft.get("base_sha256") or ""):
        return {"schema": STUDIO_SCHEMA, "view": "accept", "status": "blocked",
                "reason": "STALE_BASE", "canon_write": False,
                "hint": "原文已變，請重開草稿再對稿"}
    scene_id = str(draft.get("scene_id") or path.stem)
    payload = {
        "turn_id": scene_id,
        "scene_id": scene_id,
        "actor_id": draft.get("actor_id") or "world",
        "action_type": "scene_commit",
        "source": "author",
        "summary": (draft.get("note") or f"Scene Studio accept {scene_id}")[:240],
        "operations": [],
        "scene_sha256": str(draft.get("draft_sha256") or ""),
        "source_artifact_path": str(draft.get("path") or ""),
        "source_artifact_hash": "sha256:" + str(draft.get("draft_sha256") or ""),
        "studio_draft_id": draft.get("draft_id"),
        "used_source_ids": draft.get("used_source_ids"),
        "proposed_text_chars": draft.get("chars"),
    }
    command = None
    command_error = None
    try:
        from .author_workbench import create_command_request
        command = create_command_request(
            adapter, kind="create_candidate", payload=payload,
            author_id=author_id, reason=reason or f"accept scene draft {draft_id}",
        )
    except Exception as exc:
        command_error = str(exc)
    draft["status"] = "accepted_pending_gates" if command else "accepted_sidecar"
    draft["accepted_at"] = now_iso()
    draft["command_id"] = (command or {}).get("command_id")
    draft["command_error"] = command_error
    draft["report_hash"] = sha256_json({k: v for k, v in draft.items() if k not in {"report_hash", "text"}})
    _write_json(_draft_dir(root) / f"{_safe_id(str(draft.get('draft_id')))}.json", draft)
    pending_dir = root / "workbench" / "scene-studio" / "accepted"
    pending = {
        "schema": "minis.scene-studio-accepted.v1",
        "draft_id": draft.get("draft_id"),
        "path": draft.get("path"),
        "scene_id": scene_id,
        "draft_sha256": draft.get("draft_sha256"),
        "base_sha256": draft.get("base_sha256"),
        "used_source_ids": draft.get("used_source_ids"),
        "command_id": (command or {}).get("command_id"),
        "command_error": command_error,
        "source_state_hash": (adapter.store.load_state() or {}).get("state_hash"),
        "accepted_at": draft["accepted_at"],
        "canon_write": False,
        "note": "作者已接受草稿。正典仍須既有 Gate／approval；此檔不是正典。",
    }
    pending["report_hash"] = sha256_json(pending)
    _write_json(pending_dir / f"{_safe_id(str(draft.get('draft_id')))}.json", pending)
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "accept",
        "status": "accepted_pending_gates" if command else "accepted_sidecar",
        "frozen": False,
        "draft_id": draft.get("draft_id"),
        "command_id": (command or {}).get("command_id"),
        "command_status": (command or {}).get("status"),
        "command_error": command_error,
        "path": draft.get("path"),
        "accepted_path": str((pending_dir / f"{_safe_id(str(draft.get('draft_id')))}.json").relative_to(root)),
        "canon_write": False,
        "note": "草稿已標記接受。未改場景原文與事件正典；命令路能走才建立 create_candidate。",
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def studio_status(adapter: Any, *, query: str = "", limit: int = 12) -> dict[str, Any]:
    """Compact Scene Studio projection for the author workbench. Never writes canon."""
    root = Path(adapter.project_root)
    listed = list_scenes(adapter, query=query, limit=limit)
    drafts: list[dict[str, Any]] = []
    drafts_dir = _draft_dir(root)
    if drafts_dir.is_dir():
        for path in sorted(drafts_dir.glob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(value, dict):
                continue
            drafts.append({
                "draft_id": value.get("draft_id") or path.stem,
                "status": value.get("status"),
                "path": value.get("path"),
                "scene_id": value.get("scene_id"),
                "chars": value.get("chars"),
                "updated_at": value.get("updated_at"),
                "used_source_ids": value.get("used_source_ids"),
            })
    accepted: list[dict[str, Any]] = []
    accepted_dir = root / "workbench" / "scene-studio" / "accepted"
    if accepted_dir.is_dir():
        for path in sorted(accepted_dir.glob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(value, dict):
                continue
            accepted.append({
                "draft_id": value.get("draft_id") or path.stem,
                "path": value.get("path"),
                "scene_id": value.get("scene_id"),
                "command_id": value.get("command_id"),
                "accepted_at": value.get("accepted_at"),
                "used_source_ids": value.get("used_source_ids"),
            })
    state = adapter.store.load_state() or {}
    actor_id = next(iter(state.get("actors") or {"player": None}), "player")
    try:
        preview = preview_context(adapter, actor_id=str(actor_id))
    except Exception as exc:
        preview = {"status": "error", "actor_id": actor_id, "reason": str(exc)}
    freeze = _frozen(root)
    report = {
        "schema": STUDIO_SCHEMA,
        "view": "status",
        "generated_at": now_iso(),
        "frozen": freeze,
        "write_policy": listed.get("write_policy"),
        "head_id": listed.get("head_id"),
        "scene_count": listed.get("count"),
        "scenes": listed.get("scenes") or [],
        "drafts": drafts,
        "accepted": accepted,
        "draft_count": len(drafts),
        "accepted_count": len(accepted),
        "accept_enabled": not freeze,
        "context_preview": {
            "actor_id": preview.get("actor_id") or actor_id,
            "status": preview.get("status"),
            "used_source_ids": preview.get("used_source_ids"),
            "selected_source_ids": preview.get("selected_source_ids"),
            "addressable_source_ids": preview.get("addressable_source_ids"),
            "location": preview.get("location"),
            "reason": preview.get("reason"),
        },
        "cli": {
            "scenes": "python3 -m novel_judge.cli scenes <project-root>",
            "preview": "python3 -m novel_judge.cli preview-context <project-root>",
            "draft": "python3 -m novel_judge.cli draft-scene <project-root> --path ... --text ...",
            "diff": "python3 -m novel_judge.cli diff-scene <project-root> --draft-id ...",
            "accept": "python3 -m novel_judge.cli accept-scene <project-root> --draft-id ...",
        },
        "canon_write": False,
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def write_workbench_projection(adapter: Any) -> dict[str, Any]:
    """Rebuild workbench report.json + index.html only. Does not refresh graph/quality/canon."""
    from .author_workbench import build_workbench_report
    from .author_workbench_html import render_workbench_html
    from .longform_projector import _atomic_text

    report = build_workbench_report(adapter)
    workbench_dir = Path(adapter.project_root) / "workbench"
    workbench_dir.mkdir(parents=True, exist_ok=True)
    adapter.store._atomic_json(workbench_dir / "report.json", report)
    _atomic_text(workbench_dir / "index.html", render_workbench_html(report))
    return {
        "schema": "minis.author-workbench-refresh.v1",
        "generated_at": now_iso(),
        "path": str((workbench_dir / "index.html").relative_to(adapter.project_root)),
        "report_path": str((workbench_dir / "report.json").relative_to(adapter.project_root)),
        "report_hash": report.get("report_hash"),
        "frozen": bool((report.get("resume") or {}).get("frozen")),
        "source": report.get("source"),
        "canon_write": False,
    }

