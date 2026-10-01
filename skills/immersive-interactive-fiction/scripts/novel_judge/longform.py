from __future__ import annotations

"""Production-authority facade for traditional long-form projects."""

from pathlib import Path
from typing import Any
from .canonical import refresh_state_hash
from .intent import make_intent
from .engine import commit_turn
from .production import ProjectRuntimeAdapter
from .state import empty_state
from .store import FileStore


def init_longform_state(project_id: str, session_id: str = "manuscript", branch_id: str = "main") -> dict[str, Any]:
    state = empty_state(project_id, session_id, branch_id)
    state["canon_scope"] = "canon"
    state["world_truth"]["events"] = {}
    state["actors"]["world"] = {"kind": "world", "location": None, "status": {}, "commitments": []}
    state["metadata"]["mode"] = "long_form"
    state["metadata"]["derived_artifacts"] = ["current-state.md", "timeline.md", "chapter-index.md", "summaries", "graphify-out"]
    return refresh_state_hash(state)


def longform_adapter(project_root: str | Path, project_id: str, session_id: str = "manuscript",
                     branch_id: str = "main") -> ProjectRuntimeAdapter:
    return ProjectRuntimeAdapter(project_root, project_id, session_id, branch_id, namespace="runtime")


def initialize_longform_production(project_root: str | Path, project_id: str, *,
                                   provenance: dict[str, Any] | None = None) -> ProjectRuntimeAdapter:
    adapter = longform_adapter(project_root, project_id)
    adapter.initialize_new_project(init_longform_state(project_id), baseline_id="initial",
                                   provenance={"mode": "traditional_long_form", **dict(provenance or {})})
    return adapter


def longform_store(project_root: str | Path, project_id: str, session_id: str = "manuscript",
                   branch_id: str = "main") -> Any:
    """Legacy fixture/migration store; production projects use longform_adapter."""
    return FileStore(project_root, project_id, session_id, branch_id, namespace="runtime")


def commit_scene_event(adapter_or_store: Any, *, scene_id: str, chapter_id: str,
                       operations: list[dict[str, Any]], summary: str,
                       author_approved: bool, expected_state_hash: str,
                       source_artifact_hash: str | None = None,
                       source_artifact_path: str | None = None,
                       scene_sha256: str | None = None,
                       semantic_kind: str | None = None,
                       semantic_effects: list[dict[str, Any]] | None = None,
                       author_decision: dict[str, Any] | None = None) -> dict[str, Any]:
    if not author_approved:
        return {"status": "deferred", "reason": "author_approval_required", "scene_id": scene_id}
    adapter = adapter_or_store if isinstance(adapter_or_store, ProjectRuntimeAdapter) else None
    if adapter is None:
        # Backward-compatible non-production fixture/migration path. A store
        # bound to production-authority.json is fenced by FileStore itself.
        intent = make_intent("world", "world_tick", turn_id=scene_id, source="author", player_authored=True,
                             parameters={"operations": operations, "scene_id": scene_id, "chapter_id": chapter_id,
                                         "summary": summary, "source_artifact_hash": source_artifact_hash})
        return commit_turn(adapter_or_store, intent, expected_state_hash=expected_state_hash, source="author")
    if not scene_sha256:
        raise ValueError("production long-form commit requires a scene-bound Gate authorization")
    decision = author_decision or {
        "decision": "accept",
        "author_id": "author",
        "reason_codes": ["other"],
        "reason": "author_approved scene commit",
        "confidence": "high",
    }
    return adapter.commit(turn_id=scene_id, operations=operations,
                          expected_state_hash=expected_state_hash,
                          actor_id="world", action_type="scene_commit", source="author",
                          summary=summary, scene_id=scene_id, chapter_id=chapter_id,
                          source_artifact_hash=source_artifact_hash,
                          source_artifact_path=source_artifact_path,
                          scene_sha256=scene_sha256, semantic_kind=semantic_kind,
                          semantic_effects=semantic_effects,
                          author_decision=decision)
