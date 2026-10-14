#!/usr/bin/env python3
"""Synthetic fixtures only; model CLI is replaced with a local test executable."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from review_evidence import check_binding, consolidate_binding, capture_source, make_report, recheck_report, source_path, validate_anchor, validate_report

HERE = Path(__file__).resolve().parent


def issue():
    return {"category": "fact", "severity": "P0", "claim": "Synthetic mismatch",
            "evidence_a": {"file": "chapters/demo.md", "line": 1, "quote": "The cup is blue."},
            "evidence_b": {"file": "chapters/demo.md", "line": 2, "quote": "The cup is green."},
            "minimal_fix": "Check the cup", "confidence": 0.8}


def payload():
    return {"summary": "Synthetic review", "issues": [issue()], "questions": []}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "chapters").mkdir()
        self.draft = self.root / "chapters/demo.md"
        self.draft.write_text("The cup is blue.\nThe cup is green.\n", encoding="utf-8")
        self.sources = {"chapters/demo.md": capture_source(self.root, "chapters/demo.md")}

    def report(self, data="default"):
        return make_report(payload() if data == "default" else data, self.sources,
                           "chapters/demo.md", "continuity", "synthetic", "raw.txt", "prompt", {})

    def test_anchors_do_not_confirm_semantics_or_resolve(self):
        data = payload()
        data["issues"][0]["status"] = "resolved"
        data["status"] = "owner_accepted"
        report = self.report(data)
        self.assertEqual(report["machine_suggestion"], data)
        self.assertEqual(report["status"], "machine_suggestion")
        finding = report["validation"]["findings"][0]
        self.assertEqual(finding["status"], "anchored")
        self.assertEqual(finding["semantic_status"], "unverified")
        self.assertEqual(finding["resolution"], "unresolved")
        self.assertEqual(data["issues"][0]["status"], "resolved")

    def test_bad_duplicate_and_stitched_quotes(self):
        for quote, reason in [("absent", "quote_not_found"),
                              ("The cup", "ambiguous_quote"),
                              ("blue.green", "quote_not_found")]:
            anchor = dict(issue()["evidence_a"], quote=quote)
            self.assertEqual(validate_anchor(anchor, self.sources)["reason"], reason)

    def test_wrong_lines_and_invalid_indices(self):
        for line in [0, -1, 2, True, "1", None, 1.0]:
            self.assertEqual(validate_anchor(dict(issue()["evidence_a"], line=line), self.sources)["status"], "unverified")

    def test_outside_prompt_is_not_evidence(self):
        self.sources["chapters/demo.md"]["ranges"] = [[0, 16]]
        self.assertEqual(validate_anchor(issue()["evidence_b"], self.sources)["reason"], "quote_not_in_prompt")

    def test_source_paths_reject_aliases(self):
        for name in ["chapters//demo.md", "chapters/demo.md/", "./chapters/demo.md"]:
            with self.assertRaises(ValueError):
                source_path(self.root, name)

    def test_source_identity_is_exact(self):
        for name in ["./chapters/demo.md", "../demo.md", "/demo.md", "unknown.md"]:
            self.assertEqual(validate_anchor(dict(issue()["evidence_a"], file=name), self.sources)["status"], "unverified")

    def test_duplicate_evidence_is_not_dual_evidence(self):
        data = payload()
        data["issues"][0]["evidence_b"] = copy.deepcopy(data["issues"][0]["evidence_a"])
        self.assertEqual(self.report(data)["validation"]["findings"][0]["status"], "unverified")

    def test_containing_quotes_are_duplicate_evidence_both_directions(self):
        for first, second in [("The cup is blue", "The cup is blue."),
                              ("The cup is blue.", "The cup is blue"),
                              ("cup is blue", "The cup is blue.")]:
            data = payload()
            data["issues"][0]["evidence_a"]["quote"] = first
            data["issues"][0]["evidence_b"] = dict(data["issues"][0]["evidence_a"], quote=second)
            finding = self.report(data)["validation"]["findings"][0]
            self.assertEqual(finding["status"], "unverified")
            self.assertEqual(finding["anchors"][-1]["reason"], "duplicate_evidence")
            self.assertEqual(finding["semantic_status"], "unverified")
            self.assertEqual(finding["resolution"], "unresolved")
        self.assertEqual(self.report()["validation"]["findings"][0]["status"], "anchored")

    def test_binding_reads_once_per_check_and_checks_conflicting_hashes(self):
        original = self.report()["source_binding"]
        repeated = original * 50
        real_read = Path.read_bytes
        reads = []
        def read(path):
            reads.append(path)
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", read):
            self.assertEqual(check_binding(self.root, repeated)["status"], "current")
            self.assertEqual(reads, [self.draft])
            conflict = repeated + [dict(original[0], sha256="0" * 64)]
            self.assertEqual(check_binding(self.root, consolidate_binding(conflict))["status"], "stale")
            self.assertEqual(reads, [self.draft] * 2)
            self.draft.write_text("Changed between checks.")
            self.assertEqual(check_binding(self.root, repeated)["status"], "stale")
            self.assertEqual(reads, [self.draft] * 3)
        self.assertEqual(len(consolidate_binding(repeated)), 1)
        self.assertEqual(len(consolidate_binding(conflict)), 2)

    def test_malformed_report_and_issues(self):
        for data in [[], None, True, 1, "report", {}, {"issues": {}}]:
            self.assertEqual(self.report(data)["validation"]["status"], "unverified")
        for item in [None, [], {}, dict(issue(), category=[]), dict(issue(), confidence=True),
                     dict(issue(), confidence=2), dict(issue(), evidence_a=None)]:
            data = payload(); data["issues"] = [item]
            self.assertEqual(self.report(data)["validation"]["findings"][0]["status"], "unverified")

    def test_finding_ids_are_stable_and_draft_bound(self):
        original = self.report()["validation"]["findings"][0]["finding_id"]
        self.assertEqual(original, self.report()["validation"]["findings"][0]["finding_id"])
        self.draft.write_text(self.draft.read_text() + "Elsewhere.\n")
        self.sources["chapters/demo.md"] = capture_source(self.root, "chapters/demo.md")
        self.assertNotEqual(original, self.report()["validation"]["findings"][0]["finding_id"])

    def test_any_edit_including_whitespace_is_stale(self):
        for suffix in [" ", "\n", "Elsewhere."]:
            original = self.draft.read_text()
            report = self.report()
            self.draft.write_text(original + suffix)
            self.assertEqual(recheck_report(self.root, report)["status"], "stale")
            self.assertEqual(report["validation"]["findings"][0]["resolution"], "unresolved")
            self.draft.write_text(original)

    def test_deleted_source_and_legacy_report(self):
        report = self.report()
        self.draft.unlink()
        self.assertEqual(recheck_report(self.root, report)["status"], "stale")
        self.assertEqual(recheck_report(self.root, {"schema": "minis.novel-review.v1"})["status"], "unverified")

    def test_crlf_hash_and_one_based_line(self):
        self.draft.write_bytes(b"The cup is blue.\r\nThe cup is green.\r\n")
        sources = {"chapters/demo.md": capture_source(self.root, "chapters/demo.md")}
        self.assertEqual(validate_anchor(issue()["evidence_b"], sources)["status"], "anchored")
        self.assertNotEqual(sources["chapters/demo.md"]["sha256"], self.sources["chapters/demo.md"]["sha256"])


class ReviewCliTests(unittest.TestCase):
    def setUp(self):
        EvidenceTests.setUp(self)
        self.bin = self.root / "bin"; self.bin.mkdir()
        executable = self.bin / "minis-model-use"
        executable.write_text("#!" + sys.executable + '''
import os, pathlib, sys
args = sys.argv
pathlib.Path(os.environ['SEEN']).write_text(pathlib.Path(args[args.index('--prompt-file')+1]).read_text())
if os.environ.get('EDIT'):
    path = pathlib.Path(os.environ['EDIT'])
    path.write_text(path.read_text() + ' changed')
pathlib.Path(args[args.index('--output')+1]).write_text(os.environ['PAYLOAD'])
sys.exit(int(os.environ.get('RETURN_CODE', '0')))
''', encoding="utf-8")
        executable.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
                        PAYLOAD=json.dumps(payload()), SEEN=str(self.root / "seen.txt"))

    def run_review(self, **env):
        result = subprocess.run([sys.executable, str(HERE / "independent_review.py"),
                                 "--root", str(self.root), "--chapter", "demo", "--model", "synthetic"],
                                capture_output=True, text=True, env=dict(self.env, **env))
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(Path(result.stdout.strip()).read_text())

    def test_cli_calls_validator_and_preserves_raw(self):
        result, report = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["validation"]["findings"][0]["status"], "anchored")
        self.assertEqual((self.root / report["raw_file"]).read_text(), self.env["PAYLOAD"])
        self.assertEqual(report["freshness"]["status"], "current")
        self.assertIn("The cup is green.", (self.root / "seen.txt").read_text())

    def test_cli_containing_quotes_stay_unverified(self):
        data = payload()
        data["issues"][0]["evidence_a"]["quote"] = "The cup is blue"
        data["issues"][0]["evidence_b"] = {"file": "chapters/demo.md", "line": 1, "quote": "The cup is blue."}
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        finding = report["validation"]["findings"][0]
        self.assertEqual(finding["status"], "unverified")
        self.assertEqual(finding["anchors"][-1]["reason"], "duplicate_evidence")
        self.assertEqual(report["machine_suggestion"], data)

    def test_cli_multiple_chunks_have_one_binding_and_one_read_per_check(self):
        source = self.root / "story-bible.md"
        source.write_text("# First\nSynthetic blue rule.\n# Second\nSynthetic green rule.\n# Third\nSynthetic red rule.\n")
        built = subprocess.run([sys.executable, str(HERE / "build_context_pack.py"), "--root", str(self.root),
                                "--chapter", "demo"], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        result, report = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        chunks = [entry for entry in report["context_receipt"]["sources"] if entry["file"] == "story-bible.md"]
        self.assertEqual(len(chunks), 3)
        bindings = report["source_binding"]
        self.assertEqual(len([entry for entry in bindings if entry["file"] == "story-bible.md"]), 1)
        reads = []
        real_read = Path.read_bytes
        def read(path):
            reads.append(path)
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", read):
            self.assertEqual(check_binding(self.root, bindings)["status"], "current")
            self.assertEqual(len(reads), len(bindings))
            self.assertEqual(reads.count(source), 1)
            source.write_text(source.read_text() + " ")
            self.assertEqual(check_binding(self.root, bindings)["status"], "stale")
            self.assertEqual(reads.count(source), 2)

    def test_cli_nonobject_and_invalid_json_retained(self):
        for text in ["[]", "null", "invalid", '{"confidence":NaN}', '{"x":1e999}', '{"nested":[-1e999]}']:
            result, report = self.run_review(PAYLOAD=text)
            self.assertEqual(result.returncode, 2)
            self.assertEqual((self.root / report["raw_file"]).read_text(), text)
            self.assertTrue(report.get("status") == "unverified" or report["validation"]["status"] == "unverified")

    def test_cli_rejects_lone_surrogate_without_partial_report(self):
        invalid = json.dumps({"summary": "\ud800", "issues": [], "questions": []})
        result, report = self.run_review(PAYLOAD=invalid)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "unverified")
        self.assertEqual((self.root / report["raw_file"]).read_text(), invalid)
        self.assertTrue(all(path.stat().st_size for path in (self.root / "reviews").glob("*.json")))

    def test_cli_check_review_escapes_malformed_source_identity(self):
        result, report = self.run_review()
        path = Path(result.stdout.strip())
        report["source_binding"][0]["file"] = "bad\ud800.md"
        path.write_text(json.dumps(report), encoding="utf-8")
        check = subprocess.run([sys.executable, str(HERE / "independent_review.py"), "--root", str(self.root),
                                "--check-review", str(path)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 2, check.stderr)
        self.assertEqual(json.loads(check.stdout)["status"], "stale")

    def test_cli_model_error_and_midflight_edit(self):
        result, report = self.run_review(RETURN_CODE="1")
        self.assertEqual((result.returncode, report["status"]), (2, "unavailable"))
        self.assertEqual(recheck_report(self.root, report)["status"], "unverified")
        result, report = self.run_review(EDIT=str(self.draft))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["freshness"]["status"], "stale")
        self.assertEqual(report["validation"]["findings"][0]["status"], "stale")

    def test_cli_check_review_is_read_only(self):
        result, report = self.run_review()
        path = Path(result.stdout.strip())
        before = path.read_bytes()
        self.draft.write_text(self.draft.read_text() + " ")
        check = subprocess.run([sys.executable, str(HERE / "independent_review.py"), "--root", str(self.root),
                                "--check-review", str(path)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 2)
        self.assertEqual(json.loads(check.stdout)["status"], "stale")
        self.assertEqual(path.read_bytes(), before)

    def test_cli_stale_context_prevents_model_call(self):
        built = subprocess.run([sys.executable, str(HERE / "build_context_pack.py"), "--root", str(self.root),
                                "--chapter", "demo"], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        cp = self.root / "context-packs/demo.md"
        cp.write_text(cp.read_text() + " changed")
        result, report = self.run_review()
        self.assertEqual((result.returncode, report["status"]), (2, "stale"))
        self.assertFalse((self.root / "seen.txt").exists())

    def test_cli_context_adds_style_coverage_beyond_style_prefix(self):
        style = self.root / "style-sheet.md"
        style.write_bytes(("s" * 12000 + "\r\nContext-only rule.\r\n").encode())
        built = subprocess.run([sys.executable, str(HERE / "build_context_pack.py"), "--root", str(self.root),
                                "--chapter", "demo"], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        data = payload()
        data["issues"][0]["evidence_b"] = {"file": "style-sheet.md", "line": 2, "quote": "Context-only rule."}
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(report["validation"]["findings"][0]["anchors"][1]["status"], "anchored")
        self.assertIn("Context-only rule.", (self.root / "seen.txt").read_text())

    def test_cli_context_boundary_binds_only_actual_prompt_text(self):
        source = self.root / "story-bible.md"
        source.write_text("Visible marker. " + "z " * 16000 + "Hidden marker.", encoding="utf-8")
        built = subprocess.run([sys.executable, str(HERE / "build_context_pack.py"), "--root", str(self.root),
                                "--chapter", "demo", "--budget", "50000"], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        data = payload()
        data["issues"][0]["evidence_b"] = {"file": "story-bible.md", "line": 1, "quote": "Hidden marker."}
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(report["context_receipt"]["status"], "verified")
        self.assertGreater(report["prompt_sections"]["context"]["omitted_characters"], 0)
        self.assertEqual(report["validation"]["findings"][0]["anchors"][1]["reason"], "quote_not_in_prompt")
        self.assertNotIn("Hidden marker.", (self.root / "seen.txt").read_text())
        data["issues"][0]["evidence_b"]["quote"] = "Visible marker."
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(report["validation"]["findings"][0]["anchors"][1]["status"], "anchored")
        source.write_text(source.read_text() + " ")
        self.assertEqual(recheck_report(self.root, report)["status"], "stale")

    def test_cli_context_crlf_fingerprint_is_byte_exact(self):
        source = self.root / "story-bible.md"
        source.write_bytes(b"Synthetic header.\r\nA violet cup.\r\n")
        built = subprocess.run([sys.executable, str(HERE / "build_context_pack.py"), "--root", str(self.root),
                                "--chapter", "demo"], capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        data = payload()
        data["issues"][0]["evidence_b"] = {"file": "story-bible.md", "line": 2, "quote": "A violet cup."}
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(report["validation"]["findings"][0]["anchors"][1]["status"], "anchored")
        source.write_bytes(source.read_bytes().replace(b"\r\n", b"\n"))
        self.assertEqual(recheck_report(self.root, report)["status"], "stale")
        result, report = self.run_review()
        self.assertEqual((result.returncode, report["status"]), (2, "stale"))

    def test_cli_legacy_context_and_style_truncation(self):
        packs = self.root / "context-packs"; packs.mkdir()
        (packs / "demo.md").write_text("x" * 30001)
        (self.root / "style-sheet.md").write_text("s" * 12000 + "hidden rule")
        data = payload()
        data["issues"][0]["evidence_b"] = {"file": "style-sheet.md", "line": 1, "quote": "hidden rule"}
        result, report = self.run_review(PAYLOAD=json.dumps(data))
        self.assertEqual(report["context_receipt"]["status"], "legacy_unverified")
        self.assertEqual(report["context_receipt"]["omitted_characters"], 1)
        self.assertEqual(report["validation"]["findings"][0]["anchors"][1]["reason"], "quote_not_in_prompt")
        self.assertNotIn("hidden rule", (self.root / "seen.txt").read_text())


if __name__ == "__main__":
    unittest.main()
