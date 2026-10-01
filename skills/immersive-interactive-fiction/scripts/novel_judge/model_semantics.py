from __future__ import annotations

"""Task-specific semantic checks after JSON/schema validation.

These checks are intentionally conservative. Passing them grants only a
candidate-task capability, never canon or state authority.
"""

from typing import Any

from .repetition import detect_repetition


def validate_task_semantics(task: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    task_hash = str(result.get("task_hash", ""))
    if task == "npc_plan":
        if not str(result.get("actor_id", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_ACTOR"})
        if not str(result.get("goal", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_GOAL"})
        if not str(result.get("action_type", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_ACTION_TYPE"})
        if not isinstance(result.get("targets"), list) or not isinstance(result.get("reason_fact_ids"), list): errors.append({"code": "MODEL_RESULT_PLAN_LIST_TYPE"})
    elif task == "scene_manifest":
        if not str(result.get("scene_function", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_SCENE_FUNCTION"})
        if not str(result.get("focal_change", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_FOCAL_CHANGE"})
        if not isinstance(result.get("beats"), list) or not result.get("beats"): errors.append({"code": "MODEL_RESULT_EMPTY_BEATS"})
        if not str(result.get("handoff_owner", "")).strip(): errors.append({"code": "MODEL_RESULT_EMPTY_HANDOFF_OWNER"})
    elif task == "render":
        text = result.get("text")
        if not isinstance(text, str) or not text.strip(): errors.append({"code": "MODEL_RESULT_EMPTY_RENDER_TEXT"})
        else:
            lowered = text.lower()
            if (task_hash and task_hash.lower() in lowered) or "task_hash" in lowered: errors.append({"code": "MODEL_RESULT_TASK_HASH_LEAK_IN_PROSE"})
            safety_phrases = ("未起身", "未開門", "未害怕", "沒有起身", "沒有開門", "沒有說話", "不得替玩家", "唯一變化是")
            if any(x in text for x in safety_phrases): errors.append({"code": "MODEL_RESULT_NEGATIVE_SAFETY_NARRATION"})
            repetition = detect_repetition(text)
            for finding in repetition.get("findings", []):
                if finding.get("severity") == "P0": errors.append({"code": finding.get("code", "MODEL_RESULT_REPETITION") , "details": finding.get("evidence")})
        for field in ("claimed_facts", "action_manifest", "player_actions"):
            if not isinstance(result.get(field), list): errors.append({"code": "MODEL_RESULT_RENDER_LIST_TYPE", "field": field})
        if any(task_hash in str(x) or "task_hash" in str(x).lower() for x in result.get("action_manifest", []) if task_hash): errors.append({"code": "MODEL_RESULT_TASK_HASH_LEAK_IN_MANIFEST"})
    elif task == "repair":
        if not isinstance(result.get("text"), str) or not result.get("text", "").strip(): errors.append({"code": "MODEL_RESULT_EMPTY_REPAIR_TEXT"})
        if not isinstance(result.get("fixed_issue_ids"), list) or not result.get("fixed_issue_ids"): errors.append({"code": "MODEL_RESULT_EMPTY_FIXED_ISSUES"})
    elif task == "blind_read":
        if result.get("status") not in {"pass", "fail", "warn"}: errors.append({"code": "MODEL_RESULT_INVALID_REVIEW_STATUS"})
        if not isinstance(result.get("issues"), list): errors.append({"code": "MODEL_RESULT_REVIEW_ISSUES_TYPE"})
        if result.get("status") == "fail" and not result.get("issues"): errors.append({"code": "MODEL_RESULT_FAIL_WITHOUT_ISSUES"})
        if not isinstance(result.get("summary"), str) or not result.get("summary", "").strip(): errors.append({"code": "MODEL_RESULT_EMPTY_REVIEW_SUMMARY"})
    return errors
