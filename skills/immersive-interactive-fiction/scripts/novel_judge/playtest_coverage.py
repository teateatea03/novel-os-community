from __future__ import annotations

"""Interactive playtest coverage diagnostics.

Deterministic structural coverage over storylets/branches/events. Not a full
player study and not literary scoring.
"""

from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json
from .story_solver import solve_storylets
from .storylets import available_storylets

SCHEMA = "minis.playtest-coverage-report.v1"


def analyze_playtest_coverage(state: dict[str, Any], *, actor_id: str = "player",
                              played_storylet_ids: list[str] | None = None,
                              played_branch_ids: list[str] | None = None) -> dict[str, Any]:
    available = available_storylets(state, actor_id=actor_id) if "storylets" in state or True else []
    try:
        solver = solve_storylets(state, actor_id=actor_id)
    except Exception as exc:
        solver = {"status": "unavailable", "error": str(exc), "unreachable": [], "soft_locks": []}
    avail_ids = [str(s.get("id")) for s in available if isinstance(s, dict) and s.get("id")]
    played = set(str(x) for x in (played_storylet_ids or []))
    unplayed = [x for x in avail_ids if x not in played]
    findings = []
    if avail_ids and not played:
        findings.append(normalize_finding({
            "layer": "NARRATIVE_QA",
            "code": "PLAYTEST_NO_COVERAGE",
            "severity": "P2",
            "confidence": "high",
            "claim": "有可用 storylet 但尚未記錄任何 playtest 覆蓋",
            "blocks_commit": False,
        }))
    if unplayed and played:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "PLAYTEST_PARTIAL_COVERAGE",
            "severity": "P2",
            "confidence": "medium",
            "claim": f"{len(unplayed)}/{len(avail_ids)} 可用 storylet 尚未被 playtest 觸及",
            "blocks_commit": False,
            "details": {"unplayed": unplayed[:50]},
        }))
    unreachable = list(solver.get("unreachable") or solver.get("unreachable_storylets") or [])
    soft = list(solver.get("soft_locks") or solver.get("soft_lock") or [])
    if unreachable:
        findings.append(normalize_finding({
            "layer": "NARRATIVE_QA",
            "code": "STORYLET_UNREACHABLE",
            "severity": "P1",
            "confidence": "high",
            "claim": "solver 回報不可達 storylet",
            "blocks_commit": False,
            "details": {"unreachable": unreachable[:50]},
        }))
    if soft:
        findings.append(normalize_finding({
            "layer": "NARRATIVE_QA",
            "code": "STORYLET_SOFT_LOCK",
            "severity": "P1",
            "confidence": "high",
            "claim": "solver 回報 soft-lock 風險",
            "blocks_commit": False,
            "details": {"soft_locks": soft[:50]},
        }))
    branches = list(played_branch_ids or [])
    if len(branches) <= 1 and avail_ids:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "PLAYTEST_SINGLE_PATH",
            "severity": "P2",
            "confidence": "medium",
            "claim": "目前只看到單一路徑／分支 playtest 證據",
            "blocks_commit": False,
        }))
    authority = build_authority_report(findings=findings, source="playtest_coverage", subject={"actor_id": actor_id})
    status = "FAIL" if any(f.get("severity") == "P0" for f in findings) else ("WARN" if findings else "PASS")
    report = {
        "schema": SCHEMA,
        "status": status,
        "available_storylet_ids": avail_ids,
        "played_storylet_ids": sorted(played),
        "unplayed_storylet_ids": unplayed,
        "played_branch_ids": branches,
        "solver": {
            "status": solver.get("status"),
            "unreachable": unreachable,
            "soft_locks": soft,
        },
        "coverage_rate": round(len(played & set(avail_ids)) / len(avail_ids), 6) if avail_ids else None,
        "findings": findings,
        "authority": authority,
        "claims": {
            "is_human_playtest": False,
            "is_literary_quality": False,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report
