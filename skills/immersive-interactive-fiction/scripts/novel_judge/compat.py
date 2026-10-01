"""Explicit compatibility names for early Novel OS hosts."""
from .engine import commit_turn, replay_events
from .intent import make_intent

def judge_action(state, action):
    """Compatibility adapter; new hosts should use FileStore + commit_turn."""
    from .state import normalize_state
    from .store import FileStore
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        s = FileStore(root, state.get("project_id", "legacy"), state.get("session_id", "legacy"), state.get("branch_id", "main"))
        s.save_state(normalize_state(state, verify_hash=False))
        intent = make_intent(action["actor_id"], action["type"], turn_id=action.get("action_id"),
                             targets=[action.get("target")] if action.get("target") else [],
                             parameters={k:v for k,v in action.items() if k not in {"actor_id", "type", "action_id", "target"}},
                             source=action.get("source", "player_input"), raw_input=action.get("text"))
        turn = commit_turn(s, intent)
        return {"verdict": "allow" if turn.get("verdict") == "allow" else "deny", "state": s.load_state(),
                "turn": turn, "events": [turn.get("event")] if turn.get("event") else []}
