from __future__ import annotations

from typing import Any

from .canonical import deep_copy, now_iso, refresh_state_hash, sha256_json
from .errors import BRANCH_ISOLATION, JudgeError
from .state import normalize_state
from .store import FileStore


def branch_manifest(store: FileStore, *, parent_branch: str | None = None, base_checkpoint: str | None = None,
                    fork_turn: str | None = None, scope: str = "session", status: str = "active",
                    promoted_from: str | None = None, random_seed: int | None = None) -> dict[str, Any]:
    state = store.load_state()
    return {
        "schema": "minis.interactive-branch-manifest.v1", "project_id": store.project_id,
        "session_id": store.session_id, "branch_id": store.branch_id,
        "parent_branch": parent_branch, "base_checkpoint": base_checkpoint,
        "base_state_hash": state.get("state_hash") if state else None, "fork_turn": fork_turn,
        "scope": scope, "status": status, "created_at": now_iso(),
        "promoted_from": promoted_from, "head_event_id": state.get("events_head") if state else None,
        "head_state_hash": state.get("state_hash") if state else None,
        "random_seed": random_seed, "schema_version": 1,
    }


def ensure_manifest(store: FileStore, **kwargs: Any) -> dict[str, Any]:
    existing = store.load_manifest()
    if existing:
        return existing
    manifest = branch_manifest(store, **kwargs)
    store.save_manifest(manifest)
    return manifest


def fork_branch(parent: FileStore, child_branch_id: str, *, checkpoint_id: str | None = None,
                scope: str = "experiment", random_seed: int | None = None) -> FileStore:
    child = FileStore(parent.root, parent.project_id, parent.session_id, child_branch_id, namespace=parent.namespace)
    if child.base.exists() and child.load_state() is not None:
        raise JudgeError(BRANCH_ISOLATION, "target branch already exists", details={"branch_id": child_branch_id})
    source = parent.load_checkpoint(checkpoint_id) if checkpoint_id else parent.load_state()
    if source is None:
        raise JudgeError(BRANCH_ISOLATION, "parent branch has no state")
    state = deep_copy(source)
    state["branch_id"] = child_branch_id
    state["revision"] = int(state.get("revision", 0))
    refresh_state_hash(state)
    child.save_state(state)
    checkpoint = checkpoint_id or f"fork-{state.get('revision', 0)}-{state['state_hash'][7:19]}"
    child.write_checkpoint(checkpoint, state)
    manifest = branch_manifest(child, parent_branch=parent.branch_id, base_checkpoint=checkpoint,
                               fork_turn=state.get("last_turn_id"), scope=scope, random_seed=random_seed)
    manifest["base_state_hash"] = state["state_hash"]
    child.save_manifest(manifest)
    child.save_workflow({"status": "ready", "phase": "forked", "source_branch": parent.branch_id,
                         "base_state_hash": state["state_hash"], "updated_at": now_iso()})
    return child


def rewind_branch(parent: FileStore, child_branch_id: str, checkpoint_id: str, *, scope: str = "experiment") -> FileStore:
    return fork_branch(parent, child_branch_id, checkpoint_id=checkpoint_id, scope=scope)


def branch_affected(parent_state: dict[str, Any], branch_state: dict[str, Any]) -> dict[str, Any]:
    from .diff import state_diff, affected_entities
    changes = state_diff(parent_state, branch_state)
    return {"change_count": len(changes), "changes": changes, "entities": affected_entities(parent_state, branch_state),
            "parent_hash": parent_state.get("state_hash"), "branch_hash": branch_state.get("state_hash")}


def promote_branch(store: FileStore, *, author_decision: str, target_scope: str = "candidate-canon") -> dict[str, Any]:
    """Create an explicit promotion report; never writes project canon directly."""
    if author_decision not in {"approve", "reject"}:
        raise ValueError("author_decision must be approve or reject")
    manifest = ensure_manifest(store)
    state = store.load_state()
    events = store.read_events()
    accepted = [e for e in events if e.get("verdict") in {"allow", "allow_with_cost", "partial"}]
    report = {"schema": "minis.canon-promotion-report.v1", "promotion_id": sha256_json([store.session_id, store.branch_id, state.get("state_hash") if state else None]),
              "project_id": store.project_id, "session_id": store.session_id, "branch_id": store.branch_id,
              "source_scope": manifest.get("scope"), "target_scope": target_scope, "author_decision": author_decision,
              "accepted_event_ids": [e.get("event_id") for e in accepted], "state_hash": state.get("state_hash") if state else None,
              "status": "approved_pending_canon_writer" if author_decision == "approve" else "rejected",
              "created_at": now_iso(), "canon_write": "not_performed"}
    path = store.base / "promotions" / f"{report['promotion_id'].split(':')[-1][:24]}.json"
    store._atomic_json(path, report)
    if author_decision == "approve":
        manifest["status"] = "promotion-approved"
        manifest["promoted_from"] = store.branch_id
        store.save_manifest(manifest)
    return report
