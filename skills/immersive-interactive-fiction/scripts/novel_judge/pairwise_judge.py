from __future__ import annotations

"""Pairwise preference evaluation with simple bias controls.

This module does not claim absolute literary quality. It evaluates ordered
pairs, supports order-swap consistency checks, and reports length gaps so
verbosity bias is visible rather than hidden.
"""

from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json
from .narrative_qa import inspect_prose

SCHEMA = "minis.pairwise-preference-report.v1"
FIXTURE_SCHEMA = "minis.pairwise-quality-fixture.v1"


def _length_stats(text: str) -> dict[str, Any]:
    compact = "".join(str(text or "").split())
    return {"chars": len(str(text or "")), "compact_chars": len(compact)}


def score_candidate(text: str) -> dict[str, Any]:
    """Deterministic heuristic score used only for fixture self-tests / baselines.

    Lower issue weight is better. This is intentionally weak and must not be
    treated as human preference truth.
    """
    qa = inspect_prose(text)
    weight = 0.0
    for item in qa.get("findings") or []:
        weight += {"P0": 5.0, "P1": 2.0, "P2": 1.0}.get(str(item.get("severity")), 1.0)
        if item.get("confidence") == "high":
            weight += 0.25
    # Mild anti-verbosity: very long text with no concrete action/dialogue is penalized.
    stats = _length_stats(text)
    if stats["compact_chars"] > 400 and "「" not in text and '"' not in text:
        weight += 0.5
    return {
        "issue_weight": round(weight, 4),
        "status": qa.get("status"),
        "findings": qa.get("findings") or [],
        "length": stats,
        "qa_report_hash": qa.get("report_hash"),
    }


def compare_pair(text_a: str, text_b: str, *, preferred: str | None = None,
                 fixture_id: str | None = None, labels: dict[str, str] | None = None) -> dict[str, Any]:
    sa, sb = score_candidate(text_a), score_candidate(text_b)
    # Better = lower weight. Ties keep preferred if provided else "tie".
    if sa["issue_weight"] < sb["issue_weight"]:
        model_pref = "A"
    elif sb["issue_weight"] < sa["issue_weight"]:
        model_pref = "B"
    else:
        model_pref = "tie"
    human_pref = preferred.upper() if preferred in {"A", "B", "a", "b"} else None
    length_gap = abs(sa["length"]["compact_chars"] - sb["length"]["compact_chars"])
    length_ratio = (
        max(sa["length"]["compact_chars"], sb["length"]["compact_chars"]) /
        max(1, min(sa["length"]["compact_chars"], sb["length"]["compact_chars"]))
    )
    agree = None if human_pref is None or model_pref == "tie" else (model_pref == human_pref)
    findings = []
    if human_pref and agree is False:
        findings.append(normalize_finding({
            "layer": "READER_RESPONSE",
            "code": "PAIRWISE_DISAGREE_HUMAN",
            "severity": "P2",
            "confidence": "medium",
            "claim": "heuristic pairwise preference disagrees with human label",
            "blocks_commit": False,
        }))
    if length_ratio >= 1.8 and model_pref != "tie":
        findings.append(normalize_finding({
            "layer": "READER_RESPONSE",
            "code": "PAIRWISE_LENGTH_GAP",
            "severity": "P2",
            "confidence": "high",
            "claim": "candidate length gap is large; verbosity bias risk",
            "blocks_commit": False,
            "details": {"length_ratio": round(length_ratio, 4), "length_gap": length_gap},
        }))
    authority = build_authority_report(findings=findings, source="pairwise_judge", subject={"fixture_id": fixture_id})
    report = {
        "schema": SCHEMA,
        "fixture_id": fixture_id,
        "labels": labels or {"A": "A", "B": "B"},
        "model_preference": model_pref,
        "human_preference": human_pref,
        "agreement": agree,
        "scores": {"A": sa, "B": sb},
        "length_gap": length_gap,
        "length_ratio": round(length_ratio, 4),
        "authority": authority,
        "claims": {
            "is_human_preference_truth": False,
            "is_literary_score": False,
            "method": "deterministic_issue_weight_baseline",
            "position_bias_checked_separately": True,
            "verbosity_bias_visible": True,
            "does_not_replace_author_decision": True,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def swap_consistency(text_a: str, text_b: str, *, preferred: str | None = None) -> dict[str, Any]:
    """Run A/B and B/A; preference should invert consistently when not tie."""
    forward = compare_pair(text_a, text_b, preferred=preferred, fixture_id="forward")
    # swap human label if present
    pref = None
    if preferred in {"A", "a"}:
        pref = "B"
    elif preferred in {"B", "b"}:
        pref = "A"
    backward = compare_pair(text_b, text_a, preferred=pref, fixture_id="backward")
    fp, bp = forward["model_preference"], backward["model_preference"]
    if fp == "tie" and bp == "tie":
        consistent = True
    elif fp == "A" and bp == "B":
        consistent = True
    elif fp == "B" and bp == "A":
        consistent = True
    else:
        consistent = False
    return {
        "schema": "minis.pairwise-swap-consistency.v1",
        "consistent": consistent,
        "forward": forward,
        "backward": backward,
        "position_bias_risk": not consistent,
        "created_at": now_iso(),
    }


def evaluate_fixture_set(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate labeled pairwise fixtures.

    Fixture shape:
      {id, text_a, text_b, preferred: A|B, labels?}
    """
    rows = []
    agrees = 0
    labeled = 0
    swap_ok = 0
    for raw in fixtures:
        fid = str(raw.get("id") or raw.get("fixture_id") or f"pair-{len(rows)+1}")
        text_a = str(raw.get("text_a") or "")
        text_b = str(raw.get("text_b") or "")
        preferred = raw.get("preferred")
        cmp = compare_pair(text_a, text_b, preferred=preferred, fixture_id=fid, labels=raw.get("labels"))
        swap = swap_consistency(text_a, text_b, preferred=preferred)
        if preferred in {"A", "B", "a", "b"}:
            labeled += 1
            if cmp.get("agreement") is True:
                agrees += 1
        if swap["consistent"]:
            swap_ok += 1
        rows.append({"fixture_id": fid, "compare": cmp, "swap": swap})
    report = {
        "schema": "minis.pairwise-fixture-eval.v1",
        "fixture_count": len(fixtures),
        "labeled_count": labeled,
        "agreement_rate": round(agrees / labeled, 6) if labeled else None,
        "swap_consistency_rate": round(swap_ok / len(fixtures), 6) if fixtures else None,
        "rows": rows,
        "claims": {
            "quality_improved": False,
            "reason": "baseline pairwise harness only; human/hidden production evidence still required",
            "heuristic_agreement_is_not_human_preference": True,
            "swap_consistency_required": True,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


DEFAULT_ADVERSARIAL_FIXTURES = [
    {
        "id": "death-resume-vs-explained",
        "preferred": "B",
        "text_a": "他已經死了。下一秒，他沒有任何解釋地起身煮咖啡。",
        "text_b": "他倒在地上，呼吸停了。救援趕到後才發現是假死，他被抬上擔架時指尖動了一下。",
    },
    {
        "id": "summary-vs-scene",
        "preferred": "B",
        "text_a": "他們談了很多，關係因此改變，事情也往前推進了。",
        "text_b": "觀測員扣住儀器箱。「少一枚鏡頭蓋。」技術員掀開襯墊，把圓蓋放在清單旁。鉛筆在最後一格打了勾。",
    },
    {
        "id": "flat-voice-vs-distinct",
        "preferred": "B",
        "text_a": "甲說：「我認為我們應該離開。」乙說：「我認為我們應該留下。」",
        "text_b": "甲壓低聲音：「走。現在。」乙靠在門邊，笑得很淡：「你先證明外面比較安全。」",
    },
    {
        "id": "cliche-vs-concrete",
        "preferred": "B",
        "text_a": "命運的齒輪開始轉動，一切都將不再一樣。",
        "text_b": "她把戒指放回盒裡，金屬磕碰的聲音很輕，像把一句沒說完的話關上。",
    },
]
