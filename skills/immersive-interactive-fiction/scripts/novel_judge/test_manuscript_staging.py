"""Agent-test coverage for export generation failure; synthetic prose only."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from . import manuscript_export


class ManuscriptStagingTests(unittest.TestCase):
    def test_epub_generation_failure_preserves_previous_outputs_and_retry_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapters = root / "chapters"
            chapters.mkdir()
            chapter = chapters / "01.md"
            chapter.write_text("# Synthetic chapter\nFirst sample.\n", encoding="utf-8")
            adapter = SimpleNamespace(project_root=root, project_id="synthetic")
            out = root / "review"
            manuscript_export.export_manuscript(adapter, output_dir=out)
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            revised = "# Synthetic chapter\nA longer second sample.\n"
            chapter.write_text(revised, encoding="utf-8")
            source_before = chapter.read_bytes()

            real_writestr = zipfile.ZipFile.writestr

            def fail_while_writing(zf, name, data, *args, **kwargs):
                if name == "OEBPS/text/doc0001.xhtml":
                    raise OSError("injected export write failure")
                return real_writestr(zf, name, data, *args, **kwargs)

            with patch.object(zipfile.ZipFile, "writestr", new=fail_while_writing):
                with self.assertRaisesRegex(OSError, "injected export write failure"):
                    manuscript_export.export_manuscript(adapter, output_dir=out)

            self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)
            report = manuscript_export.export_manuscript(adapter, output_dir=out)
            self.assertEqual(Path(report["markdown_path"]), out / "synthetic.md")
            self.assertEqual(Path(report["epub_path"]), out / "synthetic.epub")
            self.assertIn("A longer second sample.", (out / "synthetic.md").read_text(encoding="utf-8"))
            with zipfile.ZipFile(out / "synthetic.epub") as epub:
                self.assertIn(b"A longer second sample.", epub.read("OEBPS/text/doc0001.xhtml"))
            self.assertEqual(json.loads((out / "export-report.json").read_text(encoding="utf-8")), report)
            self.assertEqual({p.name for p in out.iterdir()}, set(before))
            self.assertEqual(chapter.read_bytes(), source_before)


if __name__ == "__main__":
    unittest.main()
