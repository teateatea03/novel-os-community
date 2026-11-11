"""Optional real EPUBCheck validation of original synthetic exports.

Set EPUBCHECK_JAR to an official EPUBCheck distribution's epubcheck.jar and
put Java on PATH before running scripts/run_tests.py. Without that explicit
opt-in, this test is skipped and the portable standard-library suite still
runs. The validator and generated publications stay outside the source tree.
These are agent-test fixtures, not author acceptance or literary evidence.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from .manuscript_export import export_manuscript


class ManuscriptEpubCheckTests(unittest.TestCase):
    def test_synthetic_exports_pass_epubcheck(self):
        jar_value = os.environ.get("EPUBCHECK_JAR")
        if not jar_value:
            self.skipTest("Set EPUBCHECK_JAR to run real EPUBCheck validation")
        jar = Path(jar_value).expanduser().resolve()
        self.assertTrue(jar.is_file(), "EPUBCHECK_JAR must name an existing jar")
        for layout in ("chapters", "interactive/scenes", "scenes"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source_dir = root / layout
                source_dir.mkdir(parents=True)
                (root / "project.json").write_text(
                    json.dumps({"title": "Synthetic & <Metadata> 😀"}), encoding="utf-8"
                )
                for number in (1, 2):
                    (source_dir / f"{number:02d}.md").write_text(
                        f"# 合成章節 {number} & <Title>\nSynthetic body. 😀\n",
                        encoding="utf-8",
                    )
                before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
                adapter = SimpleNamespace(project_root=root, project_id="synthetic")
                report = export_manuscript(adapter)
                result = subprocess.run(
                    ["java", "-jar", str(jar), report["epub_path"], "--failonwarnings"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(report["document_count"], 2)
                self.assertFalse(report["canon_write"])
                for path, content in before.items():
                    self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
