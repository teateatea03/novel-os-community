from __future__ import annotations

"""Scene goal / opposition / value-shift diagnostics.

Advisory by default. High-confidence missing-goal on long scenes becomes
editorial/narrative warnings, not automatic canon blockers.
"""

import re
from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json

SCHEMA = "minis.scene-goal-report.v1"

# Avoid bare particles that appear in weather/time filler (e.g. 過去).
_GOAL = re.compile(
    r"(想要|必須|得先|打算|準備|決定|別再|不要|快點|離開這裡|留下來|證明|找到|說清楚|開門|關門|逃走|抓住|保護|阻止)"
)
_OPPOSITION = re.compile(r"(可是|但是|然而|卻|不行|拒絕|來不及|門被|被打斷|危險|反對|卡住|失敗)")
_TURN = re.compile(r"(於是|最後|只好|結果|忽然|突然|直到|這才|反而|終究)")
_VALUE = re.compile(r"(信任|懷疑|害怕|鬆了口氣|更近|更遠|生氣|原諒|答應|拒絕|放棄|決定)")
_DIALOGUE = re.compile(r"[「\"“][^」\"”]{2,}[」\"”]")
_ACTION = re.compile(r"(走|跑|推|拉|握|打開|關上|坐下|站起|看向|聽見|沉默)")


def inspect_scene_goals(text: str, *, scene_id: str | None = None) -> dict[str, Any]:
    body = str(text or "").strip()
    findings = []
    signals = {
        "goal": bool(_GOAL.search(body)),
        "opposition": bool(_OPPOSITION.search(body)),
        "turn": bool(_TURN.search(body)),
        "value_shift_language": bool(_VALUE.search(body)),
        "dialogue": bool(_DIALOGUE.search(body)),
        "action": bool(_ACTION.search(body)),
        "chars": len(body),
    }

    if len(body) >= 160 and not signals["goal"]:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "SCENE_GOAL_WEAK",
            "severity": "P2",
            "confidence": "medium",
            "claim": "較長場景缺少可辨目標／意圖語言",
            "blocks_commit": False,
            "minimal_fix": "讓視角人物想完成一件具體事情，並讓阻力可見",
        }))

    if len(body) >= 160 and not signals["dialogue"] and not signals["opposition"] and not signals["turn"] and not signals["value_shift_language"]:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "SCENE_STATIC_ATMOSPHERE",
            "severity": "P2",
            "confidence": "medium",
            "claim": "較長段落多為靜態氣氛／時間流逝，缺少對白、阻力或轉折",
            "blocks_commit": False,
            "minimal_repair": "加入角色意圖、阻力或狀態變化，避免純氣氛填充",
        }))

    if len(body) >= 220 and signals["goal"] and not signals["opposition"]:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "SCENE_OPPOSITION_WEAK",
            "severity": "P2",
            "confidence": "medium",
            "claim": "有目標跡象但缺少阻力／反對／代價",
            "blocks_commit": False,
            "minimal_repair": "加入另一力量的可行反制、時間壓力或關係代價",
        }))

    if len(body) >= 260 and not signals["turn"] and not signals["value_shift_language"]:
        findings.append(normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": "SCENE_VALUE_SHIFT_UNCLEAR",
            "severity": "P2",
            "confidence": "low",
            "claim": "場景結束時難辨價值變化或轉折",
            "blocks_commit": False,
            "minimal_repair": "讓離場狀態在關係、資訊、風險或目標上與進場不同",
        }))

    if len(body) >= 300 and not signals["dialogue"] and not signals["goal"] and not signals["action"]:
        findings.append(normalize_finding({
            "layer": "NARRATIVE_QA",
            "code": "SCENE_FUNCTION_OPAQUE",
            "severity": "P1",
            "confidence": "medium",
            "claim": "長場景既無對白也無清楚目標／動作，功能可能不透明",
            "blocks_commit": False,
            "minimal_repair": "明確場景功能：追問、交易、對峙、逃避或揭露",
        }))

    # de-dupe by code
    uniq = {}
    for f in findings:
        uniq[f["code"]] = f
    findings = list(uniq.values())

    authority = build_authority_report(findings=findings, source="scene_goals", subject={"scene_id": scene_id})
    status = "FAIL" if any(f.get("severity") == "P0" for f in findings) else ("WARN" if findings else "PASS")
    report = {
        "schema": SCHEMA,
        "scene_id": scene_id,
        "status": status,
        "signals": signals,
        "findings": findings,
        "authority": authority,
        "claims": {"is_complete_story_grid": False, "blocks_commit": False},
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report
