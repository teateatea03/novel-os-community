from __future__ import annotations

import re
from typing import Any

from .capacity import action_zone, capacity_budget, action_is_major, is_ai_autonomous_protagonist
from .canonical import sha256_json
from .errors import GATE_FAILED, KNOWLEDGE_BOUNDARY, PLAYER_SOVEREIGNTY, NARRATIVE_CAPACITY_VIOLATION
from .epistemic import visible_fact_ids


def _list_claims(output: dict[str, Any], key: str) -> list[Any]:
    value = output.get(key, []) or []
    return list(value) if isinstance(value, list) else []


def _action_claims(output: dict[str, Any]) -> list[dict[str, Any]]:
    result=[]
    for key in ("action_manifest", "action_claims", "observed_effects"):
        for item in _list_claims(output, key):
            if isinstance(item, str): result.append({"type": item})
            elif isinstance(item, dict): result.append(item)
    # player_actions remain an agency claim, but are also capacity claims.
    for item in _list_claims(output, "player_actions"):
        if isinstance(item, str): result.append({"type": item})
        elif isinstance(item, dict): result.append(item)
    return result


def _accepted_types(intent: dict[str, Any], accepted_delta: dict[str, Any] | None) -> list[str]:
    types=[intent.get("type", "observe")]
    if isinstance(accepted_delta, dict):
        for item in accepted_delta.get("action_manifest", []) or []:
            if isinstance(item, dict) and item.get("type"): types.append(str(item["type"]))
    return types


def validate_capacity_claims(output: dict[str, Any], before: dict[str, Any], intent: dict[str, Any], accepted_delta: dict[str, Any] | None) -> dict[str, Any]:
    actor_id=intent.get("actor_id")
    budget=capacity_budget(before, actor_id)
    claims=_action_claims(output)
    accepted=_accepted_types(intent, accepted_delta)
    errors=[]; warnings=[]
    # Renderers may describe the accepted action itself. Any extra concrete
    # action must be explicitly listed in the accepted micro action manifest.
    committed=sum(1 for c in claims if c.get("type") not in accepted)
    # A renderer must not hide substantive action in prose by omitting the
    # manifest. For constrained actors, action claims are required whenever
    # the output describes an autonomous protagonist response.
    if budget.get("requires_action_manifest") and not output.get("action_manifest") and claims:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"constrained output requires an explicit action_manifest"})
    major=sum(1 for c in claims if action_is_major(str(c.get("type", ""))))
    zones={str(c.get("zone") or c.get("location")) for c in claims if c.get("zone") or c.get("location")}
    plan_steps=output.get("plan_steps", []) or output.get("explicit_plan", []) or []
    entities=output.get("attended_entities", []) or output.get("new_entities", []) or []
    max_major=int(budget.get("max_major_actions_per_turn", 999))
    max_zones=int(budget.get("max_zones", 999))
    max_plans=int(budget.get("max_explicit_plan_steps", 999))
    max_entities=int(budget.get("max_new_entities_attended", 999))
    if committed:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose claims actions not present in accepted micro-action delta","details":{"uncommitted_action_count":committed,"accepted_types":accepted}})
    if major > max_major:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose exceeds major-action budget","details":{"major_action_count":major,"max_major_actions_per_turn":max_major}})
    if len(zones)>max_zones:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose spans too many zones","details":{"zones":sorted(zones),"max_zones":max_zones}})
    if len(plan_steps)>max_plans:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose exceeds explicit planning budget","details":{"plan_steps":len(plan_steps),"max_explicit_plan_steps":max_plans}})
    if len(entities)>max_entities:
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose attends to too many new entities","details":{"entities":len(entities),"max_new_entities_attended":max_entities}})
    if output.get("full_inventory_claim") or output.get("complete_exploration"):
        errors.append({"code":NARRATIVE_CAPACITY_VIOLATION,"message":"prose claims full inventory/exploration under bounded capacity"})
    return {"status":"fail" if errors else "pass","errors":errors,"warnings":warnings,"budget":budget,"accepted_action_types":accepted,"observed_action_count":len(claims),"uncommitted_action_count":committed,"major_action_count":major,"zone_count":len(zones),"plan_step_count":len(plan_steps),"entity_count":len(entities)}


def validate_prose(output: dict[str, Any] | None, before: dict[str, Any], after: dict[str, Any], intent: dict[str, Any], *, audience: str = "reader", actor_id: str | None = None, accepted_delta: dict[str, Any] | None = None) -> dict[str, Any]:
    if output is None:
        return {"status": "not_run", "errors": [], "warnings": [], "audience": audience}
    errors=[]; warnings=[]
    if not isinstance(output, dict) or not isinstance(output.get("text", ""), str):
        return {"status":"fail","errors":[{"code":GATE_FAILED,"message":"render output must contain string text"}],"warnings":[],"audience":audience}
    visible=visible_fact_ids(after,audience=audience,actor_id=actor_id)
    for fact in _list_claims(output,"claimed_facts"):
        if fact not in visible: errors.append({"code":KNOWLEDGE_BOUNDARY,"message":"prose claims fact outside audience scope","details":{"fact":fact}})
    player_actor=intent.get("actor_id") in {"player","user"}
    autonomous = is_ai_autonomous_protagonist(before.get("actors", {}).get(intent.get("actor_id"), {}))
    for item in _list_claims(output,"player_actions"):
        typ=item.get("type") if isinstance(item,dict) else item
        if not player_actor and intent.get("actor_id") not in {"world"}:
            errors.append({"code":PLAYER_SOVEREIGNTY,"message":"prose claims player action for non-player actor","details":{"claim":item}})
        elif player_actor and typ != intent.get("type"):
            errors.append({"code":PLAYER_SOVEREIGNTY,"message":"prose claims an unaccepted player action","details":{"claim":item,"accepted":intent.get("type")}})
    if _list_claims(output,"player_commitments") and (intent.get("type") != "promise" or not intent.get("player_authored")):
        errors.append({"code":PLAYER_SOVEREIGNTY,"message":"prose creates an unaccepted player commitment"})
    if output.get("state_delta") and accepted_delta is not None:
        proposed=output["state_delta"].get("operations",[]) if isinstance(output["state_delta"],dict) else []
        accepted=accepted_delta.get("operations",[])
        if proposed != accepted: errors.append({"code":GATE_FAILED,"message":"rendered state delta differs from judge-accepted delta"})
    cap=validate_capacity_claims(output,before,intent,accepted_delta)
    if autonomous and output.get("player_actions"):
        # Autonomous protagonist may propose its own action, but it is still
        # subject to accepted micro delta and capacity budget.
        warnings.append({"code":"AUTONOMOUS_PROTAGONIST_PROPOSAL","message":"protagonist action is a proposal; judge commit remains authoritative"})
    errors.extend(cap["errors"]); warnings.extend(cap["warnings"])
    if output.get("unstructured_state_claims"): warnings.append({"code":"UNVERIFIED_STATE_CLAIM","message":"unstructured claims are not authoritative"})
    return {"status":"fail" if errors else "pass","errors":errors,"warnings":warnings,"audience":audience,"context_fingerprint":sha256_json(sorted(visible)),"accepted_delta_hash":sha256_json(accepted_delta or {"operations":[]}),"capacity":cap}
