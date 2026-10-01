from __future__ import annotations

"""Machine scene review for author desks.

This is a prescan: Narrative QA + scene goals + editorial tickets.
It is not a beta reader, not a developmental editor, and not a literary score.
"""

from typing import Any

from .canonical import now_iso, sha256_json
from .editorial_diagnosis import diagnose_text
from .narrative_qa import inspect_prose
from .scene_goals import inspect_scene_goals

SCHEMA = "minis.scene-review.v1"


def review_scene_text(text: str, *, scene_id: str | None = None, source: str = "scene") -> dict[str, Any]:
    body = str(text or "")
    qa = inspect_prose(body)
    goals = inspect_scene_goals(body, scene_id=scene_id)
    editorial = diagnose_text(body, source=source, scene_id=scene_id)
    findings = list(qa.get("findings") or [])
    p0 = [f for f in findings if f.get("severity") == "P0" and str(f.get("confidence") or "").lower() == "high"]
    report = {
        "schema": SCHEMA,
        "scene_id": scene_id,
        "source": source,
        "chars": len(body),
        "narrative_qa": {
            "status": qa.get("status"),
            "finding_count": qa.get("finding_count"),
            "findings": findings,
            "may_commit": qa.get("may_commit"),
            "report_hash": qa.get("report_hash"),
        },
        "scene_goals": goals,
        "editorial": {
            "status": editorial.get("status"),
            "ticket_count": len(editorial.get("tickets") or []),
            "tickets": editorial.get("tickets") or [],
            "strengths": editorial.get("strengths") or [],
            "report_hash": editorial.get("report_hash"),
        },
        "blocking_p0_count": len(p0),
        "qa_would_block_later_commit": bool(p0) and qa.get("may_commit") is False,
        "claims": {
            "is_literary_score": False,
            "is_beta_reader": False,
            "is_developmental_edit": False,
            "is_author_decision": False,
            "machine_prescan_only": True,
            "does_not_replace_human_cold_read": True,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report
