from __future__ import annotations
import tempfile,unittest,json
from pathlib import Path
from .author_workbench import build_workbench_report,create_command_request
from .author_workbench_html import render_workbench_html
from .production import ProjectRuntimeAdapter
from .production_projections import refresh_production_projections
from .state import empty_state
class AuthorWorkbenchTests(unittest.TestCase):
 def adapter(self,root):
  a=ProjectRuntimeAdapter(root,'p','s');a.initialize(empty_state('p','s'),baseline_id='b',provenance={'shadow':True},migration_authorized=True);return a
 def test_report_is_read_only_and_source_bound(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);before=a.store.load_state()['state_hash'];r=build_workbench_report(a);self.assertEqual(r['source']['state_hash'],before);self.assertEqual(a.store.load_state()['state_hash'],before);self.assertEqual(r['actions']['write_policy'],'no_direct_canonical_writes')
 def test_command_request_does_not_mutate_canon(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);refresh_production_projections(a);before=a.store.load_state()['state_hash'];r=create_command_request(a,kind='create_candidate',payload={'turn':'T1'},author_id='a',reason='test');self.assertEqual(a.store.load_state()['state_hash'],before);self.assertTrue((Path(td)/r['path']).is_file());self.assertEqual(r['status'],'pending')
 def test_stale_workbench_blocks_command_and_html_has_live_guard(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);refresh_production_projections(a);html=render_workbench_html(build_workbench_report(a));self.assertIn('runtime-head.json',html);self.assertIn('STALE',html)
   (Path(td)/'workbench/report.json').write_text(json.dumps({'source':{'state_hash':'stale'}}))
   with self.assertRaises(RuntimeError):create_command_request(a,kind='create_candidate',payload={},author_id='a',reason='stale')
 def test_unknown_command_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):create_command_request(self.adapter(td),kind='direct_write',payload={},author_id='a',reason='x')
 def test_resume_card_and_html_are_present(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);r=build_workbench_report(a)
   self.assertEqual(r['resume']['schema'],'minis.author-resume-card.v1')
   self.assertFalse(r['resume']['frozen'])
   self.assertFalse(r['resume']['canon_write'])
   html=render_workbench_html(r)
   self.assertIn('恢復卡',html)
   self.assertIn('id="resume"',html)
   self.assertEqual(r['scene_studio']['schema'],'minis.scene-studio.v1')
   self.assertEqual(r['scene_studio']['view'],'status')
   self.assertFalse(r['scene_studio']['canon_write'])
   self.assertIn('id="scene-studio"',html)
   self.assertIn('Scene Studio',html)
   self.assertIn('used sources',html)
 def test_frozen_project_disables_workbench_actions(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);refresh_production_projections(a)
   Path(td,'PROJECT-FROZEN.json').write_text(json.dumps({'status':'FROZEN','reason':'pause','resume_condition':'explicit resume'}))
   r=build_workbench_report(a)
   self.assertTrue(r['resume']['frozen'])
   self.assertFalse(r['actions']['enabled'])
   self.assertIn('PROJECT_FROZEN', r['readiness']['generation_blockers'])
   self.assertIn('PROJECT_FROZEN', r['readiness']['command_blockers'])
   self.assertTrue(r['scene_studio']['frozen'])
   self.assertFalse(r['scene_studio']['accept_enabled'])
   html=render_workbench_html(r)
   self.assertIn('凍結：只可預覽',html)
   self.assertIn('id="scene-studio"',html)
if __name__=='__main__':unittest.main()
