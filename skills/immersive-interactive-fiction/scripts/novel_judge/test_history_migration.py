from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from .canonical import refresh_state_hash
from .history_migration import make_migration_event, migration_replay, install_reconstructed_history, migration_event_semantic_operations
from .production import ProjectRuntimeAdapter
from .state import empty_state

class HistoryMigrationTests(unittest.TestCase):
    def states(self):
        a=empty_state('p','s');a['canon_scope']='canon';a['actors']={'x':{'location':'a'}};refresh_state_hash(a)
        b=json.loads(json.dumps(a));b['actors']['x']['location']='b';b['revision']=1;b['last_turn_id']='T1';b['events_head']='legacy-1';refresh_state_hash(b)
        return a,b
    def test_checkpoint_event_replays_exactly(self):
        a,b=self.states();e=make_migration_event(sequence=1,turn_id='T1',source_state=a,target_state=b,provenance_status='RECONSTRUCTED_CHECKPOINT',source_paths=['x'],source_hashes={'x':'0'*64})
        self.assertEqual(migration_replay(a,[e])['state_hash'],b['state_hash'])
        self.assertTrue(any(x['path']=='/actors/x/location' for x in migration_event_semantic_operations(e)))
    def test_install_builds_integrity_index_and_conformance(self):
        a,b=self.states();e=make_migration_event(sequence=1,turn_id='T1',source_state=a,target_state=b,provenance_status='ORIGINAL',source_paths=['x'],source_hashes={'x':'0'*64})
        with tempfile.TemporaryDirectory() as root:
            adapter=ProjectRuntimeAdapter(root,'p','s')
            r=install_reconstructed_history(adapter,baseline_id='base',baseline_state=a,events=[e],frozen_state=b,frozen_scene_sha256='1'*64,frozen_turn='T1',migration_manifest={'provenance_records':[]})
            self.assertEqual(r['integrity']['status'],'pass');self.assertEqual(adapter.assert_conformant()['status'],'pass')
            self.assertEqual(len(adapter.store.read_events()),1)
    def test_migration_marker_rejected_by_normal_commit_delta(self):
        from .delta import validate_operation
        with self.assertRaises(Exception):validate_operation({'op':'replace_snapshot','path':'/','value':{}},source='author')
if __name__=='__main__':unittest.main()
