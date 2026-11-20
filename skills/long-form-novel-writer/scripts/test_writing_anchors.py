"""Synthetic optional anchor ordering, exclusion and real-prefix evidence tests."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import independent_review

from context_evidence import assess_context, text_hash
from writing_anchors import load_anchors

SCRIPT = Path(__file__).with_name("build_context_pack.py")


class WritingAnchorsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tail = "# Synthetic prior scene\nSignal clock stops.\nSignal lamp goes dark.\n"
        self.style = "# Synthetic style sample\nSignal rain ticked. She waited.\n"
        (self.root / "previous.md").write_text(self.tail, encoding="utf-8")
        (self.root / "original.md").write_text(self.style, encoding="utf-8")
        (self.root / "story-bible.md").write_text("Signal general reference.", encoding="utf-8")
        self.config = {"schema": "minis.writing-anchors.v1", "budget_characters": 2400,
                       "anchors": [
            {"id": "style", "role": "style_original", "order": 20, "file": "original.md",
             "source_sha256": text_hash(self.style), "start": 2, "end": 2,
             "applies_to": {"povs": ["observer"], "scenes": ["quiet"]}},
            {"id": "tail", "role": "previous_chapter_tail", "order": 10, "file": "previous.md",
             "source_sha256": text_hash(self.tail), "tail_lines": 1}]}

    def build(self, *extra):
        (self.root / "anchors.json").write_text(json.dumps(self.config), encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root),
                                 "--chapter", "next", "--query", "Signal", "--pov", "observer",
                                 "--scene", "quiet", "--writing-anchors", "anchors.json", *extra],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.pack = self.root / "context-packs/next.md"
        self.text = self.pack.read_text(encoding="utf-8")
        self.manifest = json.loads(self.pack.with_suffix(".json").read_text())
        return assess_context(self.root, self.pack, self.text, len(self.text))

    def test_anchor_order_precedes_ranked_retrieval_and_preserves_exact_range(self):
        result = self.build("--top-k", "1")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(self.manifest["writing_anchors"]["render_order"], ["tail", "style"])
        self.assertEqual([s.get("anchor_id") for s in self.manifest["sources"]], ["tail", "style", None])
        source = self.manifest["sources"][0]
        self.assertEqual(self.text[source["pack_start"]:source["pack_end"]], "Signal lamp goes dark.")
        self.assertNotIn("Signal clock stops.", self.text)

    def test_consumer_prefix_cannot_claim_omitted_or_partial_anchor_was_read(self):
        self.build()
        first, second = self.manifest["sources"][:2]
        for limit, expected in [(first["pack_start"], ["omitted", "omitted"]),
                                 (first["pack_start"] + 1, ["partial", "omitted"]),
                                 (first["pack_end"], ["full", "omitted"]),
                                 (second["pack_end"], ["full", "full"])]:
            result = assess_context(self.root, self.pack, self.text, limit)
            self.assertEqual([a["inclusion"]["status"] for a in result["writing_anchors"]], expected)

    def test_character_reservation_and_budget_omission_are_explicit(self):
        self.config["budget_characters"] = len("Signal lamp goes dark.")
        result = self.build("--budget", "100", "--top-k", "1")
        reports = result["writing_anchors"]
        self.assertEqual(reports[0]["inclusion"]["status"], "full")
        self.assertEqual(reports[1]["reason"], "anchor_character_budget")
        self.assertEqual(reports[1]["inclusion"]["status"], "omitted")
        self.assertNotIn("Signal rain ticked.", self.text)

    def test_token_reservation_and_omission_under_both_policies(self):
        for policy in ("lossless-addressable", "lossy-admission"):
            with self.subTest(policy=policy):
                result = self.build("--context-window", "14010", "--context-policy", policy)
                self.assertEqual(result["writing_anchors"][0]["status"], "inline")
                self.assertEqual(result["writing_anchors"][1]["reason"], "input_token_budget")
                self.assertEqual(result["writing_anchors"][1]["inclusion"]["status"], "omitted")

    def test_applicability_missing_values_and_explicit_style_change(self):
        for args in (("--pov", "other"), ("--scene", "")):
            result = self.build(*args)
            self.assertEqual(result["writing_anchors"][1]["reason"], "not_applicable")
            self.assertNotIn("Signal rain ticked.", self.text)
        self.config["anchors"][0]["skip_reason"] = "intentional_style_change"
        result = self.build()
        self.assertEqual(result["writing_anchors"][1]["reason"], "intentional_style_change")

    def test_first_chapter_missing_and_stale_are_explicit_without_stale_text(self):
        self.config["anchors"][1] = {"id": "tail", "role": "previous_chapter_tail", "order": 10,
                                      "skip_reason": "first_chapter"}
        self.assertEqual(self.build()["writing_anchors"][0]["reason"], "first_chapter")
        (self.root / "original.md").unlink()
        self.assertEqual(self.build()["writing_anchors"][1]["reason"], "source_missing")
        (self.root / "original.md").write_text("Signal revised.")
        self.assertEqual(self.build()["writing_anchors"][1]["reason"], "source_hash_mismatch")
        self.assertNotIn("Signal revised.", self.text)

    def test_post_build_source_change_still_fails_closed(self):
        self.build()
        (self.root / "previous.md").write_text("Changed after selection.")
        result = assess_context(self.root, self.pack, self.text, len(self.text))
        self.assertEqual(result["status"], "stale")

    def test_actual_review_prompt_reports_truncated_anchors_without_model_call(self):
        self.tail = "Visible marker. " + "z " * 16000 + "Hidden tail marker."
        (self.root / "previous.md").write_text(self.tail, encoding="utf-8")
        self.config["anchors"][1]["source_sha256"] = text_hash(self.tail)
        self.config["budget_characters"] = 50000
        self.build("--budget", "50000")
        (self.root / "chapters").mkdir()
        (self.root / "chapters/next.md").write_text("Synthetic next scene.", encoding="utf-8")
        captured = []
        def fake_model(command, **kwargs):
            captured.append(Path(command[command.index("--prompt-file") + 1]).read_text())
            Path(command[command.index("--output") + 1]).write_text(
                json.dumps({"summary": "Synthetic response", "issues": [], "questions": []}))
            return subprocess.CompletedProcess(command, 0, "", "")
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["independent_review.py", "--root", str(self.root),
                                             "--chapter", "next", "--model", "synthetic"]), \
                mock.patch.object(independent_review.subprocess, "run", side_effect=fake_model), \
                contextlib.redirect_stdout(output):
            independent_review.main()
        report = json.loads(Path(output.getvalue().strip()).read_text())
        self.assertEqual(len(captured), 1)
        self.assertNotIn("Hidden tail marker.", captured[0])
        self.assertNotIn("Signal rain ticked.", captured[0])
        self.assertEqual([a["inclusion"]["status"] for a in report["context_receipt"]["writing_anchors"]],
                         ["partial", "omitted"])

    def test_manifest_anchor_identity_and_order_cannot_disagree_with_source(self):
        self.build()
        original = json.dumps(self.manifest)
        for field, value in (("role", "previous_chapter_tail"), ("source_sha256", "0" * 64),
                             ("start", 100)):
            self.manifest = json.loads(original)
            self.manifest["writing_anchors"]["anchors"][1][field] = value
            self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
            self.assertEqual(assess_context(self.root, self.pack, self.text, len(self.text))["status"], "invalid")
        self.manifest = json.loads(original)
        self.manifest["writing_anchors"]["render_order"].reverse()
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
        self.assertEqual(assess_context(self.root, self.pack, self.text, len(self.text))["status"], "invalid")

    def test_lossy_policy_reserves_verbatim_anchor_whitespace(self):
        text = "A" + " " * 2000 + "B"
        (self.root / "previous.md").write_text(text, encoding="utf-8")
        self.config["anchors"][1]["source_sha256"] = text_hash(text)
        result = self.build("--context-window", "14004", "--context-policy", "lossy-admission")
        self.assertEqual(result["writing_anchors"][0]["reason"], "input_token_budget")
        self.assertNotIn(text, self.text)

    def test_anchor_metadata_requires_decision_collection(self):
        self.build()
        del self.manifest["writing_anchors"]
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
        self.assertEqual(assess_context(self.root, self.pack, self.text, len(self.text))["status"], "invalid")

    def test_repeated_build_is_byte_deterministic(self):
        self.build()
        first = self.pack.read_bytes(), self.pack.with_suffix(".json").read_bytes()
        self.build()
        self.assertEqual(first, (self.pack.read_bytes(), self.pack.with_suffix(".json").read_bytes()))

    def test_invalid_config_and_paths_rejected(self):
        for field, value in (("id", "../bad"), ("role", "canon"), ("order", True),
                             ("file", "../outside.md"), ("source_sha256", "bad"),
                             ("applies_to", {"povs": "observer"}), ("start", True)):
            with self.subTest(field=field):
                old = self.config["anchors"][0].get(field)
                self.config["anchors"][0][field] = value
                (self.root / "anchors.json").write_text(json.dumps(self.config))
                with self.assertRaises(ValueError):
                    load_anchors(self.root, "anchors.json", chapter="next", pov="observer", scene="quiet")
                if old is None:
                    del self.config["anchors"][0][field]
                else:
                    self.config["anchors"][0][field] = old

    def test_empty_and_out_of_range_excerpt_are_explicit(self):
        self.config["anchors"][0]["end"] = 900
        self.assertEqual(self.build()["writing_anchors"][1]["reason"], "source_range_missing")
        (self.root / "previous.md").write_text("\n")
        self.config["anchors"][1]["source_sha256"] = text_hash("\n")
        self.assertEqual(self.build()["writing_anchors"][0]["reason"], "empty_excerpt")


if __name__ == "__main__":
    unittest.main()
