#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ingest_public_visual as v

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
    b"\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


def fake_db(tmp: Path) -> Path:
    gdir = tmp / "graphify-out"
    gdir.mkdir(parents=True)
    graph = {
        "directed": True,
        "multigraph": True,
        "graph": {"schema": "minis.relationship-graph.v1", "title": "t"},
        "nodes": [
            {
                "id": "person:demo",
                "label": "Demo",
                "entity_type": "person",
                "properties": {"character_record": True, "subject_category": "real"},
                "status": "active",
                "confidence": "EXTRACTED",
            }
        ],
        "links": [],
        "hyperedges": [],
    }
    (gdir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    return tmp


class Ingest(unittest.TestCase):
    def test_add_file_dedupes_by_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = fake_db(Path(td) / "demo")
            img = Path(td) / "a.png"
            img.write_bytes(PNG)
            ns = type("NS", (), {})()
            ns.db = str(root)
            ns.person = "person:demo"
            ns.file = str(img)
            ns.url = None
            ns.source_url = "https://example.com/a.png"
            ns.page_url = "https://example.com/"
            ns.role = "official_avatar"
            ns.label = "avatar"
            ns.access_mode = "anonymous_public"
            ns.rights_note = "public_page"
            ns.write_graph = False
            rc = v.cmd_add(ns)
            self.assertEqual(rc, 0)
            visuals = list((root / "visuals").glob("*.png"))
            self.assertEqual(len(visuals), 1)
            digest = visuals[0].stem
            rec = json.loads((root / "visuals" / f"{digest}.json").read_text())
            self.assertEqual(rec["schema"], v.SCHEMA)
            self.assertEqual(rec["sha256"], digest)
            self.assertTrue(rec["local_path"].startswith("visuals/"))
            rc2 = v.cmd_add(ns)
            self.assertEqual(rc2, 0)
            self.assertEqual(len(list((root / "visuals").glob("*.png"))), 1)

    def test_write_graph_adds_resource_and_edge(self):
        with tempfile.TemporaryDirectory() as td:
            root = fake_db(Path(td) / "demo")
            img = Path(td) / "a.png"
            img.write_bytes(PNG)
            ns = type("NS", (), {})()
            ns.db = str(root)
            ns.person = "person:demo"
            ns.file = str(img)
            ns.url = None
            ns.source_url = "https://example.com/a.png"
            ns.page_url = None
            ns.role = "official_avatar"
            ns.label = None
            ns.access_mode = "anonymous_public"
            ns.rights_note = "public_page"
            ns.write_graph = True
            self.assertEqual(v.cmd_add(ns), 0)
            graph = json.loads((root / "graphify-out" / "graph.json").read_text())
            vis = [n for n in graph["nodes"] if str(n.get("id", "")).startswith("visual:")]
            self.assertEqual(len(vis), 1)
            person = next(n for n in graph["nodes"] if n["id"] == "person:demo")
            self.assertTrue(person["properties"]["visual_refs"])
            self.assertTrue(any(e.get("relation") == "has_visual" for e in graph["links"]))

    def test_rejects_non_image(self):
        with self.assertRaises(SystemExit):
            v.sniff_mime(b"not-an-image", None)

    def test_compare_without_vision_is_false(self):
        with tempfile.TemporaryDirectory() as td:
            root = fake_db(Path(td) / "demo")
            img = Path(td) / "a.png"
            img.write_bytes(PNG)
            ns = type("NS", (), {})()
            ns.db = str(root)
            ns.person = "person:demo"
            ns.file = str(img)
            ns.url = None
            ns.source_url = "https://example.com/a.png"
            ns.page_url = None
            ns.role = "comparison_still"
            ns.label = None
            ns.access_mode = "anonymous_public"
            ns.rights_note = "public_page"
            ns.write_graph = False
            v.cmd_add(ns)
            recs = v.list_visuals(root)
            ident = recs[0]["visual_id"]
            cmp_ns = type("NS", (), {})()
            cmp_ns.db = str(root)
            cmp_ns.id = [ident, ident]
            cmp_ns.threshold = 0.9
            with patch.object(v.shutil, "which", return_value=None):
                rc = v.cmd_compare(cmp_ns)
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
