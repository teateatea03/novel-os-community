from __future__ import annotations

"""Deterministic token-aware context admission for Novel OS.

The host, not the model, owns Astra-style memory: never summarize details away.
Default policy is lossless-addressable for every model. Window size only decides
how much original text is inlined this turn; overflow stays addressable by id/hash.
lossy-admission is an explicit opt-in for experiments, never the Novel OS default.
"""

import os
import json
import re
from typing import Any

from .canonical import sha256_json

CONTEXT_WINDOW_64K = 65536
CONTEXT_WINDOW_LARGE = 1_050_000
POLICY_LOSSY = "lossy-admission"
POLICY_LOSSLESS = "lossless-addressable"
DEFAULT_CONTEXT_POLICY = POLICY_LOSSLESS

# Budgets are total request envelopes. input_budget is derived so output and
# uncertainty are never silently consumed by prompt content.
PROFILES: dict[str, dict[str, int]] = {
    "interactive": {"system": 4000, "output": 8000, "safety": 4000},
    "plan": {"system": 3500, "output": 5000, "safety": 3500},
    "render": {"system": 4000, "output": 8000, "safety": 4000},
    "research": {"system": 4000, "output": 6000, "safety": 4000},
    "blind_read": {"system": 4000, "output": 6000, "safety": 4000},
}

_CJK = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_WORD = re.compile(r"[A-Za-z0-9_]+")


def default_context_window() -> int:
    """64K unless the host exports a larger model envelope."""
    raw = os.environ.get("NOVEL_OS_CONTEXT_WINDOW") or os.environ.get("NOVEL_OS_MODEL_CONTEXT_WINDOW")
    if raw and str(raw).strip().isdigit():
        value = int(str(raw).strip())
        if value > 0:
            return value
    return CONTEXT_WINDOW_64K


def default_context_policy() -> str:
    """Lossless for every model unless the host explicitly opts into lossy."""
    raw = os.environ.get("NOVEL_OS_CONTEXT_POLICY")
    if raw:
        return context_policy_for_window(default_context_window(), raw)
    return DEFAULT_CONTEXT_POLICY


def context_policy_for_window(context_window: int, explicit: str | None = None) -> str:
    """Select admission policy. Explicit always wins; otherwise lossless.

    Window size never switches Novel OS onto a forgetting path. A 9B/64K model
    still keeps overflow addressable; it just inlines less this turn.
    """
    if explicit:
        policy = str(explicit).strip().lower().replace("_", "-")
        if policy in {"lossy", "lossy-admission", "compressed"}:
            return POLICY_LOSSY
        if policy in {"lossless", "lossless-addressable", "astra", "addressable"}:
            return POLICY_LOSSLESS
        raise ValueError(f"unsupported context policy: {explicit}")
    return default_context_policy()


def estimate_tokens(value: Any, *, tokenizer_kind: str = "conservative-v1") -> int:
    """Estimate tokens without requiring a model-specific tokenizer.

    CJK characters are counted conservatively; ASCII words and punctuation use
    a separate estimate. The estimate is deliberately an upper bound suitable
    for admission, not a claim about the endpoint's exact tokenizer.
    """
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    text = str(value)
    cjk = len(_CJK.findall(text))
    words_found = _WORD.findall(text)
    remaining = max(0, len(text) - cjk)
    word_chars = sum(len(x) for x in words_found)
    punctuation = max(0, remaining - word_chars)
    ascii_tokens = sum(max(1, (len(x) + 3) // 4) for x in words_found)
    estimate = cjk * 1.6 + ascii_tokens + punctuation / 3.0
    return max(1, int(estimate + 0.9999))


def _profile(name: str, context_window: int, output_reserve: int | None,
             safety_margin: int | None) -> dict[str, int]:
    base = dict(PROFILES.get(name, PROFILES["interactive"]))
    output = int(output_reserve if output_reserve is not None else base["output"])
    safety = int(safety_margin if safety_margin is not None else base["safety"])
    system = int(base["system"])
    input_budget = int(context_window) - system - output - safety
    if input_budget < 1:
        raise ValueError("context window cannot fit system/output/safety reservation")
    return {"context_window": int(context_window), "system_reserve": system,
            "output_reserve": output, "safety_margin": safety,
            "input_budget": input_budget}


def _compact(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _display_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _source(raw: dict[str, Any], index: int, *, preserve_text: bool = False) -> dict[str, Any]:
    value = dict(raw)
    sid = str(value.get("source_id") or value.get("id") or f"source-{index:04d}")
    tier = str(value.get("tier") or "EVIDENCE").upper()
    if tier not in {"CORE", "ACTIVE", "EVIDENCE", "ARCHIVE"}:
        tier = "EVIDENCE"
    text = value.get("text", "")
    if preserve_text:
        rendered = text
        tokens = estimate_tokens(text)
        return {"source_id": sid, "tier": tier, "priority": int(value.get("priority", 0)),
                "required": bool(value.get("required", False)), "text": rendered,
                "original_tokens": tokens, "estimated_tokens": tokens,
                "compression_applied": False, "content_hash": sha256_json(text),
                "provenance": value.get("provenance", {})}
    compact = _compact(text)
    return {"source_id": sid, "tier": tier, "priority": int(value.get("priority", 0)),
            "required": bool(value.get("required", False)), "text": compact,
            "original_tokens": estimate_tokens(text), "estimated_tokens": estimate_tokens(compact),
            "compression_applied": compact != _display_text(text),
            "content_hash": sha256_json(compact),
            "provenance": value.get("provenance", {})}


def _overflow_record(item: dict[str, Any]) -> dict[str, Any]:
    return {"source_id": item["source_id"], "tier": item["tier"],
            "estimated_tokens": item["estimated_tokens"],
            "content_hash": item.get("content_hash"),
            "provenance": item.get("provenance", {}), "inline": False}


def admit_sources(sources: list[dict[str, Any]], *, profile: str = "interactive",
                  context_window: int = CONTEXT_WINDOW_64K,
                  output_reserve: int | None = None,
                  safety_margin: int | None = None,
                  context_policy: str | None = None) -> dict[str, Any]:
    """Select sources deterministically and return an auditable admission record."""
    policy = context_policy_for_window(context_window, context_policy)
    preserve = policy == POLICY_LOSSLESS
    budget = _profile(profile, context_window, output_reserve, safety_margin)
    prepared = [_source(x, i, preserve_text=preserve) for i, x in enumerate(sources)]
    required = [x for x in prepared if x["required"]]
    if sum(x["estimated_tokens"] for x in required) > budget["input_budget"]:
        return {"schema": "minis.context-admission.v1", "status": "reject",
                "admission": "reject", **budget, "profile": profile,
                "context_policy": policy,
                "detail_preservation": "verbatim" if preserve else "whitespace-compacted",
                "tokenizer_kind": "conservative-v1", "selected_sources": [],
                "evicted_sources": [x["source_id"] for x in prepared],
                "addressable_overflow": [],
                "forgotten_sources": [x["source_id"] for x in prepared],
                "compression_records": [], "reason": "required_sources_exceed_input_budget"}

    tier_order = {"CORE": 0, "ACTIVE": 1, "EVIDENCE": 2, "ARCHIVE": 3}
    ordered = sorted(prepared, key=lambda x: (tier_order[x["tier"]], -x["priority"], x["source_id"]))
    selected: list[dict[str, Any]] = []
    overflow: list[dict[str, Any]] = []
    used = 0
    for item in ordered:
        cost = item["estimated_tokens"]
        if item["required"] or used + cost <= budget["input_budget"]:
            selected.append(item)
            used += cost
        else:
            overflow.append(item)
    selected_ids = {x["source_id"] for x in selected}
    if policy == POLICY_LOSSLESS:
        evicted: list[str] = []
        forgotten: list[str] = []
        addressable = [_overflow_record(x) for x in overflow]
        status = "pass" if not overflow else "addressable_pass"
        records: list[dict[str, Any]] = []
    else:
        evicted = [x["source_id"] for x in prepared if x["source_id"] not in selected_ids]
        forgotten = list(evicted)
        addressable = []
        status = "pass" if not evicted else "compressed_pass"
        records = [{"source_id": x["source_id"], "original_tokens": x["original_tokens"],
                    "estimated_tokens": x["estimated_tokens"]} for x in selected if x["compression_applied"]]
    return {"schema": "minis.context-admission.v1", "status": status, "admission": status,
            **budget, "profile": profile, "context_policy": policy,
            "detail_preservation": "verbatim" if preserve else "whitespace-compacted",
            "tokenizer_kind": "conservative-v1",
            "estimated_tokens": used, "selected_sources": [x["source_id"] for x in selected],
            "evicted_sources": evicted, "addressable_overflow": addressable,
            "forgotten_sources": forgotten, "compression_records": records,
            "source_manifest_hash": sha256_json([{k: x[k] for k in ("source_id", "tier", "priority", "required", "estimated_tokens", "provenance")} for x in prepared]),
            "context_hash": sha256_json([{k: x[k] for k in ("source_id", "text")} for x in selected])}


def render_admitted_sources(sources: list[dict[str, Any]], admission: dict[str, Any]) -> str:
    preserve = admission.get("context_policy") == POLICY_LOSSLESS or admission.get("detail_preservation") == "verbatim"
    selected = set(admission.get("selected_sources", []))
    rows = []
    for i, raw in enumerate(sources):
        item = _source(raw, i, preserve_text=preserve)
        if item["source_id"] in selected:
            rows.append(f"<source id=\"{item['source_id']}\" tier=\"{item['tier']}\">\n{_display_text(item['text'])}\n</source>")
    catalog = admission.get("addressable_overflow") or []
    if catalog:
        lines = ["<addressable-overflow>"]
        for row in catalog:
            lines.append(
                f'<ref id="{row.get("source_id")}" tier="{row.get("tier")}" '
                f'hash="{row.get("content_hash")}" tokens="{row.get("estimated_tokens")}" inline="false" />'
            )
        lines.append("</addressable-overflow>")
        rows.append("\n".join(lines))
    return "\n\n".join(rows)


def _context_sources(context: dict[str, Any], *, explode_memories: bool) -> list[dict[str, Any]]:
    """Turn a context pack into admission sources.

    Lossless windows explode episodic memories so overflow stays addressable
    instead of dropping the whole memory blob.
    """
    tier_map = {"schema": "CORE", "audience": "CORE", "actor_id": "CORE", "provenance": "CORE",
                "self": "ACTIVE", "clock": "ACTIVE", "reality_card": "ACTIVE",
                "cognitive_budget": "ACTIVE", "location": "ACTIVE", "actors": "ACTIVE",
                "objects": "ACTIVE", "world_public": "ACTIVE", "relations": "ACTIVE",
                "storylets": "ACTIVE", "threads": "ACTIVE", "facts": "ACTIVE",
                "memory_context": "EVIDENCE", "legacy_knowledge": "EVIDENCE",
                "production_read_model": "EVIDENCE", "excluded": "CORE",
                "author_corrections": "CORE", "author_correction_notes": "CORE",
                "selected_source_ids": "EVIDENCE", "addressable_source_ids": "CORE"}
    required = {"schema", "audience", "actor_id", "provenance", "reality_card", "self", "addressable_source_ids"}
    hot = {"schema", "provenance", "reality_card", "self", "addressable_source_ids"}
    sources: list[dict[str, Any]] = []
    for key, value in context.items():
        if key == "context_hash":
            continue
        if explode_memories and key == "memory_context" and isinstance(value, dict):
            memories = value.get("memories") or []
            meta = {k: v for k, v in value.items() if k != "memories"}
            sources.append({
                "source_id": "context.memory_context.meta",
                "tier": "EVIDENCE",
                "priority": 40,
                "required": False,
                "text": {"memory_context_meta": meta},
                "provenance": {"field": "memory_context", "part": "meta"},
            })
            for index, memory in enumerate(memories):
                if not isinstance(memory, dict):
                    continue
                mid = str(memory.get("memory_id") or memory.get("reflection_id") or f"memory-{index:04d}")
                sources.append({
                    "source_id": f"memory.{mid}",
                    "tier": "EVIDENCE",
                    "priority": max(1, int(memory.get("importance", 1)) * 10),
                    "required": False,
                    "text": memory,
                    "provenance": {"field": "memory_context", "memory_id": mid},
                })
            continue
        sources.append({
            "source_id": f"context.{key}",
            "tier": tier_map.get(key, "EVIDENCE"),
            "priority": 100 if key in hot else 10,
            "required": key in required,
            "text": {key: value},
            "provenance": {"field": key},
        })
    return sources


def admit_context_dict(context: dict[str, Any], *, profile: str = "interactive",
                       context_window: int = CONTEXT_WINDOW_64K,
                       context_policy: str | None = None) -> dict[str, Any]:
    """Admit a structured context by top-level field, preserving selected fields."""
    policy = context_policy_for_window(context_window, context_policy)
    explode = policy == POLICY_LOSSLESS
    sources = _context_sources(context, explode_memories=explode)
    admission = admit_sources(sources, profile=profile, context_window=context_window,
                              context_policy=policy)
    selected = set(admission.get("selected_sources", []))
    result = {key: value for key, value in context.items()
              if key != "context_hash" and f"context.{key}" in selected}
    if explode and isinstance(context.get("memory_context"), dict):
        original = context["memory_context"]
        kept = []
        overflow_ids = []
        for memory in original.get("memories") or []:
            if not isinstance(memory, dict):
                continue
            mid = str(memory.get("memory_id") or memory.get("reflection_id") or "")
            if f"memory.{mid}" in selected:
                kept.append(memory)
            else:
                overflow_ids.append(mid)
        meta = {k: v for k, v in original.items() if k != "memories"}
        if "context.memory_context.meta" in selected or kept:
            rebuilt = dict(meta)
            rebuilt["memories"] = kept
            rebuilt["inline_memory_ids"] = [x.get("memory_id") for x in kept if x.get("memory_id")]
            rebuilt["addressable_overflow_ids"] = overflow_ids
            rebuilt["retrieval_cut"] = False
            result["memory_context"] = rebuilt
        if overflow_ids and not result.get("addressable_source_ids"):
            result["addressable_source_ids"] = list(context.get("addressable_source_ids") or []) or overflow_ids
    result["context_admission"] = admission
    result["context_hash"] = sha256_json({k: v for k, v in result.items() if k != "context_hash"})
    return result
