"""Optional, author-selected original excerpts; never a style or canon verdict."""
import json
import re

from context_evidence import sha256_bytes, source_path, text_hash

ROLES = {"previous_chapter_tail", "style_original"}


def load_anchors(root, config_name, *, chapter, pov="", scene=""):
    if not config_name:
        return [], [], set(), 0
    config = json.loads(source_path(root, config_name).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema") != "minis.writing-anchors.v1":
        raise ValueError("unsupported writing anchors config")
    if set(config) - {"schema", "budget_characters", "anchors"}:
        raise ValueError("unknown writing anchors config field")
    budget = config.get("budget_characters", 2400)
    entries = config.get("anchors")
    if type(budget) is not int or budget < 0 or not isinstance(entries, list):
        raise ValueError("invalid writing anchors budget or entries")
    candidates, reports, excluded, ids = [], [], set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("anchor must be an object")
        if set(entry) - {"id", "role", "order", "file", "source_sha256", "start", "end", "tail_lines", "applies_to", "skip_reason"}:
            raise ValueError("unknown writing anchor field")
        ident, role, order = entry.get("id"), entry.get("role"), entry.get("order")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", ident) or ident in ids:
            raise ValueError("anchor id must be unique and portable")
        ids.add(ident)
        if role not in ROLES or type(order) is not int:
            raise ValueError("invalid anchor role or order")
        applies = entry.get("applies_to", {})
        if not isinstance(applies, dict) or set(applies) - {"chapters", "povs", "scenes"}:
            raise ValueError("invalid anchor applicability")
        for values in applies.values():
            if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                raise ValueError("anchor applicability must contain string arrays")
        report = {"id": ident, "role": role, "order": order, "applies_to": applies,
                  "status": "omitted", "reason": "not_applicable"}
        reports.append(report)
        name = entry.get("file")
        if name is not None:
            source_path(root, name)  # Validate even disabled paths; never follow symlinks.
            excluded.add(name)
            report["file"] = name
        disabled = entry.get("skip_reason")
        if disabled is not None:
            if disabled not in {"first_chapter", "intentional_style_change", "author_disabled"}:
                raise ValueError("invalid explicit anchor skip reason")
            report["reason"] = disabled
            continue
        if any(values and value not in values for key, value in
               (("chapters", chapter), ("povs", pov), ("scenes", scene))
               for values in [applies.get(key, [])]):
            continue
        if name is None:
            raise ValueError("active anchor requires file")
        expected = entry.get("source_sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("active anchor requires source_sha256")
        report["expected_source_sha256"] = expected
        try:
            raw = source_path(root, name).read_bytes()
        except FileNotFoundError:
            report["reason"] = "source_missing"
            continue
        actual = sha256_bytes(raw)
        report["source_sha256"] = actual
        if actual != expected:
            report["reason"] = "source_hash_mismatch"
            continue
        lines = raw.decode("utf-8").splitlines()
        if "tail_lines" in entry:
            count = entry["tail_lines"]
            if role != "previous_chapter_tail" or type(count) is not int or count < 1 or "start" in entry or "end" in entry:
                raise ValueError("invalid anchor tail range")
            start, end = max(1, len(lines) - count + 1), len(lines)
        else:
            start, end = entry.get("start"), entry.get("end")
            if type(start) is not int or type(end) is not int or start < 1 or end < start:
                raise ValueError("invalid anchor line range")
        if end > len(lines) or not lines:
            report["reason"] = "source_range_missing"
            continue
        text = "\n".join(lines[start - 1:end])
        if not text.strip():
            report["reason"] = "empty_excerpt"
            continue
        report.update(start=start, end=end, excerpt_sha256=text_hash(text), reason="pending_budget")
        candidates.append({"file": name, "start": start, "end": end, "text": text,
                           "source_sha256": actual, "excerpt_sha256": text_hash(text), "score": 0,
                           "anchor_id": ident, "anchor_role": role, "anchor_order": order})
    candidates.sort(key=lambda item: (item["anchor_order"], item["anchor_id"]))
    reports.sort(key=lambda item: (item["order"], item["id"]))
    return candidates, reports, excluded, budget


def source_id(item):
    return "anchor:" + item["anchor_id"] if "anchor_id" in item else f"{item['file']}:{item['start']}-{item['end']}"
