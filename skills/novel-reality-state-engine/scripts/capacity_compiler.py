from __future__ import annotations

HIGH_LOAD = {'high', 'critical', 'severe'}
CONSTRAINED = {'fragmented_clear', 'confused', 'impaired'}

def capacity_budget(state: dict, actor_id: str) -> dict:
    rec = state.get('reality', {}).get('actors', {}).get(actor_id, {})
    physical = rec.get('physical', {})
    cognition = rec.get('cognition', {})
    constrained = cognition.get('clarity') in CONSTRAINED or cognition.get('working_memory') in {'reduced','poor'} or cognition.get('planning_horizon') in {'immediate','minutes'} or any(physical.get(k) in HIGH_LOAD for k in ('hunger','fatigue','cold','thermal_load'))
    base = {}
    if constrained:
        base = {'max_major_actions_per_turn': 1, 'max_minor_actions_per_turn': 2, 'max_new_entities_attended': 2, 'max_explicit_plan_steps': 1, 'max_zones': 1, 'must_reanchor_after_actions': 1, 'requires_action_manifest': True, 'action_granularity': 'micro'}
    explicit = rec.get('capacity', {}).get('cognitive_budget', {})
    if isinstance(explicit, dict): base.update(explicit)
    return base

def compile_reality_capacity(state: dict, actor_id: str) -> dict:
    """Return executable action budget from canonical physical/cognitive state."""
    rec = state.get('reality', {}).get('actors', {}).get(actor_id, {})
    return {'actor_id': actor_id, 'budget': capacity_budget(state, actor_id), 'physical': rec.get('physical', {}), 'cognition': rec.get('cognition', {}), 'affordances': rec.get('available_actions', []), 'blocked': rec.get('blocked_actions', []), 'source': rec.get('source', 'state')}
