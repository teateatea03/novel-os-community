from __future__ import annotations

from typing import Any

from .canonical import deep_copy, sha256_json


def state_diff(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    """Deterministic JSON-like diff used for audit and graph proposals."""
    if type(before) is not type(after):
        return [{"path": path or "/", "before": deep_copy(before), "after": deep_copy(after)}]
    if isinstance(before, dict):
        out: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            child = f"{path}/{key}" if path else f"/{key}"
            if key not in before:
                out.append({"path": child, "before": None, "after": deep_copy(after[key])})
            elif key not in after:
                out.append({"path": child, "before": deep_copy(before[key]), "after": None})
            else:
                out.extend(state_diff(before[key], after[key], child))
        return out
    if isinstance(before, list):
        out = []
        for index in range(max(len(before), len(after))):
            child = f"{path}/{index}" if path else f"/{index}"
            if index >= len(before):
                out.append({"path": child, "before": None, "after": deep_copy(after[index])})
            elif index >= len(after):
                out.append({"path": child, "before": deep_copy(before[index]), "after": None})
            else:
                out.extend(state_diff(before[index], after[index], child))
        return out
    return [] if before == after else [{"path": path or "/", "before": before, "after": after}]


def affected_entities(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"actors": [], "objects": [], "locations": [], "relations": [], "facts": [], "other": []}
    for change in state_diff(before, after):
        parts = [p for p in change["path"].split("/") if p]
        bucket = {"actors": "actors", "world_truth": "other", "relations": "relations", "knowledge": "facts"}.get(parts[0], "other") if parts else "other"
        if parts[:2] == ["world_truth", "objects"]: bucket = "objects"
        if parts[:2] == ["world_truth", "locations"]: bucket = "locations"
        if len(parts) > 1 and parts[0] in {"actors", "relations"}:
            result[bucket].append(parts[1])
        elif len(parts) > 2 and parts[:2] == ["world_truth", "objects"]:
            result[bucket].append(parts[2])
        elif len(parts) > 2 and parts[:2] == ["world_truth", "locations"]:
            result[bucket].append(parts[2])
        elif len(parts) > 2 and parts[0] == "knowledge":
            result[bucket].append(parts[2])
    for key in result:
        result[key] = sorted(set(result[key]))
    result["fingerprint"] = [sha256_json(result)]
    return result
