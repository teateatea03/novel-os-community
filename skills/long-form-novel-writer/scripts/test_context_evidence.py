"""Synthetic source integrity and exact character inclusion regressions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from context_evidence import assess_context, context_source_spans, text_hash

SCRIPT = Path(__file__).with_name("build_context_pack.py")


class ContextEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "story-bible.md"
        self.source.write_text("# Synthetic\nSignal alpha.\nSignal beta.\n", encoding="utf-8")

    def build(self, *extra):
        subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root),
                        "--chapter", "sample", "--query", "Signal", *extra],
                       check=True, capture_output=True, text=True)
        self.pack = self.root / "context-packs/sample.md"
        self.text = self.pack.read_text(encoding="utf-8")
        self.manifest = json.loads(self.pack.with_suffix(".json").read_text())
        return self.assess()

    def assess(self, limit=None):
        return assess_context(self.root, self.pack, self.text,
                              len(self.text) if limit is None else limit)

    def test_builder_refuses_output_escape_and_invalid_utf8(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root),
                                 "--chapter", "../escape"], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "escape.md").exists())
        self.source.write_bytes(b"Signal \xff")
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root),
                                 "--chapter", "sample"], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "context-packs/sample.md").exists())

    def test_selection_summary_discloses_unlisted_ranked_chunks(self):
        for i in range(84):
            (self.root / f"extra-{i}.md").write_text("Signal synthetic", encoding="utf-8")
        result = self.build("--top-k", "1", "--context-policy", "lossless-addressable")
        summary = result["selection_summary"]
        self.assertGreater(summary["unlisted_ranked_chunks"], 0)
        self.assertEqual(summary["ranked_chunks"], summary["inline_chunks"] +
                         summary["addressable_overflow_chunks"] + summary["unlisted_ranked_chunks"])

    def test_exact_cli_pack_hashes_and_unicode_boundaries(self):
        self.source.write_text("# Synthetic\nSignal 星🌟尾\n", encoding="utf-8")
        self.assertEqual(self.build()["status"], "verified")
        entry = self.manifest["sources"][0]
        a, b = entry["pack_start"], entry["pack_end"]
        for limit, status, count in [(a - 1, "omitted", 0), (a, "omitted", 0),
                                     (a + 1, "partial", 1), (b - 1, "partial", b-a-1),
                                     (b, "full", b-a), (b+1, "full", b-a)]:
            with self.subTest(limit=limit):
                assessment = self.assess(limit)
                evidence = assessment["sources"][0]["inclusion"]
                self.assertEqual(evidence["status"], status)
                self.assertEqual(evidence["included_characters"], count)
                snapshots = context_source_spans(self.root, assessment)
                if count:
                    self.assertEqual(snapshots["story-bible.md"]["ranges"], [[0, count]])
                else:
                    self.assertEqual(snapshots, {})

    def test_changed_same_name_and_line_insert_are_stale(self):
        for new in ("# Synthetic\nSignal changed.\n", "prefix\n# Synthetic\nSignal alpha.\nSignal beta.\n"):
            self.build()
            self.source.write_text(new, encoding="utf-8")
            result = self.assess()
            self.assertEqual(result["status"], "stale")
            self.assertEqual(result["sources"][0]["reason"], "source_hash_mismatch")

    def test_missing_source_precise(self):
        self.build()
        self.source.unlink()
        self.assertEqual(self.assess()["sources"][0]["status"], "missing")

    def test_changed_pack_rejected(self):
        self.build()
        self.text += "tampered"
        self.assertEqual(self.assess()["reason"], "pack_hash_mismatch")

    def test_malformed_ranges_rejected_even_with_matching_pack_hash(self):
        self.build()
        self.manifest["sources"][0]["pack_end"] = len(self.text) + 1
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
        self.assertEqual(self.assess()["status"], "invalid")

    def test_legacy_policy_explicit_and_unknown_rejected(self):
        self.build()
        self.pack.with_suffix(".json").unlink()
        self.assertEqual(self.assess()["status"], "invalid")
        self.text = "Synthetic legacy context pack"
        self.pack.write_text(self.text, encoding="utf-8")
        self.assertEqual(self.assess()["status"], "legacy_unverified")
        for schema, expected in [("minis.context-pack.v4", "legacy_unverified"), ("unknown", "invalid")]:
            self.pack.with_suffix(".json").write_text(json.dumps({"schema": schema}))
            self.assertEqual(self.assess()["status"], expected)

    def test_addressable_overflow_not_prompt_text(self):
        for i in range(5):
            (self.root / f"source-{i}.md").write_text("Signal " * 40, encoding="utf-8")
        result = self.build("--top-k", "1", "--context-policy", "lossless-addressable")
        overflow = [s for s in result["sources"] if s["placement"] == "addressable_overflow"]
        self.assertTrue(overflow)
        self.assertTrue(all(s["inclusion"]["status"] == "omitted" for s in overflow))
        self.assertTrue(all(s["source_sha256"] for s in overflow))

    def test_source_changes_between_assessment_and_evidence_read(self):
        result = self.build()
        self.source.write_text("Signal replaced", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed during preparation"):
            context_source_spans(self.root, result)

    def test_crlf_byte_fingerprint_and_normalized_ranges(self):
        self.source.write_bytes(b"# Synthetic\r\nSignal alpha.\r\n")
        result = self.build()
        self.assertEqual(result["status"], "verified")
        self.assertNotIn("\r", context_source_spans(self.root, result)["story-bible.md"]["text"])
        self.source.write_bytes(b"# Synthetic\nSignal alpha.\n")
        self.assertEqual(self.assess()["status"], "stale")

    def test_overflow_changes_also_invalidate(self):
        (self.root / "extra.md").write_text("Signal overflow", encoding="utf-8")
        result = self.build("--top-k", "1", "--context-policy", "lossless-addressable")
        entry = next(s for s in result["sources"] if s["placement"] == "addressable_overflow")
        (self.root / entry["file"]).write_text("Signal replacement", encoding="utf-8")
        self.assertEqual(self.assess()["status"], "stale")

    def test_symlink_sources_and_manifest_rejected(self):
        self.build()
        target = self.root / "target.md"
        target.write_text("Synthetic outside evidence", encoding="utf-8")
        self.source.unlink()
        try:
            self.source.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertEqual(self.assess()["status"], "invalid")
        self.source.unlink()
        self.source.write_text("Signal", encoding="utf-8")
        self.build()
        manifest = self.pack.with_suffix(".json")
        content = manifest.read_bytes()
        manifest.unlink()
        replacement = self.root / "replacement.json"
        replacement.write_bytes(content)
        manifest.symlink_to(replacement)
        self.assertEqual(self.assess()["status"], "invalid")

    def test_nonfinite_or_inconsistent_manifest_is_invalid(self):
        self.build()
        for value in (float("nan"), float("inf"), -1, True, 999):
            self.manifest["selection_summary"]["inline_chunks"] = value
            self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
            self.assertEqual(self.assess()["status"], "invalid")
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest).replace('999', '1e999'))
        self.assertEqual(self.assess()["status"], "invalid")

    def test_noncanonical_source_aliases_rejected(self):
        self.build()
        for name in ("./story-bible.md", "folder//story-bible.md", "story-bible.md/"):
            self.manifest["sources"][0]["file"] = name
            self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
            self.assertEqual(self.assess()["status"], "invalid")

    def test_absolute_source_path_rejected(self):
        self.build()
        self.manifest["sources"][0]["file"] = str(self.source)
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
        self.assertEqual(self.assess()["status"], "invalid")

    def test_source_path_escape_invalid(self):
        self.build()
        self.manifest["sources"][0]["file"] = "../outside.md"
        self.pack.with_suffix(".json").write_text(json.dumps(self.manifest))
        self.assertEqual(self.assess()["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
