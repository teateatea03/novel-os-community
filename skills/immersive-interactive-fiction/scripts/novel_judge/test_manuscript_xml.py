"""Agent-generated synthetic XML export regressions; not reader-quality evidence."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

from .manuscript_export import export_manuscript


class ManuscriptXmlTests(unittest.TestCase):
    def make_project(self, root, body='# Synthetic\n合成測試。', title='Synthetic'):
        (root / 'chapters').mkdir(exist_ok=True)
        (root / 'chapters/01.md').write_text(body, encoding='utf-8')
        (root / 'project.json').write_text(json.dumps({'title': title}), encoding='utf-8')
        return SimpleNamespace(project_root=root, project_id='synthetic')

    def test_invalid_body_rejected_without_output_or_source_changes(self):
        for char in ('\x00', '\x0b', '\x0c', '\x1f', '\ufffe', '\uffff'):
            with self.subTest(codepoint=ord(char)), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                a = self.make_project(root, '# Synthetic\nAgent-test' + char)
                before = {p.name: p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError, 'forbidden by XML 1.0'):
                    export_manuscript(a)
                self.assertFalse((root / 'workbench').exists())
                self.assertEqual(before, {p.name: p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_invalid_title_preserves_existing_exports(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = self.make_project(root)
            export_manuscript(a)
            out = root / 'workbench/exports'
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            for title in ('Bad\x0bTitle', 'Bad\ud800Title', 'Bad\ufffeTitle'):
                (root / 'project.json').write_text(json.dumps({'title': title}), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Publication title'):
                    export_manuscript(a)
                self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_invalid_heading_and_filename_title(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = self.make_project(root, '# Bad\x00Title\nSynthetic')
            with self.assertRaises(ValueError):
                export_manuscript(a)
            (root / 'chapters/01.md').unlink()
            # XML-invalid characters can be legal filenames on the tested OS.
            try:
                (root / 'chapters/bad\ufffe.md').write_text('Synthetic body', encoding='utf-8')
            except OSError:
                self.skipTest('OS rejects XML-invalid filename')
            with self.assertRaises(ValueError):
                export_manuscript(a)

    def test_xml_legal_unicode_and_escaping_parse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            body = '# 合成章節\n繁中 & < > " \' 😀\t\n\r\u0085\ud7ff\ue000\ufffd\U00010000\U0010ffff'
            a = self.make_project(root, body, 'Synthetic & <Title> 😀')
            source_before = (root / 'chapters/01.md').read_bytes()
            report = export_manuscript(a)
            self.assertEqual(report['document_count'], 1)
            with zipfile.ZipFile(report['epub_path']) as zf:
                for name in zf.namelist():
                    if name.endswith(('.xhtml', '.opf', '.xml')):
                        ElementTree.fromstring(zf.read(name))
            self.assertEqual((root / 'chapters/01.md').read_bytes(), source_before)
