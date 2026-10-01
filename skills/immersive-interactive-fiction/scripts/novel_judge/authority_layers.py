from __future__ import annotations

"""Authority layers for Novel Judge.

A single PASS must never mean all of:
- safe to commit canon
- free of narrative bugs
- editorially strong
- readers will like it
- author prefers this version

Layers are intentionally separate so host policy can decide which
findings block commit, which open tickets, and which only advise.
"""

from typing import Any

from .canonical import now_iso, sha256_json

SCHEMA = "minis.authority-layer-report.v1"
LAYER_SCHEMA = "minis.authority-layer.v1"

LAYERS = (
    "CANON_INTEGRITY",
    "NARRATIVE_QA",
    "EDITORIAL_DIAGNOSIS",
    "READER_RESPONSE",
    "AUTHOR_DECISION",
)

# Default host policy: only canon integrity hard-blocks commit.
# Narrative QA P0 may optionally block when evidence confidence is high.
DEFAULT_COMMIT_POLICY = {
    "CANON_INTEGRITY": {"blocks_commit": True, "min_block_severity": "P0"},
    "NARRATIVE_QA": {"blocks_commit": True, "min_block_severity": "P0", "requires_high_confidence": True},
    "EDITORIAL_DIAGNOSIS": {"blocks_commit": False},
    "READER_RESPONSE": {"blocks_commit": False},
    "AUTHOR_DECISION": {"blocks_commit": False, "is_truth_source_for_preference": True},
}

LAYER_PURPOSE = {
    "CANON_INTEGRITY": "state, agency, knowledge, reality, durability and authorization safety",
    "NARRATIVE_QA": "high-confidence continuity and prose-contract bugs with evidence",
    "EDITORIAL_DIAGNOSIS": "structure, pacing, arcs, scene function and craft suggestions",
    "READER_RESPONSE": "blind reader or beta reactions; never objective truth",
    "AUTHOR_DECISION": "explicit author accept/reject/revise preference truth",
}


def _sev_rank(value: str) -> int:
    return {"OK": 0, "P2": 1, "P1": 2, "P0": 3}.get(str(value).upper(), 0)


def normalize_finding(finding: dict[str, Any], *, default_layer: str = "NARRATIVE_QA") -> dict[str, Any]:
    layer = str(finding.get("layer") or default_layer).upper()
    if layer not in LAYERS:
        layer = default_layer
    severity = str(finding.get("severity") or "P2").upper()
    if severity not in {"P0", "P1", "P2", "OK"}:
        severity = "P2"
    confidence = str(finding.get("confidence") or "medium").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    # blocks_commit:
    # - True/False = explicit finding-level override
    # - None = defer to host layer policy
    if "blocks_commit" in finding:
        blocks_commit = bool(finding.get("blocks_commit"))
    else:
        blocks_commit = None
    out = {
        "schema": "minis.authority-finding.v1",
        "layer": layer,
        "code": str(finding.get("code") or "UNCODED"),
        "severity": severity,
        "confidence": confidence,
        "claim": str(finding.get("claim") or finding.get("message") or ""),
        "evidence": finding.get("evidence") if isinstance(finding.get("evidence"), list) else (
            [finding["evidence"]] if finding.get("evidence") is not None else []
        ),
        "span": finding.get("span"),
        "minimal_fix": finding.get("minimal_fix") or finding.get("repair"),
        "blocks_commit": blocks_commit,
        "author_overridable": bool(finding.get("author_overridable", layer != "CANON_INTEGRITY" and severity != "P0")),
        "details": finding.get("details") if isinstance(finding.get("details"), dict) else {},
    }
    return out



def classify_findings(findings: list[dict[str, Any]] | None, *, default_layer: str = "NARRATIVE_QA") -> dict[str, list[dict[str, Any]]]:
    buckets = {layer: [] for layer in LAYERS}
    for raw in findings or []:
        item = normalize_finding(raw if isinstance(raw, dict) else {"claim": str(raw)}, default_layer=default_layer)
        buckets[item["layer"]].append(item)
    return buckets


def layer_status(findings: list[dict[str, Any]]) -> dict[str, Any]:
    if not findings:
        return {"status": "PASS", "severity": "OK", "finding_count": 0}
    worst = max(findings, key=lambda x: _sev_rank(x.get("severity", "P2")))
    severity = worst.get("severity", "P2")
    status = "FAIL" if severity == "P0" else "WARN"
    return {"status": status, "severity": severity, "finding_count": len(findings)}


def apply_commit_policy(layer_findings: dict[str, list[dict[str, Any]]], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or DEFAULT_COMMIT_POLICY
    blockers: list[dict[str, Any]] = []
    for layer, findings in layer_findings.items():
        rule = policy.get(layer) or {}
        if not rule.get("blocks_commit"):
            continue
        min_sev = str(rule.get("min_block_severity") or "P0").upper()
        need_high = bool(rule.get("requires_high_confidence"))
        for item in findings:
            if _sev_rank(item.get("severity", "P2")) < _sev_rank(min_sev):
                continue
            if need_high and str(item.get("confidence", "")).lower() != "high":
                continue
            # Explicit False opts out of blocking for non-canon layers.
            # None defers to this layer policy; True forces a block candidate.
            if item.get("blocks_commit") is False and layer != "CANON_INTEGRITY":
                continue
            blockers.append(item)
    return {
        "may_commit": not blockers,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "policy": policy,
    }


def build_authority_report(
    *,
    findings: list[dict[str, Any]] | None = None,
    source: str = "novel-judge",
    subject: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    layers = classify_findings(findings)
    layer_reports = {}
    for name in LAYERS:
        status = layer_status(layers[name])
        layer_reports[name] = {
            "schema": LAYER_SCHEMA,
            "layer": name,
            "purpose": LAYER_PURPOSE[name],
            "status": status["status"],
            "severity": status["severity"],
            "finding_count": status["finding_count"],
            "findings": layers[name],
        }
    commit = apply_commit_policy(layers, policy)
    report = {
        "schema": SCHEMA,
        "source": source,
        "subject": subject or {},
        "layers": layer_reports,
        "commit": commit,
        "summary": {
            "may_commit": commit["may_commit"],
            "layer_status": {name: layer_reports[name]["status"] for name in LAYERS},
            "total_findings": sum(len(v) for v in layers.values()),
        },
        "created_at": now_iso(),
    }
    if extras:
        report["extras"] = extras
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def merge_layer_reports(*reports: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    subjects = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        subjects.append(report.get("subject") or {})
        for layer in (report.get("layers") or {}).values():
            findings.extend(layer.get("findings") or [])
        for item in report.get("findings") or []:
            findings.append(item)
    subject = {}
    for part in subjects:
        subject.update(part)
    return build_authority_report(findings=findings, source="merged", subject=subject)
