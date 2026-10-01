import copy
import unittest

from narrative_judge import judge_action, replay, state_hash


def fixture():
    return {
        "schema_version": "novel-state.v1",
        "clock": {"tick": 0},
        "actors": {
            "player": {"kind": "player", "location": "room"},
            "fish": {"kind": "npc", "location": "room"},
        },
        "locations": {
            "room": {"connections": {"door": {"to": "hall", "open": False, "locked": True}}},
            "hall": {"connections": {"door": {"to": "room", "open": False, "locked": True}}},
        },
        "objects": {
            "bag": {"location": "room", "held_by": None, "portable": True},
            "wall": {"location": "room", "held_by": None, "portable": False},
        },
        "event_log": [],
    }


class NarrativeJudgeTests(unittest.TestCase):
    def test_locked_move_is_denied_without_mutation(self):
        state = fixture()
        result = judge_action(state, {"action_id": "a1", "actor_id": "player", "type": "move", "target": "hall", "source": "player_input"})
        self.assertEqual(result["verdict"], "deny")
        self.assertEqual(result["reason_code"], "LOCKED_CONNECTION")
        self.assertEqual(state["actors"]["player"]["location"], "room")

    def test_model_cannot_move_player(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "move", "target": "hall", "source": "model"})
        self.assertEqual(result["reason_code"], "PLAYER_AGENCY_PROTECTED")

    def test_take_updates_object_and_inventory(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "bag", "source": "player_input"})
        self.assertEqual(result["verdict"], "allow")
        self.assertEqual(result["state"]["objects"]["bag"]["held_by"], "player")

    def test_take_not_here_is_denied(self):
        state = fixture(); state["objects"]["bag"]["location"] = "hall"
        result = judge_action(state, {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "bag", "source": "player_input"})
        self.assertEqual(result["reason_code"], "OBJECT_NOT_HERE")

    def test_unknown_object_is_denied(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "nope", "source": "player_input"})
        self.assertEqual(result["reason_code"], "UNKNOWN_OBJECT")

    def test_explicit_player_commitment_allowed(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "commit", "text": "我自己決定離開", "source": "player_input"})
        self.assertEqual(result["reason_code"], "COMMITMENT_RECORDED")

    def test_model_cannot_create_player_commitment(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "commit", "text": "我答應", "source": "model"})
        self.assertEqual(result["reason_code"], "PLAYER_AGENCY_PROTECTED")

    def test_idempotency_blocks_second_application(self):
        first = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "bag", "source": "player_input"})
        second = judge_action(first["state"], {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "bag", "source": "player_input"})
        self.assertEqual(second["verdict"], "duplicate")
        self.assertEqual(len(second["state"]["event_log"]), 1)

    def test_replay_is_deterministic(self):
        state = fixture(); actions = [
            {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "bag", "source": "player_input"},
            {"action_id": "a2", "actor_id": "fish", "type": "wait", "seconds": 60, "source": "npc_tick"},
        ]
        events = []
        for action in actions:
            result = judge_action(state, action); self.assertEqual(result["verdict"], "allow")
            events += result["events"]; state = result["state"]
        rebuilt = replay(fixture(), events)
        self.assertEqual(state_hash(state), state_hash(rebuilt))

    def test_wait_advances_only_explicit_time(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "fish", "type": "wait", "seconds": 120, "source": "npc_tick"})
        self.assertEqual(result["state"]["clock"]["tick"], 120)

    def test_nonportable_object_is_denied(self):
        result = judge_action(fixture(), {"action_id": "a1", "actor_id": "player", "type": "take", "object_id": "wall", "source": "player_input"})
        self.assertEqual(result["reason_code"], "OBJECT_NOT_PORTABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
