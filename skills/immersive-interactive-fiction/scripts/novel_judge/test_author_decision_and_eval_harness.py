from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from .author_decision import normalize_author_decision_payload, require_scene_author_decision
from .author_feedback import feedback_status
from .canonical import refresh_state_hash
from .cold_read import cold_read_text, open_beta_session, record_reader_reaction, summarize_reader_consensus
from .gate_authority import make_gate_envelope
from .longform import commit_scene_event, initialize_longform_production
from .pairwise_judge import DEFAULT_ADVERSARIAL_FIXTURES, evaluate_fixture_set, swap_consistency
from .playtest_coverage import analyze_playtest_coverage
from .production import ProjectRuntimeAdapter, make_candidate_binding
from .scene_goals import inspect_scene_goals
from .semantic_events import compile_semantic_delta
from .state import empty_state


def _shadow(root):
    s = empty_state("p", "s")
    s["canon_scope"] = "experiment"
    s["actors"] = {"world": {"kind": "world", "location": "room", "status": {}, "commitments": []}}
    s["world_truth"]["locations"] = {"room": {"connections": {}}}
    s = refresh_state_hash(s)
    a = ProjectRuntimeAdapter(root, "p", "s")
    a.initialize(s, baseline_id="b", provenance={"shadow": True}, migration_authorized=True)
    return a, s


class AuthorDecisionAndHarnessTests(unittest.TestCase):
    def test_scene_commit_requires_explicit_author_decision_payload(self):
        with self.assertRaises(ValueError):
            require_scene_author_decision(
                scene_id="S1",
                author_decision=None,
                authority_record={"require_author_decision_on_scene_commit": True},
            )
        payload = require_scene_author_decision(
            scene_id="S1",
            author_decision={"decision": "accept", "reason_codes": ["continuity"], "reason": "ok"},
            authority_record={"require_author_decision_on_scene_commit": True},
        )
        self.assertEqual(payload["decision"], "accept")
        with self.assertRaises(ValueError):
            normalize_author_decision_payload({"decision": "reject"})

    def test_longform_scene_commit_records_author_decision(self):
        with tempfile.TemporaryDirectory() as td:
            a = initialize_longform_production(td, "novel")
            root = Path(td)
            scene_path = root / "chapters/chapter-001.md"
            scene_path.parent.mkdir()
            scene_path.write_text("scene body", encoding="utf-8")
            scene_hash = hashlib.sha256(scene_path.read_bytes()).hexdigest()
            state = a.store.load_state()
            turn = "scene-001"
            envs = [
                make_gate_envelope(gate_type=g, turn_id=turn, scene_sha256=scene_hash, source_state_hash=state["state_hash"])
                for g in a.gate_policy()["required_gate_types"]
            ]
            ops = [{"op": "add", "path": "/world_truth/events/scene-001", "value": {"summary": "door opens"}}]
            sem = compile_semantic_delta(
                turn_id=turn, actor_id="world", action_type="scene_commit", operations=ops,
                summary="Door opens", scene_id=turn,
            )
            binding = make_candidate_binding(
                turn_id=turn, operations=ops, actor_id="world", action_type="scene_commit",
                summary="Door opens", scene_id=turn, chapter_id="chapter-001",
                scene_sha256=scene_hash, semantic_hash=sem["semantic_hash"],
            )
            a.approve_gate_bundle(
                turn_id=turn, scene_sha256=scene_hash, source_state_hash=state["state_hash"],
                envelopes=envs, candidate_binding=binding,
            )
            r = commit_scene_event(
                a, scene_id=turn, chapter_id="chapter-001", operations=ops, summary="Door opens",
                author_approved=True, expected_state_hash=state["state_hash"],
                source_artifact_hash=scene_hash, source_artifact_path="chapters/chapter-001.md",
                scene_sha256=scene_hash,
                author_decision={"decision": "accept", "reason_codes": ["continuity"], "reason": "scene ok"},
            )
            self.assertEqual(r["status"], "committed")
            self.assertIn("author_decision", r)
            self.assertEqual(r["author_decision"]["event"]["decision"], "accept")
            self.assertEqual(feedback_status(a.store)["explicit_count"], 1)

    def test_non_scene_commit_still_works_without_author_decision(self):
        with tempfile.TemporaryDirectory() as td:
            a, s = _shadow(td)
            turn = "Tsys"
            scene = hashlib.sha256(b"sys").hexdigest()
            ops = [{"op": "replace", "path": "/clock/tick", "value": 1}]
            envs = [make_gate_envelope(gate_type=g, turn_id=turn, scene_sha256=scene, source_state_hash=s["state_hash"]) for g in a.gate_policy()["required_gate_types"]]
            # shadow authority may not require candidate binding; omit it to avoid drift.
            a.approve_gate_bundle(turn_id=turn, scene_sha256=scene, source_state_hash=s["state_hash"], envelopes=envs)
            r = a.commit(turn_id=turn, operations=ops, expected_state_hash=s["state_hash"], scene_sha256=scene, summary="t")
            self.assertEqual(r["status"], "committed")
            self.assertNotIn("author_decision", r)
            # no scene_id => AUTHOR_DECISION ledger may remain empty
            self.assertEqual(feedback_status(a.store)["explicit_count"], 0)

    def test_pairwise_adversarial_fixtures_agree_and_swap_stable(self):
        report = evaluate_fixture_set(DEFAULT_ADVERSARIAL_FIXTURES)
        self.assertGreaterEqual(report["fixture_count"], 4)
        self.assertEqual(report["agreement_rate"], 1.0)
        self.assertEqual(report["swap_consistency_rate"], 1.0)
        one = swap_consistency(DEFAULT_ADVERSARIAL_FIXTURES[0]["text_a"], DEFAULT_ADVERSARIAL_FIXTURES[0]["text_b"], preferred="B")
        self.assertTrue(one["consistent"])

    def test_cold_read_and_beta_session(self):
        report = cold_read_text("他們談了很多，關係因此改變，事情也往前推進了。", source="demo")
        self.assertEqual(report["role"], "cold_read_prescan")
        self.assertFalse(report["claims"]["is_beta_reader"])
        self.assertFalse(report["claims"]["is_human_reader"])
        self.assertTrue(report["claims"]["machine_prescan_only"])
        self.assertEqual(report["authority"]["layers"]["READER_RESPONSE"]["status"], "PASS")
        self.assertEqual(report["reactions"], [])
        codes = {x["code"] for x in (report["prescan"]["narrative_qa"]["findings"] or [])}
        self.assertIn("SUMMARY_ONLY_SCENE", codes)
        self.assertEqual(report["human_slots"]["status"], "pending")
        with tempfile.TemporaryDirectory() as td:
            session = open_beta_session(td, session_id="beta1", readers=["r1"])
            self.assertTrue(Path(session["path"], "session.json").is_file())
            q = (Path(session["path"]) / "questionnaire.md").read_text(encoding="utf-8")
            self.assertIn("核心題", q)
            self.assertIn("不必當編輯", q)

    def test_human_reader_consensus_is_not_author_decision(self):
        a = record_reader_reaction(
            reader_id="r1", source="ch1", role="beta_reader",
            reactions=[{"code": "LOST_INTEREST", "claim": "第三章開始略讀", "locus": {"chapter": "ch3"}}],
        )
        b = record_reader_reaction(
            reader_id="r2", source="ch1", role="beta_reader",
            reactions=[{"code": "LOST_INTEREST", "claim": "第三章失趣", "locus": {"chapter": "ch3"}}],
        )
        lone = record_reader_reaction(
            reader_id="r3", source="ch1", role="beta_reader",
            reactions=[{"code": "DISLIKE_VOICE", "claim": "不喜歡敘事者", "locus": {"chapter": "ch1"}}],
        )
        consensus = summarize_reader_consensus([a, b, lone])
        self.assertEqual(consensus["human_report_count"], 3)
        self.assertGreaterEqual(consensus["consensus_candidate_count"], 1)
        self.assertFalse(consensus["claims"]["is_author_decision"])
        self.assertFalse(consensus["claims"]["author_must_accept_all"])
        lost = next(x for x in consensus["rows"] if x["code"] == "LOST_INTEREST")
        self.assertEqual(lost["status"], "consensus_candidate")
        self.assertEqual(lost["independent_reader_count"], 2)

    def test_scene_goals_and_playtest_coverage(self):
        weak = inspect_scene_goals("空氣很好。窗外有樹。時間過去。什麼都沒有發生。" * 8)
        self.assertEqual(weak["status"], "WARN")
        strong = inspect_scene_goals("他要開門離開，可是鎖卡住了。最後只好改走陽台，心裡更慌。")
        self.assertIn(strong["status"], {"PASS", "WARN"})
        state = empty_state("p", "s")
        state["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []}}
        state["storylets"] = {"active": [
            {"id": "s1", "conditions": {"location": "room"}, "effects": [], "next_storylets": ["s2"]},
            {"id": "s2", "conditions": {"location": "nowhere"}, "effects": [], "next_storylets": []},
        ]}
        state = refresh_state_hash(state)
        cov = analyze_playtest_coverage(state, actor_id="player", played_storylet_ids=[], played_branch_ids=["main"])
        self.assertEqual(cov["status"], "WARN")
        self.assertTrue(any(f["code"] in {"PLAYTEST_NO_COVERAGE", "STORYLET_UNREACHABLE", "PLAYTEST_SINGLE_PATH"} for f in cov["findings"]))


if __name__ == "__main__":
    unittest.main()
