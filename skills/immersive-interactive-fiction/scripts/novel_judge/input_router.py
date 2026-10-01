from __future__ import annotations

"""Deterministic intent routing with fail-closed ambiguity handling."""

import re
from typing import Any

from .canonical import stable_id

META_STATUS = ("狀態", "目前狀況", "進度", "status", "where are we")
META_OPTIONS = ("選項", "能做什麼", "可做什麼", "options", "what can i do")
META_REVISION = ("重寫", "修改前文", "撤回", "回溯", "rewrite", "revise", "undo")
TIME_SKIP = ("跳到", "快轉", "隔天", "幾小時後", "time skip", "skip to")
WORLD_VERBS = ("走", "去", "拿", "放", "看", "問", "說", "等", "吃", "喝", "開", "關", "躲", "摸", "坐", "站", "move", "go", "take", "ask", "wait", "open", "close")


def classify_input(raw_input: str) -> dict[str, Any]:
    text = " ".join(str(raw_input).strip().split())
    low = text.lower()
    candidates: list[dict[str, Any]] = []
    def add(kind: str, confidence: float, reason: str) -> None:
        candidates.append({"kind": kind, "confidence": confidence, "reason": reason})
    if any(x in low for x in META_REVISION): add("meta_revision", 0.96, "revision marker")
    if any(x in low for x in META_STATUS): add("meta_status", 0.94, "status marker")
    if any(x in low for x in META_OPTIONS): add("meta_options", 0.94, "options marker")
    if any(x in low for x in TIME_SKIP): add("time_skip", 0.92, "time-skip marker")
    if any(x in low for x in WORLD_VERBS) or re.match(r"^[「『\"']", text): add("world_action", 0.72, "action or dialogue marker")
    if len(text) <= 2 or low in {"繼續", "續", "好", "可以", "那個", "continue", "ok", "yes", "no"}:
        add("ambiguous_intent", 0.99, "deictic or underspecified input")
    if not candidates:
        add("ambiguous_intent", 0.95, "no deterministic intent marker")
    candidates.sort(key=lambda x: (-x["confidence"], x["kind"]))
    substantive = [x for x in candidates if x["kind"] != "ambiguous_intent" and x["confidence"] >= 0.85]
    conflict = len({x["kind"] for x in substantive}) > 1
    ambiguous = candidates[0]["kind"] == "ambiguous_intent" or conflict
    kind = "ambiguous_intent" if ambiguous else candidates[0]["kind"]
    prompt = None
    if ambiguous:
        names = [x["kind"] for x in substantive[:3]]
        prompt = "你要修改／查詢系統狀態，還是讓角色在世界中行動？" if names else "請補一個動作、對象或你要查詢／修改的內容。"
    return {
        "schema": "minis.input-routing.v1", "routing_id": stable_id("routing", text),
        "raw_input": text, "kind": kind, "confidence": candidates[0]["confidence"],
        "candidates": candidates[:5], "ambiguous": ambiguous,
        "advance_world": kind in {"world_action", "time_skip"} and not ambiguous,
        "requires_clarification": ambiguous, "clarification_prompt": prompt,
    }


def resolve_extractor_candidates(raw_input: str, candidates: list[dict[str, Any]], *, min_confidence: float = 0.72, margin: float = 0.12) -> dict[str, Any]:
    valid = [x for x in candidates if isinstance(x, dict) and x.get("type") and isinstance(x.get("confidence"), (int, float))]
    valid.sort(key=lambda x: (-float(x["confidence"]), str(x["type"])))
    if not valid or float(valid[0]["confidence"]) < min_confidence:
        return {**classify_input(raw_input), "kind": "ambiguous_intent", "advance_world": False, "requires_clarification": True}
    if len(valid) > 1 and float(valid[0]["confidence"]) - float(valid[1]["confidence"]) < margin and valid[0]["type"] != valid[1]["type"]:
        return {**classify_input(raw_input), "kind": "ambiguous_intent", "advance_world": False, "requires_clarification": True, "extractor_candidates": valid[:3]}
    return {"schema": "minis.input-routing.v1", "raw_input": raw_input, "kind": "world_action", "confidence": float(valid[0]["confidence"]), "selected": valid[0], "ambiguous": False, "advance_world": True, "requires_clarification": False, "clarification_prompt": None}
