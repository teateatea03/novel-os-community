from __future__ import annotations

"""Auditable, non-canonical random-event suggestions.

The module deliberately never creates a world event, StateDelta, Graph patch,
knowledge update, prose injection, or player action.  A draw only returns an
optional direction card.  Canonical adoption must re-enter the ordinary Judge
planning and Gate pipeline.
"""

from pathlib import Path
from typing import Any
import hashlib
import json
import os

from .canonical import canonical_json, now_iso, sha256_json, stable_id
from .durability import crash_failpoint, fsync_directory
from .errors import JudgeError, SCHEMA_ERROR, STATE_HASH_MISMATCH

SETTINGS_SCHEMA = "minis.random-event-settings.v1"
POOL_SCHEMA = "minis.random-event-pool.v1"
SUGGESTION_SCHEMA = "minis.random-event-suggestion.v1"
DRAW_SCHEMA = "minis.random-event-draw.v1"
HANDOFF_SCHEMA = "minis.random-event-adoption-handoff.v1"
ALGORITHM_VERSION = "sha256-weighted-v1"
MODES = {"off", "on-suggestion"}
TRIGGERS = {
    "action_resolution", "scene_boundary", "transition", "travel", "downtime",
    "post_scene", "post_chapter", "world_pulse", "telegraphed_threat_due",
}
CATEGORIES = {
    "ambient", "opportunity", "complication", "threat", "recovery", "remote_world",
    "character_hook", "relationship", "background_npc", "faction_world", "thread_move", "thematic_accident",
}
URGENCY = {"low": 0, "normal": 1, "high": 2, "critical": 3}
GLOBAL_FORBIDDEN_OUTCOMES = [
    "control_player_action_or_inner_state", "reveal_protected_unknown",
    "declare_death_or_permanent_injury", "declare_pregnancy_marriage_or_parenthood",
    "declare_betrayal_or_relationship_formation_or_break", "destroy_faction_or_change_world_rule",
    "mutate_state_graph_knowledge_timeline_or_prose", "commit_canon_without_author_choice_and_normal_gates",
]
DECISIVE_PATTERNS = (
    "已死亡", "已死", "已背叛", "已懷孕", "已結婚", "已離婚", "已滅亡", "永久殘疾",
    "玩家必須", "你必須", "你決定", "你害怕", "你愛上", "你相信",
)


def default_settings() -> dict[str, Any]:
    return {"schema": SETTINGS_SCHEMA, "mode": "off", "scope": "branch", "updated_at": None, "changed_by": None}


def _paths(store: Any) -> tuple[Path, Path]:
    root = Path(store.base) / "random-events"
    return root / "settings.json", root / "suggestion-audit.jsonl"


def load_random_event_settings(store: Any) -> dict[str, Any]:
    settings_path, _ = _paths(store)
    if not settings_path.exists():
        return default_settings()
    value = json.loads(settings_path.read_text(encoding="utf-8"))
    if value.get("schema") != SETTINGS_SCHEMA or value.get("mode") not in MODES or value.get("scope") != "branch":
        raise JudgeError(SCHEMA_ERROR, "invalid random-event settings")
    return value


def set_random_event_mode(store: Any, mode: str, *, changed_by: str = "user") -> dict[str, Any]:
    if mode not in MODES:
        raise JudgeError(SCHEMA_ERROR, "random-event mode must be off or on-suggestion", details={"mode": mode})
    if changed_by not in {"user", "author"}:
        raise JudgeError("RANDOM_EVENT_MODE_AUTHORITY_REQUIRED", "only user/author authority may change random-event mode")
    value = {"schema": SETTINGS_SCHEMA, "mode": mode, "scope": "branch", "updated_at": now_iso(), "changed_by": changed_by}
    settings_path, _ = _paths(store)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with store.transaction_lock():
        store._atomic_json(settings_path, value)
    return value


def _get_path(value: Any, path: str) -> Any:
    cur = value
    for part in path.split("."):
        if not isinstance(cur, dict): return None
        cur = cur.get(part)
    return cur


def validate_random_event_pool(pool: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    if not isinstance(pool, dict) or pool.get("schema") != POOL_SCHEMA:
        errors.append({"code": "RANDOM_EVENT_POOL_SCHEMA", "path": "schema"})
        return {"ok": False, "errors": errors}
    seen: set[str] = set()
    events = pool.get("events")
    if not isinstance(events, list):
        return {"ok": False, "errors": [{"code": "RANDOM_EVENT_POOL_EVENTS", "path": "events"}]}
    required = {"id", "category", "triggers", "frequency_weight", "urgency", "focus_kind", "function", "pressure_direction", "exposure"}
    for index, event in enumerate(events):
        path = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append({"code": "RANDOM_EVENT_DEFINITION_TYPE", "path": path}); continue
        missing = sorted(required - set(event))
        if missing: errors.append({"code": "RANDOM_EVENT_DEFINITION_MISSING", "path": path, "missing": missing})
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id: errors.append({"code": "RANDOM_EVENT_ID", "path": path})
        elif event_id in seen: errors.append({"code": "RANDOM_EVENT_DUPLICATE_ID", "path": path, "id": event_id})
        else: seen.add(event_id)
        if event.get("category") not in CATEGORIES: errors.append({"code": "RANDOM_EVENT_CATEGORY", "path": path})
        triggers = event.get("triggers", [])
        if not isinstance(triggers, list) or not triggers or not set(triggers).issubset(TRIGGERS): errors.append({"code": "RANDOM_EVENT_TRIGGER", "path": path})
        if not isinstance(event.get("frequency_weight"), int) or not 1 <= event.get("frequency_weight", 0) <= 100000: errors.append({"code": "RANDOM_EVENT_WEIGHT", "path": path})
        if event.get("urgency") not in URGENCY: errors.append({"code": "RANDOM_EVENT_URGENCY", "path": path})
        text = " ".join(str(event.get(k, "")) for k in ("function", "pressure_direction", "exposure"))
        if any(term in text for term in DECISIVE_PATTERNS): errors.append({"code": "RANDOM_EVENT_DECISIVE_OUTCOME", "path": path})
    no_event_weight = pool.get("no_event_weight", 1)
    if not isinstance(no_event_weight, int) or not 1 <= no_event_weight <= 100000:
        errors.append({"code": "RANDOM_EVENT_NO_EVENT_WEIGHT", "path": "no_event_weight"})
    return {"ok": not errors, "errors": errors, "event_count": len(events), "pool_hash": sha256_json(pool)}


def _window_gate(trigger: str, window: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if trigger not in TRIGGERS: return False, ["unsupported_trigger"]
    if window.get("input_kind") in {"meta", "status", "options", "revision", "clarification"}: reasons.append("meta_or_clarification")
    if window.get("direct_consequence_pending"): reasons.append("direct_consequence_pending")
    if window.get("deterministic_consequence_available"): reasons.append("deterministic_consequence_available")
    if window.get("emotional_closure_active"): reasons.append("emotional_closure_active")
    if window.get("high_intensity_active") and not window.get("natural_break"): reasons.append("no_natural_break")
    if trigger == "action_resolution" and not window.get("randomness_needed", False): reasons.append("action_resolution_does_not_need_randomness")
    if trigger in {"scene_boundary", "transition", "post_scene", "post_chapter"} and not window.get("natural_break", True): reasons.append("no_natural_break")
    if trigger == "telegraphed_threat_due" and not window.get("telegraphed", False): reasons.append("threat_not_telegraphed")
    return not reasons, sorted(set(reasons))


def _player_id(state: dict[str, Any], window: dict[str, Any]) -> str:
    explicit = window.get("player_actor_id")
    if explicit: return str(explicit)
    for actor_id, actor in sorted(state.get("actors", {}).items()):
        if actor.get("kind") == "player": return actor_id
    return "player"


def _present_ids(state: dict[str, Any], window: dict[str, Any]) -> list[str]:
    if isinstance(window.get("present_actor_ids"), list): return [str(x) for x in window["present_actor_ids"]]
    player = state.get("actors", {}).get(_player_id(state, window), {})
    location = window.get("location") or player.get("location")
    return sorted(aid for aid, actor in state.get("actors", {}).items() if location is not None and actor.get("location") == location)


def _bind_roles(state: dict[str, Any], event: dict[str, Any], window: dict[str, Any], seed: Any) -> tuple[dict[str, str] | None, list[str]]:
    roles = event.get("required_roles", {})
    if not isinstance(roles, dict): return None, ["invalid_roles"]
    present = set(_present_ids(state, window)); player_id = _player_id(state, window); protected = set(window.get("protected_actor_ids", []))
    bindings: dict[str, str] = {}; used: set[str] = set()
    for role, spec in sorted(roles.items()):
        if not isinstance(spec, dict): return None, [f"invalid_role:{role}"]
        candidates = []
        allowed_ids = set(spec.get("actor_ids", [])) if spec.get("actor_ids") else None
        required_tags = set(spec.get("required_tags", [])); preferred_tags = set(spec.get("preferred_tags", []))
        for actor_id, actor in sorted(state.get("actors", {}).items()):
            if actor_id in used or actor_id in protected: continue
            if spec.get("not_player", True) and actor_id == player_id: continue
            if allowed_ids is not None and actor_id not in allowed_ids: continue
            if spec.get("kind") and actor.get("kind") != spec["kind"]: continue
            if spec.get("present", False) and actor_id not in present: continue
            tags = set(actor.get("tags", [])) | set(actor.get("hooks", []))
            if not required_tags.issubset(tags): continue
            score = len(preferred_tags & tags)
            tie = hashlib.sha256(canonical_json([seed, event.get("id"), role, actor_id]).encode("utf-8")).hexdigest()
            candidates.append((-score, tie, actor_id))
        if not candidates: return None, [f"role_unbound:{role}"]
        candidates.sort(); chosen = candidates[0][2]; bindings[role] = chosen; used.add(chosen)
    return bindings, []


def _event_eligible(state: dict[str, Any], event: dict[str, Any], trigger: str, window: dict[str, Any], seed: Any) -> tuple[bool, dict[str, str], list[str]]:
    reasons: list[str] = []
    if trigger not in event.get("triggers", []): return False, {}, ["trigger"]
    if event.get("category") in set(window.get("pending_categories", [])): reasons.append("category_already_pending")
    if event.get("dedup_key") in set(window.get("recent_dedup_keys", [])): reasons.append("recent_dedup")
    if event.get("category") in set(window.get("excluded_categories", [])): reasons.append("category_excluded")
    cond = event.get("conditions", {})
    if not isinstance(cond, dict): reasons.append("invalid_conditions"); cond = {}
    for path, expected in cond.get("state_equals", {}).items():
        if _get_path(state, path) != expected: reasons.append(f"state:{path}")
    open_threads = {str(x.get("id")) if isinstance(x, dict) else str(x) for x in state.get("threads", {}).get("open", [])}
    if cond.get("requires_open_thread") and not open_threads: reasons.append("open_thread_required")
    required_threads = set(cond.get("thread_ids", []))
    if required_threads and not (required_threads & open_threads): reasons.append("thread")
    visible = set(state.get("knowledge", {}).get("reader", [])) | set(state.get("knowledge", {}).get("player", {}).get(_player_id(state, window), []))
    required_facts = set(cond.get("requires_visible_facts", []))
    if not required_facts.issubset(visible): reasons.append("visible_fact")
    protected_facts = set(window.get("protected_fact_ids", []))
    if set(event.get("fact_refs", [])) & protected_facts: reasons.append("protected_unknown")
    if reasons: return False, {}, reasons
    bindings, role_reasons = _bind_roles(state, event, window, seed)
    return bindings is not None, bindings or {}, role_reasons


def _roll(seed: Any, pool_hash: str, trigger: str, source_state_hash: str, total: int) -> tuple[int, str]:
    material = canonical_json([ALGORITHM_VERSION, seed, pool_hash, trigger, source_state_hash])
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return int(digest, 16) % total, "sha256:" + digest


def suggest_random_event(state: dict[str, Any], pool: dict[str, Any], *, trigger: str, seed: Any, window: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pure draw.  The input state is inspected but never changed."""
    report = validate_random_event_pool(pool)
    if not report["ok"]: raise JudgeError(SCHEMA_ERROR, "invalid random-event pool", details=report)
    window = dict(window or {})
    allowed, suppressed = _window_gate(trigger, window)
    base = {"schema": DRAW_SCHEMA, "algorithm_version": ALGORITHM_VERSION, "source_state_hash": state.get("state_hash"), "pool_hash": report["pool_hash"], "trigger": trigger, "seed": seed, "canon_status": "NON_CANONICAL", "write_authority": "none"}
    if not allowed:
        return {**base, "status": "suppressed", "generated": False, "suppression_reasons": suppressed, "eligible_set": [], "suggestion": None, "state_delta": [], "graph_patch": [], "knowledge_patch": [], "prose_patch": []}
    eligible = []
    rejected = []
    for event in pool.get("events", []):
        ok, bindings, reasons = _event_eligible(state, event, trigger, window, seed)
        if ok:
            eligible.append({"event": event, "bindings": bindings, "effective_weight": event["frequency_weight"], "urgency_rank": URGENCY[event["urgency"]]})
        else: rejected.append({"event_id": event.get("id"), "reasons": reasons})
    if not eligible:
        return {**base, "status": "no_event", "generated": False, "reason": "empty_eligible_pool", "eligible_set": [], "rejected": rejected, "suggestion": None, "state_delta": [], "graph_patch": [], "knowledge_patch": [], "prose_patch": []}
    max_urgency = max(x["urgency_rank"] for x in eligible)
    tier = [x for x in eligible if x["urgency_rank"] == max_urgency]
    weighted = [(x["event"]["id"], x["effective_weight"], x) for x in tier]
    weighted.append(("__no_event__", int(pool.get("no_event_weight", 1)), None))
    total = sum(x[1] for x in weighted); roll, roll_digest = _roll(seed, report["pool_hash"], trigger, str(state.get("state_hash")), total)
    cursor = 0; selected = weighted[-1]
    for item in weighted:
        cursor += item[1]
        if roll < cursor: selected = item; break
    provenance = {"roll": roll, "roll_digest": roll_digest, "total_weight": total, "urgency_tier": max_urgency, "weighted_choices": [{"id": x[0], "weight": x[1]} for x in weighted], "rejected": rejected}
    eligible_summary = [{"event_id": x["event"]["id"], "category": x["event"]["category"], "weight": x["effective_weight"], "urgency": x["event"]["urgency"], "bindings": x["bindings"]} for x in tier]
    if selected[2] is None:
        return {**base, "status": "no_event", "generated": False, "reason": "weighted_no_event", "eligible_set": eligible_summary, "draw_provenance": provenance, "suggestion": None, "state_delta": [], "graph_patch": [], "knowledge_patch": [], "prose_patch": []}
    chosen = selected[2]; event = chosen["event"]; bindings = chosen["bindings"]
    focus_ref = next(iter(bindings.values()), None)
    if focus_ref is None and event.get("focus_kind") == "open_thread":
        threads = state.get("threads", {}).get("open", []); focus_ref = (threads[0].get("id") if threads and isinstance(threads[0], dict) else (threads[0] if threads else None))
    suggestion_id = stable_id("random-suggestion", state.get("state_hash"), report["pool_hash"], trigger, seed, event["id"], roll_digest)
    text = f"可考慮讓「{focus_ref or event['focus_kind']}」相關的{event['function']}，從{event['exposure']}露出；壓力方向是{event['pressure_direction']}。先保留查證、回應或略過的空間，不預定結果。"
    suggestion = {
        "schema": SUGGESTION_SCHEMA, "suggestion_id": suggestion_id, "event_definition_id": event["id"],
        "source_state_hash": state.get("state_hash"), "pool_hash": report["pool_hash"], "algorithm_version": ALGORITHM_VERSION,
        "category": event["category"], "focus_kind": event["focus_kind"], "focus_ref": focus_ref,
        "role_bindings": bindings, "function": event["function"], "pressure_direction": event["pressure_direction"],
        "exposure": event["exposure"], "direction_text": text, "dedup_key": event.get("dedup_key", event["id"]),
        "canon_status": "NON_CANONICAL_SUGGESTION", "optional": True, "commit_authority": "none",
        "forbidden_outcomes": sorted(set(GLOBAL_FORBIDDEN_OUTCOMES + list(event.get("forbidden_outcomes", [])))),
        "required_next_step": "author_or_user_may_request_adoption_handoff_then_run_current_state_revalidation_and_all_normal_gates",
        "state_delta": [], "graph_patch": [], "knowledge_patch": [], "timeline_patch": [], "prose_patch": [],
    }
    return {**base, "status": "suggested", "generated": True, "eligible_set": eligible_summary, "draw_provenance": provenance, "suggestion": suggestion, "state_delta": [], "graph_patch": [], "knowledge_patch": [], "prose_patch": []}


def _audit_paths(store: Any) -> tuple[Path, Path, Path]:
    _, audit_path = _paths(store)
    return audit_path, audit_path.parent / "audit-manifest.json", audit_path.parent / "audit-transaction.json"


def _default_audit_manifest() -> dict[str, Any]:
    return {"schema": "minis.random-event-audit-manifest.v1", "record_count": 0, "head_hash": None}


def _parse_audit_bytes(data: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []; previous_hash = None
    for raw in data.splitlines():
        if not raw.strip(): continue
        try:
            value = json.loads(raw.decode("utf-8")); supplied = value.pop("audit_hash", None)
        except Exception as exc:
            raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "random-event audit is malformed") from exc
        if supplied != sha256_json(value) or value.get("previous_audit_hash") != previous_hash:
            raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "random-event audit hash chain failed")
        value["audit_hash"] = supplied; previous_hash = supplied; records.append(value)
    return records


def _verified_audit(store: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit_path, manifest_path, journal_path = _audit_paths(store)
    if journal_path.exists():
        raise JudgeError("RANDOM_EVENT_AUDIT_RECOVERY_REQUIRED", "random-event audit transaction requires recovery")
    if not audit_path.exists():
        if manifest_path.exists():
            manifest = store._read_json(manifest_path)
            if manifest != _default_audit_manifest():
                raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "audit manifest exists without matching audit")
        return [], _default_audit_manifest()
    try:
        manifest = store._read_json(manifest_path)
    except Exception as exc:
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "random-event audit manifest is invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != "minis.random-event-audit-manifest.v1":
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "random-event audit manifest is missing or invalid")
    records = _parse_audit_bytes(audit_path.read_bytes())
    head = records[-1]["audit_hash"] if records else None
    if int(manifest.get("record_count", -1)) != len(records) or manifest.get("head_hash") != head:
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "random-event audit manifest does not match records")
    return records, manifest


def recover_random_event_audit(store: Any) -> dict[str, Any]:
    """Finish or roll forward one journal-proven append; unknown bytes block."""
    audit_path, manifest_path, journal_path = _audit_paths(store)
    if not journal_path.exists(): return {"status": "clean", "recovered": False}
    journal = store._read_json(journal_path)
    if not isinstance(journal, dict) or journal.get("schema") != "minis.random-event-audit-transaction.v1":
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "invalid random-event audit transaction")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    old_manifest = journal["previous_manifest"]; next_manifest = journal["next_manifest"]
    current_manifest = store._read_json(manifest_path, _default_audit_manifest())
    expected = canonical_json(journal["record"]).encode("utf-8") + b"\n"
    offset = int(journal["audit_offset"]); raw = audit_path.read_bytes() if audit_path.exists() else b""
    if len(raw) < offset:
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "audit was truncated before transaction offset")
    prefix_records = _parse_audit_bytes(raw[:offset])
    prefix_head = prefix_records[-1]["audit_hash"] if prefix_records else None
    if len(prefix_records) != int(old_manifest["record_count"]) or prefix_head != old_manifest.get("head_hash"):
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "audit prefix does not match transaction head")
    suffix = raw[offset:]
    if current_manifest == next_manifest and suffix == expected:
        journal_path.unlink(); fsync_directory(journal_path.parent)
        return {"status": "reconciled_committed_audit", "recovered": True}
    if current_manifest != old_manifest:
        raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "audit manifest is neither transaction old nor new head")
    if suffix != expected:
        if not expected.startswith(suffix):
            raise JudgeError("RANDOM_EVENT_AUDIT_INTEGRITY_FAILURE", "unknown audit suffix cannot be recovered")
        with audit_path.open("r+b" if audit_path.exists() else "wb") as fh:
            fh.truncate(offset); fh.seek(offset); fh.write(expected); fh.flush(); os.fsync(fh.fileno())
    crash_failpoint("random_audit_recovery_after_append")
    store._atomic_json(manifest_path, next_manifest)
    crash_failpoint("random_audit_recovery_after_manifest")
    journal_path.unlink(); fsync_directory(journal_path.parent)
    return {"status": "reconciled_audit_transaction", "recovered": True}


def _append_audit(store: Any, record: dict[str, Any]) -> None:
    audit_path, manifest_path, journal_path = _audit_paths(store)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    records, manifest = _verified_audit(store)
    record = dict(record); record["previous_audit_hash"] = manifest.get("head_hash")
    record["audit_hash"] = sha256_json(record)
    next_manifest = {"schema": "minis.random-event-audit-manifest.v1",
                     "record_count": len(records) + 1, "head_hash": record["audit_hash"], "updated_at": now_iso()}
    journal = {"schema": "minis.random-event-audit-transaction.v1", "phase": "prepared",
               "audit_offset": audit_path.stat().st_size if audit_path.exists() else 0,
               "previous_manifest": manifest, "next_manifest": next_manifest, "record": record,
               "request_id": record.get("request_id"), "request_fingerprint": record.get("request_fingerprint"),
               "prepared_at": now_iso()}
    store._atomic_json(journal_path, journal)
    crash_failpoint("random_audit_after_journal")
    with audit_path.open("ab") as fh:
        fh.write(canonical_json(record).encode("utf-8") + b"\n"); fh.flush(); os.fsync(fh.fileno())
    crash_failpoint("random_audit_after_append")
    store._atomic_json(manifest_path, next_manifest)
    crash_failpoint("random_audit_after_manifest")
    journal_path.unlink(); fsync_directory(journal_path.parent)


def _find_audit_by_request(store: Any, request_id: str) -> dict[str, Any] | None:
    records, _ = _verified_audit(store)
    for value in records:
        if value.get("request_id") == request_id: return value
    return None

def request_random_suggestion(store: Any, pool: dict[str, Any], *, trigger: str, seed: Any, window: dict[str, Any] | None = None, expected_state_hash: str | None = None, request_id: str | None = None) -> dict[str, Any]:
    """Explicit branch request. Off mode performs no pool validation, draw, or audit."""
    with store.transaction_lock():
        settings = load_random_event_settings(store)
        if settings["mode"] == "off":
            return {"schema": DRAW_SCHEMA, "status": "off", "generated": False, "mode": "off", "suggestion": None, "draw_performed": False, "audit_written": False}
        state = store.load_state()
        if state is None: raise JudgeError(SCHEMA_ERROR, "state is required for random-event suggestion")
        if expected_state_hash and expected_state_hash != state.get("state_hash"):
            raise JudgeError(STATE_HASH_MISMATCH, "random-event suggestion source state is stale", details={"expected": expected_state_hash, "actual": state.get("state_hash")})
        pool_report = validate_random_event_pool(pool)
        if not pool_report["ok"]: raise JudgeError(SCHEMA_ERROR, "invalid random-event pool", details=pool_report)
        normalized_window = dict(window or {})
        effective_request_id = request_id or stable_id("random-request", store.branch_id, state.get("state_hash"), pool_report["pool_hash"], trigger, seed, normalized_window)
        request_fingerprint = sha256_json({"schema": "minis.random-event-request.v2", "branch_id": store.branch_id,
                                           "source_state_hash": state.get("state_hash"), "algorithm_version": ALGORITHM_VERSION,
                                           "pool_hash": pool_report["pool_hash"], "trigger": trigger, "seed": seed,
                                           "window": normalized_window})
        recovery = recover_random_event_audit(store)
        existing = _find_audit_by_request(store, effective_request_id)
        if existing is not None:
            if not existing.get("request_fingerprint"):
                raise JudgeError("RANDOM_EVENT_LEGACY_REQUEST_ID_CONFLICT", "legacy request_id has no v2 fingerprint and is reserved; use a new request_id",
                                 details={"request_id": effective_request_id, "legacy_audit_schema": existing.get("schema")})
            if existing.get("request_fingerprint") != request_fingerprint:
                raise JudgeError("RANDOM_EVENT_IDEMPOTENCY_CONFLICT", "request_id was already used with a different random-event request",
                                 details={"request_id": effective_request_id, "existing_fingerprint": existing.get("request_fingerprint"), "actual_fingerprint": request_fingerprint})
            result = dict(existing.get("result") or {})
            result.update({"mode": settings["mode"], "draw_performed": result.get("status") != "suppressed", "audit_written": False, "replayed_from_audit": True, "request_id": effective_request_id, "request_fingerprint": request_fingerprint, "audit_recovery": recovery})
            return result
        before = state.get("state_hash"); result = suggest_random_event(state, pool, trigger=trigger, seed=seed, window=normalized_window)
        if store.load_state().get("state_hash") != before: raise RuntimeError("random-event suggestion mutated canonical state")
        audit = {"schema": "minis.random-event-suggestion-audit.v2", "recorded_at": now_iso(), "request_id": effective_request_id, "request_fingerprint": request_fingerprint, "mode": settings["mode"], "branch_id": store.branch_id, "result": result}
        _append_audit(store, audit)
        result = dict(result); result.update({"mode": settings["mode"], "draw_performed": result["status"] != "suppressed", "audit_written": True, "replayed_from_audit": False, "request_id": effective_request_id, "request_fingerprint": request_fingerprint, "audit_recovery": recovery})
        return result


def make_adoption_handoff(state: dict[str, Any], suggestion: dict[str, Any], *, requested_by: str = "user") -> dict[str, Any]:
    if suggestion.get("schema") != SUGGESTION_SCHEMA or suggestion.get("canon_status") != "NON_CANONICAL_SUGGESTION":
        raise JudgeError(SCHEMA_ERROR, "adoption requires a non-canonical random-event suggestion")
    if requested_by not in {"user", "author"}: raise JudgeError("RANDOM_EVENT_ADOPTION_AUTHORITY_REQUIRED", "only user/author may request adoption")
    if suggestion.get("source_state_hash") != state.get("state_hash"):
        raise JudgeError(STATE_HASH_MISMATCH, "random-event suggestion is stale; redraw or rebuild against current state", details={"suggestion_state_hash": suggestion.get("source_state_hash"), "current_state_hash": state.get("state_hash")})
    return {"schema": HANDOFF_SCHEMA, "suggestion_id": suggestion["suggestion_id"], "requested_by": requested_by,
            "source_state_hash": state.get("state_hash"), "status": "planning_candidate_only", "canon_status": "NON_CANONICAL",
            "required_gates": ["current_state_revalidation", "Reality", "Knowledge", "PlayerAgency", "CharacterBehavior", "WorldRules", "Canon"],
            "forbidden_shortcuts": suggestion.get("forbidden_outcomes", []), "state_delta": [], "commit_authority": "judge_after_author_approval"}


def random_event_health(store: Any) -> dict[str, Any]:
    settings = load_random_event_settings(store); audit_path, _, journal_path = _audit_paths(store)
    count = 0; malformed = 0; recovery_pending = journal_path.exists()
    try:
        if recovery_pending:
            # Health is read-only: report the pending journal; explicit request
            # or recovery entry points perform reconciliation while locked.
            malformed += 1
        else:
            records, _ = _verified_audit(store); count = len(records)
            for value in records:
                result = value.get("result") or {}
                if result.get("source_state_hash") is None or value.get("branch_id") != store.branch_id: malformed += 1
                if not value.get("request_id"): malformed += 1
                if value.get("schema") == "minis.random-event-suggestion-audit.v2" and not value.get("request_fingerprint"): malformed += 1
    except Exception:
        malformed += 1
        if audit_path.exists(): count = len([x for x in audit_path.read_bytes().splitlines() if x.strip()])
    return {"status": "pass" if not malformed else "warning", "mode": settings["mode"], "scope": settings["scope"],
            "noncanonical_audit_records": count, "malformed_audit_records": malformed,
            "recovery_pending": recovery_pending, "automatic_generation": False}

def calibrate_random_event_pool(state: dict[str, Any], pool: dict[str, Any], *, trigger: str, seeds: int = 1000, window: dict[str, Any] | None = None) -> dict[str, Any]:
    seeds = max(1, min(int(seeds), 100000)); counts: dict[str, int] = {}; suppressed = 0
    for seed in range(seeds):
        result = suggest_random_event(state, pool, trigger=trigger, seed=seed, window=window)
        if result["status"] == "suppressed": key = "__suppressed__"; suppressed += 1
        elif result["status"] == "no_event": key = "__no_event__"
        else: key = result["suggestion"]["event_definition_id"]
        counts[key] = counts.get(key, 0) + 1
    return {"schema": "minis.random-event-calibration.v1", "algorithm_version": ALGORITHM_VERSION, "pool_hash": sha256_json(pool), "trigger": trigger, "seeds": seeds, "counts": dict(sorted(counts.items())), "rates": {k: v / seeds for k, v in sorted(counts.items())}, "suppressed": suppressed}
