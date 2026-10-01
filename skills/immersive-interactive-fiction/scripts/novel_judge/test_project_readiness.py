from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from .production import ProjectRuntimeAdapter
from .production_projections import refresh_production_projections
from .project_readiness import project_readiness_report
from .state import empty_state

class ProjectReadinessTests(unittest.TestCase):
 def adapter(self, root):
  a=ProjectRuntimeAdapter(root,'p','s');a.initialize(empty_state('p','s'),baseline_id='b',provenance={'shadow':True},migration_authorized=True);return a
 def test_fresh_disposable_surfaces_make_fixture_ready(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);refresh_production_projections(a);r=project_readiness_report(a)
   self.assertEqual(r['status'],'ready');self.assertTrue(r['ready_for_generation']);self.assertTrue(r['ready_for_commands'])
 def test_graph_and_workbench_staleness_are_separate_blockers(self):
  with tempfile.TemporaryDirectory() as td:
   a=self.adapter(td);refresh_production_projections(a)
   graph=Path(td)/'graphify-out/interactive/s-main.json';graph.write_text('{}')
   r=project_readiness_report(a);self.assertIn('STALE_GRAPH_PROJECTION',r['generation_blockers'])
   (Path(td)/'workbench/report.json').write_text('{}')
   r=project_readiness_report(a);self.assertIn('STALE_WORKBENCH',r['command_blockers'])
 def test_bootstrap_zero_events_allows_first_scene(self):
  with tempfile.TemporaryDirectory() as td:
   state=empty_state('p','s');state['actors']={'actor':{'kind':'npc','location':'room','status':{},'commitments':[]}}
   a=ProjectRuntimeAdapter(td,'p','s');a.initialize(state,baseline_id='b',provenance={'shadow':True},migration_authorized=True);refresh_production_projections(a)
   r=project_readiness_report(a)
   self.assertIn('BOOTSTRAP_FIRST_SCENE', r['warnings'])
   self.assertNotIn('UNEXPECTEDLY_EMPTY_OR_STALE_PRODUCTION_MEMORY', r['generation_blockers'])
   self.assertNotIn('STALE_OR_MISSING_CONTEXT_PACK', r['generation_blockers'])
 def test_active_project_empty_memory_and_context_fail_writing_readiness(self):
  with tempfile.TemporaryDirectory() as td:
   state=empty_state('p','s');state['revision']=3;state['actors']={'actor':{'kind':'npc','location':'room','status':{},'commitments':[]}}
   a=ProjectRuntimeAdapter(td,'p','s');a.initialize(state,baseline_id='b',provenance={'shadow':True},migration_authorized=True);refresh_production_projections(a)
   a.store.read_events=lambda **kw:[{'schema':'minis.world-event.v1','event_id':'e1','turn_id':'T1','verdict':'allow','operations':[],'transition_contract':'legacy-v1'}]
   r=project_readiness_report(a);self.assertIn('UNEXPECTEDLY_EMPTY_OR_STALE_PRODUCTION_MEMORY',r['generation_blockers']);self.assertIn('STALE_OR_MISSING_CONTEXT_PACK',r['generation_blockers'])
if __name__=='__main__':unittest.main()
