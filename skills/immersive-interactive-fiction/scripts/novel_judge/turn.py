from __future__ import annotations

from typing import Any, Callable

from .capacity import capacity_budget, is_ai_autonomous_protagonist
from .canonical import deep_copy, sha256_json
from .context import build_context
from .engine import commit_turn
from .epistemic import visible_facts
from .micro import expand_macro_intent, is_macro_intent
from .model_tasks import compile_model_task
from .reality import build_reality_card
from .storylets import available_storylets


def run_turn(store: Any, intent: str | dict[str, Any], *, actor_id: str | None = None,
             renderer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
             generated_output: dict[str, Any] | None = None,
             expected_state_hash: str | None = None, source: str = "player_input",
             tick_seconds: int = 0) -> dict[str, Any]:
    """Run the deterministic turn boundary; renderer never receives hidden truth."""
    state = store.load_state()
    if state is None:
        raise ValueError("branch has no current state")
    actor = actor_id or (intent.get("actor_id") if isinstance(intent, dict) else "player")
    generating = renderer is not None or generated_output is not None
    packet = compile_model_task(
        state, task="render", actor_id=actor, store=store,
        persist_used_sources=generating,
    )
    context = packet.get("context") or build_context(state, audience="player" if actor == "player" else "npc", actor_id=actor)
    preview = {"state_hash": state.get("state_hash"), "actor_id": actor,
               "reality": build_reality_card(state, actor),
               "storylets": available_storylets(state, actor_id=actor),
               "visible_facts": visible_facts(state, audience="actor", actor_id=actor),
               "context": context,
               "generation_read_model": packet.get("generation_read_model"),
               "used_source_ids": packet.get("used_source_ids")}
    preview["context_hash"] = sha256_json(preview["context"])
    if renderer and generated_output is None:
        generated_output = renderer(deep_copy(preview))
    result = commit_turn(store, intent, actor_id=actor, generated_output=generated_output,
                         expected_state_hash=expected_state_hash, source=source)
    result["turn_pipeline"] = {"preflight_context": preview,
                                "status": result.get("status")}
    return result
