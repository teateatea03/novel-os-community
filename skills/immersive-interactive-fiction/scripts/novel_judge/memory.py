from __future__ import annotations

import re
from typing import Any

from .canonical import deep_copy, sha256_json, stable_id

MEMORY_SCHEMA = "minis.actor-memory.v2"


def _memory_root(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("memory", {})
    return value if isinstance(value, dict) else {}


def make_episode(actor_id: str, *, event_id: str, text: str, turn_id: str | None = None,
                 tags: list[str] | None = None, importance: int = 1,
                 location: str | None = None, tick: int | None = None,
                 visibility: str = "private") -> dict[str, Any]:
    clean = " ".join(str(text).split())
    return {
        "schema": "minis.episodic-memory.v1",
        "memory_id": stable_id("memory", actor_id, event_id, clean),
        "actor_id": actor_id, "event_id": event_id, "turn_id": turn_id,
        "text": clean, "tags": sorted({str(x).lower() for x in (tags or [])}),
        "importance": max(0, min(int(importance), 5)), "location": location,
        "tick": tick, "visibility": visibility, "source": "event",
    }


def add_episode(state: dict[str, Any], episode: dict[str, Any]) -> dict[str, Any]:
    result = deep_copy(state)
    actor_id = str(episode["actor_id"])
    root = result.setdefault("memory", {"schema": MEMORY_SCHEMA, "episodic": {}, "reflections": {}, "working": {}})
    bucket = root.setdefault("episodic", {}).setdefault(actor_id, [])
    if not any(x.get("memory_id") == episode.get("memory_id") for x in bucket if isinstance(x, dict)):
        bucket.append(deep_copy(episode))
    return result


def validate_reflection(state: dict[str, Any], reflection: dict[str, Any]) -> dict[str, Any]:
    actor_id = reflection.get("actor_id")
    evidence = list(reflection.get("evidence_memory_ids", []))
    known = {x.get("memory_id") for x in _memory_root(state).get("episodic", {}).get(actor_id, []) if isinstance(x, dict)}
    missing = sorted(str(x) for x in evidence if x not in known)
    errors = []
    if not actor_id or not str(reflection.get("text", "")).strip(): errors.append("missing_actor_or_text")
    if len(evidence) < 2: errors.append("reflection_requires_two_episodes")
    if missing: errors.append("unknown_evidence")
    return {"ok": not errors, "errors": errors, "missing_evidence": missing, "status": "candidate" if not errors else "rejected"}


def _terms(value: str) -> set[str]:
    return {x.lower() for x in re.findall(r"[\w\-\u3400-\u9fff]+", value, re.UNICODE) if len(x) > 1}


def retrieve_memories(state: dict[str, Any], actor_id: str, *, query: str = "",
                      tags: list[str] | None = None, top_k: int | None = 6,
                      include_archive: bool = False) -> list[dict[str, Any]]:
    """Deterministic recency/importance/relevance retrieval; no embedding required.

    top_k=None returns the full ranked list (lossless-addressable). Event logs
    remain the authority even when retrieval cuts a prompt-sized subset.
    """
    root = _memory_root(state)
    episodes = list(root.get("episodic", {}).get(actor_id, []) or [])
    reflections = list(root.get("reflections", {}).get(actor_id, []) or [])
    if include_archive:
        archive = (root.get("archive") or {}).get(actor_id, {}) or {}
        episodes = episodes + list(archive.get("episodes") or [])
        reflections = reflections + list(archive.get("reflections") or [])
    now_tick = int(state.get("clock", {}).get("tick", 0) or 0)
    q = _terms(query) | {str(x).lower() for x in (tags or [])}
    ranked = []
    for kind, records in (("episode", episodes), ("reflection", reflections)):
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict): continue
            if kind == "reflection" and record.get("status", "active") != "active": continue
            words = _terms(str(record.get("text", ""))) | set(record.get("tags", []))
            overlap = len(q & words)
            age = max(0, now_tick - int(record.get("tick", now_tick) or now_tick))
            recency = 1.0 / (1.0 + age / 3600.0)
            importance = float(record.get("importance", 1))
            score = overlap * 4.0 + importance + recency + (0.5 if kind == "reflection" else 0.0)
            item = filter_memory(record)
            item.update({"memory_kind": kind, "retrieval_score": round(score, 4)})
            ranked.append(item)
    ranked.sort(key=lambda x: (-x["retrieval_score"], str(x.get("memory_id") or x.get("reflection_id"))))
    if top_k is None:
        return ranked
    return ranked[:max(0, min(int(top_k), 20))]


def add_reflection(state: dict[str, Any], reflection: dict[str, Any]) -> dict[str, Any]:
    report = validate_reflection(state, reflection)
    if not report["ok"]:
        raise ValueError("invalid reflection: " + ",".join(report["errors"]))
    result = deep_copy(state)
    actor_id = str(reflection["actor_id"])
    value = deep_copy(reflection)
    value.setdefault("schema", "minis.memory-reflection.v1")
    value.setdefault("reflection_id", stable_id("reflection", actor_id, value["text"], sorted(value["evidence_memory_ids"])))
    value.setdefault("status", "active")
    value.setdefault("importance", 2)
    bucket = result.setdefault("memory", {}).setdefault("reflections", {}).setdefault(actor_id, [])
    active_text = " ".join(str(value["text"]).lower().split())
    for old in bucket:
        if isinstance(old, dict) and old.get("status", "active") == "active" and " ".join(str(old.get("text", "")).lower().split()) == active_text:
            old["status"] = "superseded"; old["superseded_by"] = value["reflection_id"]
    if not any(x.get("reflection_id") == value.get("reflection_id") for x in bucket if isinstance(x, dict)):
        bucket.append(value)
    return result


def consolidate_memory(state: dict[str, Any], actor_id: str, *, hot_episode_limit: int = 120,
                       hot_reflection_limit: int = 40) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bound retrieval state without deleting event provenance.

    Old low-importance episodes move to an archive index. Event logs remain the
    authoritative, replayable source and can regenerate every episode.
    """
    result = deep_copy(state)
    root = result.setdefault("memory", {"schema": MEMORY_SCHEMA, "episodic": {}, "reflections": {}, "working": {}, "archive": {}})
    root["schema"] = MEMORY_SCHEMA; root.setdefault("archive", {})
    episodes = list(root.setdefault("episodic", {}).get(actor_id, []))
    reflections = list(root.setdefault("reflections", {}).get(actor_id, []))
    episodes.sort(key=lambda x: (-int(x.get("importance", 1)), -int(x.get("tick", 0) or 0), str(x.get("memory_id"))))
    hot_ids = {x.get("memory_id") for x in episodes[:max(0, hot_episode_limit)]}
    hot = [x for x in episodes if x.get("memory_id") in hot_ids]
    archived = [x for x in episodes if x.get("memory_id") not in hot_ids]
    active_reflections = [x for x in reflections if x.get("status", "active") == "active"]
    stale_reflections = [x for x in reflections if x.get("status", "active") != "active"]
    active_reflections.sort(key=lambda x: (-int(x.get("importance", 1)), -int(x.get("tick", 0) or 0), str(x.get("reflection_id"))))
    kept_reflections = active_reflections[:max(0, hot_reflection_limit)]
    stale_reflections += active_reflections[max(0, hot_reflection_limit):]
    root["episodic"][actor_id] = hot
    root["reflections"][actor_id] = kept_reflections
    archive = root["archive"].setdefault(actor_id, {"episodes": [], "reflections": []})
    known_ep = {x.get("memory_id") for x in archive["episodes"] if isinstance(x, dict)}
    archive["episodes"].extend(filter_memory(x) for x in archived if x.get("memory_id") not in known_ep)
    known_rf = {x.get("reflection_id") for x in archive["reflections"] if isinstance(x, dict)}
    archive["reflections"].extend(filter_memory(x) for x in stale_reflections if x.get("reflection_id") not in known_rf)
    report = {"schema": "minis.memory-consolidation-report.v1", "actor_id": actor_id,
              "hot_episodes": len(hot), "archived_episodes": len(archived),
              "hot_reflections": len(kept_reflections), "archived_reflections": len(stale_reflections),
              "event_source_preserved": True}
    return result, report


def memory_health(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    root = _memory_root(state); episodes = root.get("episodic", {}).get(actor_id, []); reflections = root.get("reflections", {}).get(actor_id, [])
    episode_ids = {x.get("memory_id") for x in episodes if isinstance(x, dict)}
    broken = []
    for ref in reflections if isinstance(reflections, list) else []:
        missing = sorted(str(x) for x in ref.get("evidence_memory_ids", []) if x not in episode_ids)
        if missing: broken.append({"reflection_id": ref.get("reflection_id"), "missing_evidence": missing})
    return {"status": "pass" if not broken else "warn", "actor_id": actor_id, "episodes": len(episodes), "reflections": len(reflections), "broken_reflections": broken}


def filter_memory(record: dict[str, Any]) -> dict[str, Any]:
    allowed = {"memory_id", "reflection_id", "event_id", "turn_id", "text", "tags", "importance", "location", "tick", "evidence_memory_ids"}
    return {k: deep_copy(v) for k, v in record.items() if k in allowed}


def compile_memory_context(state: dict[str, Any], actor_id: str, *, query: str = "",
                           top_k: int | None = 6, include_archive: bool = False) -> dict[str, Any]:
    memories = retrieve_memories(state, actor_id, query=query, top_k=top_k,
                                 include_archive=include_archive)
    return {"schema": "minis.memory-context.v1", "actor_id": actor_id, "query": query,
            "memories": memories, "retrieval_cut": top_k is not None,
            "include_archive": bool(include_archive),
            "source_state_hash": state.get("state_hash"),
            "context_hash": sha256_json(memories)}
