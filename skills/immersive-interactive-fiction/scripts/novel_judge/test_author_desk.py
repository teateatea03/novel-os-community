from __future__ import annotations
import json, tempfile, unittest, zipfile
from pathlib import Path
from .author_resume import build_resume_card, load_project_adapter
from .manuscript_export import export_manuscript
from .production import ProjectRuntimeAdapter
from .production_projections import refresh_production_projections
from .scene_studio import list_scenes, inspect_scene_file, save_scene_draft, diff_scene_draft, accept_scene_draft, write_workbench_projection, studio_status
from .state import empty_state

class AuthorDeskTests(unittest.TestCase):
    def adapter(self, root, *, frozen=False):
        a = ProjectRuntimeAdapter(root, "desk", "s")
        a.initialize(empty_state("desk", "s"), baseline_id="b", provenance={"shadow": True}, migration_authorized=True)
        Path(root, "project.json").write_text(json.dumps({
            "project_id": "desk", "title": "Desk",
            "interactive_runtime": {"session_id": "s", "branch": "main"},
        }))
        (Path(root) / "interactive" / "scenes").mkdir(parents=True, exist_ok=True)
        (Path(root) / "interactive" / "scenes" / "T0001.md").write_text("# 第一場\n她想要開門，可是門被卡住。於是她只好停住。\n")
        if frozen:
            Path(root, "PROJECT-FROZEN.json").write_text(json.dumps({
                "status": "FROZEN", "reason": "pause",
                "resume_condition": "explicit resume",
                "freeze_scope": {"canonical_head": "T0001"},
            }))
        return a

    def test_resume_card_reports_freeze_without_writing_canon(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td, frozen=True)
            before = a.store.load_state()["state_hash"]
            card = build_resume_card(a)
            self.assertTrue(card["frozen"])
            self.assertFalse(card["canon_write"])
            self.assertIn("凍結", card["next_action"])
            self.assertEqual(a.store.load_state()["state_hash"], before)

    def test_load_project_adapter_uses_project_json(self):
        with tempfile.TemporaryDirectory() as td:
            self.adapter(td)
            loaded = load_project_adapter(td)
            self.assertEqual(loaded.project_id, "desk")
            self.assertEqual(loaded.session_id, "s")

    def test_load_project_adapter_prefers_live_runtime_namespace(self):
        with tempfile.TemporaryDirectory() as td:
            from .longform import initialize_longform_production
            initialize_longform_production(td, "desk")
            Path(td, "project.json").write_text(json.dumps({
                "project_id": "desk",
                "interactive_runtime": {"session_id": "manuscript", "branch": "main", "namespace": "runtime"},
            }))
            loaded = load_project_adapter(td)
            self.assertEqual(loaded.namespace, "runtime")
            self.assertEqual(loaded.session_id, "manuscript")
            self.assertTrue((Path(td) / "runtime" / "sessions" / "manuscript" / "branches" / "main" / "state" / "current.json").is_file())

    def test_scene_studio_lists_and_inspects_without_commit(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td)
            listed = list_scenes(a)
            self.assertGreaterEqual(listed["count"], 1)
            inspected = inspect_scene_file(a, relative_path="interactive/scenes/T0001.md")
            self.assertEqual(inspected["scene_goals"]["status"] in {"PASS", "WARN", "FAIL"}, True)
            self.assertIn("narrative_qa", inspected)
            self.assertIn("scene_review", inspected)
            self.assertTrue(inspected["claims"]["machine_prescan_only"])
            self.assertFalse(inspected["claims"]["is_beta_reader"])
            self.assertFalse(inspected["blocks_commit"])

    def test_draft_diff_accept_does_not_rewrite_canon_scene(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td)
            refresh_production_projections(a)
            original = (Path(td) / "interactive" / "scenes" / "T0001.md").read_text()
            before = a.store.load_state()["state_hash"]
            drafted = save_scene_draft(a, relative_path="interactive/scenes/T0001.md",
                                       text=original + "她又試了一次門把。\n", actor_id="alice", note="retry")
            self.assertEqual(drafted["status"], "saved")
            self.assertTrue(drafted["changed"])
            self.assertIn("她又試了一次門把", drafted["diff"])
            self.assertFalse(drafted["canon_write"])
            self.assertEqual((Path(td) / "interactive" / "scenes" / "T0001.md").read_text(), original)
            diffed = diff_scene_draft(a, draft_id=drafted["draft_id"])
            self.assertFalse(diffed["stale_base"])
            accepted = accept_scene_draft(a, draft_id=drafted["draft_id"], author_id="author")
            self.assertIn(accepted["status"], {"accepted_sidecar", "accepted_pending_gates"})
            self.assertFalse(accepted["canon_write"])
            accepted_file = Path(td) / accepted["accepted_path"]
            self.assertTrue(accepted_file.is_file())
            self.assertEqual((Path(td) / "interactive" / "scenes" / "T0001.md").read_text(), original)
            self.assertEqual(a.store.load_state()["state_hash"], before)

    def test_frozen_project_blocks_draft_and_accept(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td, frozen=True)
            drafted = save_scene_draft(a, relative_path="interactive/scenes/T0001.md", text="x")
            self.assertEqual(drafted["status"], "blocked")
            self.assertEqual(drafted["reason"], "PROJECT_FROZEN")
            accepted = accept_scene_draft(a, draft_id="T0001")
            self.assertEqual(accepted["status"], "blocked")
            self.assertEqual(accepted["reason"], "PROJECT_FROZEN")

    def test_manuscript_export_writes_copy_only(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td)
            report = export_manuscript(a)
            md = Path(report["markdown_path"])
            epub = Path(report["epub_path"])
            self.assertTrue(md.is_file())
            self.assertTrue(epub.is_file())
            self.assertIn("第一場", md.read_text(encoding="utf-8"))
            self.assertTrue(zipfile.is_zipfile(epub))
            self.assertFalse(report["canon_write"])
            self.assertTrue((Path(td) / "interactive" / "scenes" / "T0001.md").is_file())

    def test_workbench_refresh_writes_projection_only(self):
        with tempfile.TemporaryDirectory() as td:
            a = self.adapter(td, frozen=True)
            before = a.store.load_state()["state_hash"]
            original = (Path(td) / "interactive" / "scenes" / "T0001.md").read_text()
            status = studio_status(a)
            self.assertTrue(status["frozen"])
            self.assertFalse(status["accept_enabled"])
            self.assertFalse(status["canon_write"])
            out = write_workbench_projection(a)
            self.assertFalse(out["canon_write"])
            self.assertTrue(out["frozen"])
            html = (Path(td) / "workbench" / "index.html").read_text(encoding="utf-8")
            self.assertIn("恢復卡", html)
            self.assertIn("Scene Studio", html)
            self.assertIn("凍結：只可預覽", html)
            self.assertEqual(a.store.load_state()["state_hash"], before)
            self.assertEqual((Path(td) / "interactive" / "scenes" / "T0001.md").read_text(), original)
if __name__ == "__main__":
    unittest.main()
