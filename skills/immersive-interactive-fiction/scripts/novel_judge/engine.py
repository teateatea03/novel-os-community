from __future__ import annotations

from typing import Any

from .canonical import deep_copy, new_id, now_iso, refresh_state_hash, sha256_json, stable_id, state_hash
from .contracts import TURN_SCHEMA
from .delta import apply_operations, propose_delta, validate_delta_paths
from .errors import JudgeError, RECOVERY_REQUIRED, STATE_HASH_MISMATCH
from .graph_patch import build_graph_patch
from .intent import normalize_intent
from .narrative import validate_prose
from .narrative_gate import validate_generated_output
from .state import normalize_state
from .store import FileStore

REPLAYABLE_VERDICTS = {"allow", "allow_with_cost", "partial", "meta"}


def _event(state_before: dict[str, Any], state_after: dict[str, Any], intent: dict[str, Any], delta: dict[str, Any], *, verdict: str) -> dict[str, Any]:
    from .runtime_versioning import stamp_event_contract
    return stamp_event_contract({"schema": "minis.world-event.v1", "event_id": new_id("event"), "turn_id": intent["turn_id"],
            "idempotency_key": f"{intent['turn_id']}:{intent['intent_id']}", "verdict": verdict,
            "intent_id": intent["intent_id"], "actor_id": intent["actor_id"], "action_type": intent["type"],
            "branch_id": state_before.get("branch_id"), "source": intent.get("source"), "operations": delta.get("operations", []),
            "scene": ({"scene_id": intent.get("parameters", {}).get("scene_id"), "chapter_id": intent.get("parameters", {}).get("chapter_id"),
                       "summary": intent.get("parameters", {}).get("summary"), "source_artifact_hash": intent.get("parameters", {}).get("source_artifact_hash"),
                       "source_artifact_path": intent.get("parameters", {}).get("source_artifact_path")}
                      if intent.get("parameters", {}).get("scene_id") else None),
            "costs": delta.get("costs", []), "delayed_effects": delta.get("delayed_effects", []),
            "semantic_delta": intent.get("parameters", {}).get("semantic_delta"),
            "semantic_delta_hash": (intent.get("parameters", {}).get("semantic_delta") or {}).get("semantic_hash"),
            "gate_authorization_hash": intent.get("parameters", {}).get("gate_authorization_hash"),
            "semantic_invariant_report_hash": intent.get("parameters", {}).get("semantic_invariant_report_hash"),
            "pre_state_hash": state_before.get("state_hash"), "after_state_hash": state_after.get("state_hash"),
            "after_revision": state_after.get("revision"), "after_events_head": state_after.get("events_head"),
            "after_last_turn_id": state_after.get("last_turn_id"), "created_at": now_iso()})


def _turn_record(intent: dict[str, Any], *, verdict: str, reason: dict[str, Any] | None = None,
                 before: dict[str, Any], after: dict[str, Any], delta: dict[str, Any] | None,
                 event: dict[str, Any] | None, gate: dict[str, Any] | None, patch: dict[str, Any] | None,
                 status: str = "committed") -> dict[str, Any]:
    return {"schema": TURN_SCHEMA, "turn_id": intent["turn_id"], "intent": intent, "verdict": verdict,
            "status": status, "reason": reason, "pre_state_hash": before.get("state_hash"),
            "post_state_hash": after.get("state_hash"), "delta": delta, "event": event,
            "narrative_gate": gate, "graph_patch": patch, "created_at": now_iso()}


def _restore_journal_sidecars(store: FileStore, journal: dict[str, Any], event: dict[str, Any] | None,
                              after_state: dict[str, Any] | None, *, authority_token: object | None = None) -> None:
    turn = journal.get("turn")
    audit = journal.get("audit")
    patch = journal.get("patch")
    turn_id = journal.get("turn_id")
    if isinstance(turn, dict) and turn_id:
        store.save_turn(turn, _authority_token=authority_token)
    if isinstance(audit, dict) and turn_id:
        store.save_audit(str(turn_id), audit, _authority_token=authority_token)
    if isinstance(patch, dict) and turn_id:
        store.save_graph_patch(str(turn_id), patch, _authority_token=authority_token)
    if event and isinstance(after_state, dict) and journal.get("status") == "committed":
        store.update_head(event, after_state, _authority_token=authority_token)


def recover_store(store: FileStore, *, _authority_token: object | None = None) -> dict[str, Any]:
    store._require_production_token(_authority_token)
    journal = store.load_journal()
    if not journal:
        return {"status": "clean", "recovered": False}
    state = store.load_state()
    after_state = journal.get("after_state")
    after_hash = journal.get("after_state_hash")
    if state and after_hash == state.get("state_hash"):
        event = store.find_event(event_id=journal.get("event_id"), idempotency_key=journal.get("idempotency_key"))
        if event:
            from .event_log import refresh_active_segment_manifest, build_event_index
            refresh_active_segment_manifest(store); build_event_index(store)
        _restore_journal_sidecars(store, journal, event, state, authority_token=_authority_token)
        store.clear_journal(_authority_token=_authority_token); return {"status": "reconciled", "recovered": True}
    # If the append-only event made it to disk but the state replacement did
    # not, finish the state side from the journal snapshot.  Never do this
    # merely because a journal exists: the event/idempotency proof is required.
    event = store.find_event(event_id=journal.get("event_id"),
                             idempotency_key=journal.get("idempotency_key"))
    if event and event.get("verdict") in REPLAYABLE_VERDICTS and isinstance(after_state, dict):
        candidate = normalize_state(after_state, verify_hash=False)
        if candidate.get("state_hash") == after_hash and event.get("after_state_hash") == after_hash:
            from .event_log import refresh_active_segment_manifest, build_event_index
            refresh_active_segment_manifest(store); build_event_index(store)
            store.save_state(candidate, _authority_token=_authority_token)
            _restore_journal_sidecars(store, journal, event, candidate, authority_token=_authority_token)
            store.clear_journal(_authority_token=_authority_token)
            return {"status": "reconciled_state_from_event", "recovered": True,
                    "event_id": event.get("event_id"), "state_hash": after_hash}
    store.clear_journal(_authority_token=_authority_token)
    return {"status": "rolled_back_to_last_state", "recovered": True, "journal": journal}


def _save_rejected(store: FileStore, before: dict[str, Any], intent: dict[str, Any], error: JudgeError,
                   *, recovery: dict[str, Any], authority_token: object | None = None) -> dict[str, Any]:
    """Persist a rejected attempt without mutating authoritative state."""
    event = _event(before, before, intent, {"operations": []}, verdict="reject")
    reason = error.as_dict()
    turn = _turn_record(intent, verdict="reject", reason=reason, before=before, after=before,
                        delta=None, event=event, gate=None, patch=None, status="rejected")
    store.append_event(event, _authority_token=authority_token)
    store.save_turn(turn, _authority_token=authority_token)
    store.save_audit(intent["turn_id"], {"turn_id": intent["turn_id"], "verdict": "reject",
                                         "reason": reason, "recovery": recovery}, _authority_token=authority_token)
    return turn


def _commit_turn_locked(store: FileStore, intent_value: str | dict[str, Any], *, actor_id: str | None = None,
                        generated_output: dict[str, Any] | None = None, expected_state_hash: str | None = None,
                        source: str = "player_input", authority_token: object | None = None) -> dict[str, Any]:
    store._require_production_token(authority_token)
    recovery = recover_store(store, _authority_token=authority_token)
    if recovery["status"] not in {"clean", "reconciled", "reconciled_state_from_event", "rolled_back_to_last_state"}:
        raise JudgeError(RECOVERY_REQUIRED, "store requires manual recovery", details=recovery)
    before = store.load_state()
    if before is None:
        raise JudgeError(RECOVERY_REQUIRED, "branch has no current state")
    before = normalize_state(before)
    if expected_state_hash and expected_state_hash != before["state_hash"]:
        raise JudgeError(STATE_HASH_MISMATCH, "caller state hash is stale", details={"expected": expected_state_hash, "actual": before["state_hash"]})
    intent = normalize_intent(intent_value, actor_id, source=source)
    existing = store.find_event(idempotency_key=f"{intent['turn_id']}:{intent['intent_id']}")
    if existing:
        intent_turn_id = store._safe_segment(intent["turn_id"], "turn_id")
        for turn in [store._read_json(store.turns_dir / f"{intent_turn_id}.json")]:
            if turn: return turn
        return {"status": "already_committed", "event": existing, "post_state_hash": existing.get("after_state_hash")}
    try:
        delta = propose_delta(before, intent)
        after = apply_operations(before, delta["operations"], source=delta.get("source", "system"))
        after["revision"] = int(before.get("revision", 0)) + 1
        after["last_turn_id"] = intent["turn_id"]
        after["events_head"] = new_id("head")
        refresh_state_hash(after)
        gate = validate_generated_output(generated_output, before, audience="reader") if generated_output else {"status": "not_run", "errors": [], "warnings": []}
        if generated_output:
            capacity_gate = validate_prose(generated_output, before, after, intent, audience="reader", accepted_delta=delta)
            gate = {**gate, "capacity_gate": capacity_gate}
            if capacity_gate.get("status") == "fail":
                gate["status"] = "fail"
                gate.setdefault("errors", []).extend(capacity_gate.get("errors", []))
        if intent["type"] == "meta":
            verdict, status = "meta", "committed"
            event = _event(before, after, intent, delta, verdict=verdict)
            patch = None
        elif intent.get("parameters", {}).get("defer_author"):
            after = deep_copy(before)
            verdict, status = "defer", "deferred"
            event = _event(before, after, intent, {**delta, "operations": []}, verdict=verdict)
            patch = None
        elif gate.get("status") == "fail":
            after = deep_copy(before)
            verdict, status = "rejected", "rejected"
            event = _event(before, after, intent, {**delta, "operations": []}, verdict=verdict)
            patch = None
        else:
            verdict = "allow_with_cost" if delta.get("costs") or delta.get("delayed_effects") else "allow"
            status = "committed"
            event = _event(before, after, intent, delta, verdict=verdict)
            patch = build_graph_patch(before, after, turn_id=intent["turn_id"], event_id=event["event_id"], branch_id=store.branch_id)
        turn = _turn_record(intent, verdict=verdict, before=before, after=after, delta=delta, event=event, gate=gate, patch=patch, status=status)
        audit = {"turn_id": intent["turn_id"], "verdict": verdict, "recovery": recovery, "gate": gate}
        store.write_journal({"turn_id": intent["turn_id"], "idempotency_key": event["idempotency_key"],
                             "event_id": event["event_id"], "pre_state_hash": before["state_hash"],
                             "after_state_hash": after["state_hash"], "after_state": after,
                             "turn": turn, "audit": audit, "patch": patch, "status": status, "phase": "prepared"},
                            _authority_token=authority_token)
        store.append_event(event, _authority_token=authority_token)
        store.save_turn(turn, _authority_token=authority_token)
        store.save_audit(intent["turn_id"], audit, _authority_token=authority_token)
        if patch: store.save_graph_patch(intent["turn_id"], patch, _authority_token=authority_token)
        if status == "committed": store.save_state(after, _authority_token=authority_token)
        if authority_token is not None:
            from .durability import crash_failpoint
            crash_failpoint("production_after_state")
        if status == "committed": store.update_head(event, after, _authority_token=authority_token)
        if authority_token is not None:
            from .durability import crash_failpoint
            crash_failpoint("production_after_head")
        store.clear_journal(_authority_token=authority_token)
        return turn
    except JudgeError as exc:
        # Preflight failures do not mutate state, but remain auditable.
        try:
            _save_rejected(store, before, intent, exc, recovery=recovery, authority_token=authority_token)
        except Exception:
            pass
        raise
    except Exception:
        # Journal deliberately remains for the next invocation to inspect.
        raise


def commit_turn(store: FileStore, intent_value: str | dict[str, Any], *, actor_id: str | None = None,
                generated_output: dict[str, Any] | None = None, expected_state_hash: str | None = None,
                source: str = "player_input", lock_timeout: float = 10.0,
                _authority_token: object | None = None) -> dict[str, Any]:
    """Commit one turn under a branch-scoped cross-process lock.

    The lock covers recovery, stale-hash validation, event append, state
    replacement, manifest update and journal cleanup. Models never own it.
    """
    with store.transaction_lock(timeout=lock_timeout):
        from .event_log import recover_event_maintenance
        recover_event_maintenance(store)
        return _commit_turn_locked(
            store, intent_value, actor_id=actor_id, generated_output=generated_output,
            expected_state_hash=expected_state_hash, source=source, authority_token=_authority_token,
        )


def replay_events(initial_state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    from .runtime_versioning import require_replay_compatible
    require_replay_compatible(events)
    state = normalize_state(initial_state, verify_hash=False)
    for event in events:
        if event.get("verdict") not in REPLAYABLE_VERDICTS: continue
        operations = event.get("operations", [])
        if any(isinstance(op, dict) and op.get("op") == "replace_snapshot" for op in operations):
            # Step 3 source-faithful migration events carry full checkpoints.
            # The marker is migration-only and never accepted by normal delta
            # validation or ProjectRuntimeAdapter.commit().
            from .history_migration import apply_migration_operations
            state = apply_migration_operations(state, operations)
        else:
            state = apply_operations(state, operations, source="replay")
        state["revision"] = event.get("after_revision", int(state.get("revision", 0)) + 1)
        state["last_turn_id"] = event.get("after_last_turn_id", event.get("turn_id"))
        state["events_head"] = event.get("after_events_head", event.get("event_id"))
        refresh_state_hash(state)
        if event.get("after_state_hash") and state["state_hash"] != event["after_state_hash"]:
            raise JudgeError(STATE_HASH_MISMATCH, "replay hash mismatch", details={"turn_id": event.get("turn_id")})
    return state
