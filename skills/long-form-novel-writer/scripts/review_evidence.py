#!/usr/bin/env python3
"""Deterministic anchor checks; never a semantic verdict or author acceptance."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

SCHEMA = "minis.novel-review.v2"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8"))


def source_path(root, name):
    """Only canonical project-relative identities; never follow symlinks."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid source identity")
    rel = PurePosixPath(name)
    if rel.as_posix() != name or rel.is_absolute() or any(p in {".", ".."} for p in name.split("/")):
        raise ValueError("source must be project relative")
    name.encode("utf-8")
    root = Path(root).resolve()
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink source is unsupported")
    path.resolve().relative_to(root)
    return path


def capture_source(root, name, limit=None, normalize=False):
    raw = source_path(root, name).read_bytes()
    text = raw.decode("utf-8")
    if normalize:
        text = "\n".join(text.splitlines())
    end = len(text) if limit is None else min(len(text), limit)
    return {"file": name, "sha256": digest(raw), "text": text,
            "ranges": [[0, end]]}


def source_binding(sources):
    return [{"file": name, "sha256": source["sha256"],
             "ranges": copy.deepcopy(source["ranges"])}
            for name, source in sorted(sources.items())]


def consolidate_binding(binding):
    """Merge repeated file/hash records; retain conflicting hashes for validation."""
    merged = {}
    for item in binding:
        key = (item["file"], item["sha256"])
        if key not in merged:
            merged[key] = {"file": item["file"], "sha256": item["sha256"], "ranges": []}
        for span in item["ranges"]:
            if span not in merged[key]["ranges"]:
                merged[key]["ranges"].append(copy.deepcopy(span))
    return list(merged.values())


def check_binding(root, binding):
    problems = []
    if not isinstance(binding, list) or not binding:
        return {"status": "unverified", "problems": ["missing source binding"]}
    # Invocation-local only: pre-model, post-model and reuse each read afresh.
    current_hashes = {}
    for item in binding:
        try:
            name = item["file"]
            if not isinstance(name, str):
                raise ValueError("invalid source identity")
            if name not in current_hashes:
                try:
                    current_hashes[name] = digest(source_path(root, name).read_bytes())
                except (OSError, ValueError):
                    current_hashes[name] = None
            current = current_hashes[name]
            if current is None:
                raise ValueError("source missing or invalid")
            # Check every expected fingerprint, including conflicting duplicates.
            if current != item["sha256"]:
                problems.append({"file": name, "reason": "source_changed"})
        except (OSError, ValueError, KeyError, TypeError):
            problems.append({"file": item.get("file") if isinstance(item, dict) else None,
                             "reason": "source_missing_or_invalid"})
    return {"status": "stale" if problems else "current", "problems": problems}


def validate_anchor(evidence, sources):
    result = {"status": "unverified"}
    if not isinstance(evidence, dict):
        return dict(result, reason="malformed_evidence")
    name, line, quote = (evidence.get(k) for k in ("file", "line", "quote"))
    if (not isinstance(name, str) or type(line) is not int or line < 1
            or not isinstance(quote, str) or not quote.strip()):
        return dict(result, reason="malformed_evidence")
    source = sources.get(name)
    if source is None:
        return dict(result, reason="source_not_loaded")
    text = source["text"]
    # Count overlapping occurrences too. A line number cannot rescue an ambiguous quote.
    first = text.find(quote)
    if first < 0:
        return dict(result, reason="quote_not_found")
    if text.find(quote, first + 1) >= 0:
        return dict(result, reason="ambiguous_quote")
    if text.count("\n", 0, first) + 1 != line:
        return dict(result, reason="line_mismatch")
    end = first + len(quote)
    if not any(start <= first and end <= stop for start, stop in source["ranges"]):
        return dict(result, reason="quote_not_in_prompt")
    return {"status": "anchored", "file": name, "line": line,
            "start_char": first, "end_char": end, "source_sha256": source["sha256"]}


def validate_report(data, sources, draft_file):
    """Return separate machine checks; leave the original model payload untouched."""
    errors = []
    if not isinstance(data, dict):
        return {"status": "unverified", "errors": ["report must be an object"], "findings": []}
    if not isinstance(data.get("summary"), str):
        errors.append("summary must be a string")
    if not isinstance(data.get("questions"), list):
        errors.append("questions must be an array")
    issues = data.get("issues")
    if not isinstance(issues, list):
        return {"status": "unverified", "errors": errors + ["issues must be an array"], "findings": []}
    findings = []
    for index, issue in enumerate(issues):
        checks = []
        valid = isinstance(issue, dict)
        if valid:
            valid = (isinstance(issue.get("category"), str) and issue.get("category") in {"time", "fact", "knowledge", "motivation", "pov", "world", "reader", "style"}
                     and isinstance(issue.get("severity"), str) and issue.get("severity") in {"P0", "P1", "P2"}
                     and all(isinstance(issue.get(k), str) and issue[k].strip() for k in ("claim", "minimal_fix"))
                     and type(issue.get("confidence")) in (int, float)
                     and 0 <= issue["confidence"] <= 1 and math.isfinite(issue["confidence"]))
            checks = [validate_anchor(issue.get(k), sources) for k in ("evidence_a", "evidence_b")]
        if not valid:
            errors.append(f"issues[{index}] has malformed or missing fields")
        anchored = valid and all(c["status"] == "anchored" for c in checks)
        if anchored and checks[0]["file"] == checks[1]["file"] and (
                checks[0]["start_char"] <= checks[1]["start_char"]
                and checks[1]["end_char"] <= checks[0]["end_char"]
                or checks[1]["start_char"] <= checks[0]["start_char"]
                and checks[0]["end_char"] <= checks[1]["end_char"]):
            anchored = False
            checks.append({"status": "unverified", "reason": "duplicate_evidence"})
        identity = {"draft": sources[draft_file]["sha256"], "draft_file": draft_file, "issue": issue}
        findings.append({"finding_id": object_digest(identity), "issue_index": index,
                         "status": "anchored" if anchored else "unverified",
                         "shape_valid": bool(valid), "anchors": checks,
                         "semantic_status": "unverified", "resolution": "unresolved",
                         "decision_source": "machine_suggestion"})
    return {"status": "checked" if not errors else "unverified", "errors": errors, "findings": findings}


def make_report(data, sources, draft_file, role, model, raw_file, prompt, context_receipt):
    # Compatibility: callers can still read summary/issues/questions, but must recognize v2.
    report = {key: copy.deepcopy(data[key]) for key in ("summary", "issues", "questions")
              if isinstance(data, dict) and key in data}
    report.update({"schema": SCHEMA, "role": role, "model": model,
                   "status": "machine_suggestion", "raw_file": raw_file,
                   "machine_suggestion": copy.deepcopy(data),
                   "draft": {"file": draft_file, "sha256": sources[draft_file]["sha256"]},
                   "source_binding": source_binding(sources),
                   "prompt_sha256": digest(prompt.encode("utf-8")),
                   "context_receipt": context_receipt,
                   "validation": validate_report(data, sources, draft_file)})
    return report


def recheck_report(root, report):
    """Read-only reuse check. Does not mark findings resolved after any manuscript edit."""
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        return {"status": "unverified", "problems": ["legacy or unsupported review schema"]}
    if report.get("status") != "machine_suggestion" or not isinstance(report.get("validation"), dict):
        return {"status": "unverified", "problems": ["not a completed machine review"]}
    result = check_binding(root, report.get("source_binding"))
    result["scope"] = "source_freshness_only_not_semantic_acceptance"
    return result
