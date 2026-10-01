from __future__ import annotations

from typing import Any

from .canonical import deep_copy
from .errors import JudgeError
from .micro import expand_macro_intent, is_macro_intent
from .engine import commit_turn
from .model_tasks import compile_model_task


def run_agent_turn(store: Any, intent: str | dict[str, Any], *, actor_id: str | None = None,
                   renderer: Any = None, generated_output: dict[str, Any] | None = None,
                   expected_state_hash: str | None = None, source: str = "model") -> dict[str, Any]:
    """Run an AI-autonomous protagonist turn with macro→micro compilation.

    The renderer is called once per micro child with fresh state. A macro
    request never receives permission to narrate all children in one response.
    If a child fails, prior committed children remain auditable and the parent
    report marks the boundary rather than silently continuing.
    """
    raw = intent
    if isinstance(raw, str):
        raise JudgeError("SCHEMA_ERROR", "agent turn requires structured intent")
    state = store.load_state()
    if state is None: raise ValueError("branch has no current state")
    actor = actor_id or raw.get("actor_id")
    macro = is_macro_intent(raw)
    children = expand_macro_intent(state, raw) if macro else [raw]
    results=[]
    for index, child in enumerate(children):
        current=store.load_state()
        packet=compile_model_task(current, task="render", actor_id=actor, store=store, persist_used_sources=bool(renderer))
        preview={"state_hash":current.get("state_hash"),"micro_index":index,"micro_count":len(children),
                 "context":packet.get("context"),"generation_read_model":packet.get("generation_read_model"),
                 "used_source_ids":packet.get("used_source_ids")}
        if renderer and generated_output is None:
            output=renderer(deep_copy(preview))
        else:
            output=generated_output if len(children)==1 else {"text":"","action_claims":[]}
        result=commit_turn(store, child, actor_id=actor, generated_output=output,
                           expected_state_hash=current.get("state_hash"), source=source)
        results.append(result)
        if result.get("status") in {"rejected","deferred"} or result.get("verdict") in {"rejected","defer"}:
            break
        generated_output=None
    final=store.load_state()
    return {"status":"committed" if all(r.get("status") not in {"rejected","deferred"} for r in results) else "partial",
            "macro":macro,"micro_count":len(results),"requested_micro_count":len(children),
            "results":results,"state_hash":final.get("state_hash") if final else None}
