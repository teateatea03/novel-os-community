from __future__ import annotations

"""Deterministic repetition/loop detection for generated prose.

This is a safety gate, not a style judge. It intentionally ignores very short
replies and does not ban a single deliberate repeated word or dialogue echo.
It catches repeated sentence blocks, duplicated long units, and token-loop-like
character shingles before a candidate can reach canonical commit.
"""

import re
from collections import Counter
from typing import Any

_SENTENCE = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?", re.UNICODE)
_SPACE = re.compile(r"\s+")
_WRAPPER = re.compile(r"^[\s「」『』\"“”'‘’、，,。.!！？?：:；;（）()\[\]{}]+|[\s「」『』\"“”'‘’、，,。.!！？?：:；;（）()\[\]{}]+$", re.UNICODE)


def normalize_unit(value: str) -> str:
    value = _SPACE.sub(" ", str(value).strip()).lower()
    return _WRAPPER.sub("", value)


def split_units(text: str) -> list[str]:
    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n+", str(text)):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        found = [x.strip() for x in _SENTENCE.findall(paragraph) if x.strip()]
        units.extend(found or [paragraph])
    return units


def _loop_blocks(units: list[str]) -> list[dict[str, Any]]:
    normalized = [normalize_unit(x) for x in units]
    results: list[dict[str, Any]] = []
    n = len(normalized)
    # Three or four consecutive copies are strong evidence of a decoder loop.
    for start in range(n):
        for size in range(1, min(4, (n - start) // 3 + 1)):
            block = normalized[start:start + size]
            if not block or sum(len(x) for x in block) < 12:
                continue
            copies = 1
            while start + (copies + 1) * size <= n and normalized[start + copies * size:start + (copies + 1) * size] == block:
                copies += 1
            if copies >= 3:
                results.append({"start": start, "unit_count": size, "copies": copies,
                                "text": " ".join(block)[:240]})
    # Keep the largest non-overlapping-looking evidence first.
    results.sort(key=lambda x: (-x["copies"], -x["unit_count"], x["start"]))
    unique: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int]] = set()
    for item in results:
        key = (item["start"], item["unit_count"], item["copies"])
        if key not in seen:
            seen.add(key); unique.append(item)
    return unique[:8]


def _long_duplicate_units(units: list[str]) -> list[dict[str, Any]]:
    normalized = [normalize_unit(x) for x in units]
    positions: dict[str, list[int]] = {}
    for i, value in enumerate(normalized):
        if len(value) >= 20:
            positions.setdefault(value, []).append(i)
    result = []
    for value, indexes in positions.items():
        if len(indexes) >= 2:
            result.append({"text": value[:240], "count": len(indexes), "positions": indexes[:8], "length": len(value)})
    return sorted(result, key=lambda x: (-x["count"], -x["length"], x["positions"][0]))[:8]


def _ngram_hotspots(text: str, size: int = 18) -> list[dict[str, Any]]:
    compact = re.sub(r"\s+", "", str(text).lower())
    if len(compact) < 260:
        return []
    counts: Counter[str] = Counter(compact[i:i + size] for i in range(len(compact) - size + 1))
    return [{"ngram": x[:80], "count": n} for x, n in counts.most_common(8) if n >= 4]


def detect_repetition(text: str, *, allow_short: bool = True) -> dict[str, Any]:
    value = str(text or "")
    units = split_units(value)
    normalized = [normalize_unit(x) for x in units if normalize_unit(x)]
    chars = len(re.sub(r"\s+", "", value))
    duplicate_units = _long_duplicate_units(units)
    loop_blocks = _loop_blocks(units)
    hotspots = _ngram_hotspots(value)
    findings: list[dict[str, Any]] = []

    # Do not reject tiny dialogue replies such as 「好。好。」. A repeated
    # three-unit decoder loop is still suspicious even when the total sample
    # is short, so it is checked once there is enough evidence for a block.
    if not (allow_short and chars < 40):
        if loop_blocks:
            findings.append({"code": "REPETITION_LOOP", "severity": "P0", "evidence": loop_blocks[0]})
        elif duplicate_units and duplicate_units[0]["count"] >= 2 and duplicate_units[0]["length"] >= 48:
            findings.append({"code": "DUPLICATE_LONG_CONTENT", "severity": "P1", "evidence": duplicate_units[0]})
        elif hotspots and chars >= 420:
            findings.append({"code": "REPETITION_NGRAM_HOTSPOT", "severity": "P1", "evidence": hotspots[0]})
        elif duplicate_units:
            findings.append({"code": "DUPLICATE_CONTENT_WARNING", "severity": "WARN", "evidence": duplicate_units[0]})

    status = "fail" if any(x["severity"] == "P0" for x in findings) else ("warn" if findings else "pass")
    return {"schema": "minis.repetition-report.v1", "status": status,
            "text_chars": chars, "unit_count": len(normalized),
            "unique_unit_ratio": round(len(set(normalized)) / max(1, len(normalized)), 4),
            "duplicate_units": duplicate_units, "loop_blocks": loop_blocks,
            "ngram_hotspots": hotspots, "findings": findings}


def validate_no_repetition(text: str) -> list[dict[str, Any]]:
    report = detect_repetition(text)
    return [{"code": x["code"], "severity": x["severity"], "details": x["evidence"]}
            for x in report["findings"] if x["severity"] != "WARN"]
