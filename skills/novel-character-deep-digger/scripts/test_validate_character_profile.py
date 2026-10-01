#!/usr/bin/env python3
import json, subprocess, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).with_name("validate_character_profile.py")

def base(depth="L0"):
    return {"subject_category":"other","character_importance":"minor_functional","work_stage":"discovery","profile_depth":depth,"model_status":"MODEL_DRAFT","story_questions":["此人如何妨礙主角？"],"identity_scope":"original","current_goal":"守住門口","visible_obstacle":"主角要求進入","agency":"可拒絕或通報","behavior_anchors":[{"trigger":"無證件","action":"攔阻","cost":"衝突"}]}

def run(d):
    with tempfile.NamedTemporaryFile("w",suffix=".json",delete=False,encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False); name=f.name
    r=subprocess.run(["python3",str(SCRIPT),name],capture_output=True,text=True)
    Path(name).unlink(); return r.returncode,json.loads(r.stdout)

class TestProfile(unittest.TestCase):
    def test_l0_draft_passes_with_warning(self):
        code,out=run(base()); self.assertEqual(code,0); self.assertTrue(out["warnings"])
    def test_l1_without_test_fails(self):
        d=base("L1"); d.update({"strategy_cost":"先查證但拖慢","relationship_variation":"對長官服從","voice_cues":["短句"],"conditional_reactions":[1,2],"capabilities_limits":"可通報，無搜查權"})
        code,out=run(d); self.assertEqual(code,1); self.assertIn("gate:L1_requires_validation_test",out["errors"])
    def test_l2_complete_passes(self):
        d=base("L2"); d.update({"character_importance":"lead","model_status":"SCENE_TESTED","strategy_cost":"控制換安全但失去信任","relationship_variation":"親密時迴避、權威前順從","voice_cues":["先問程序再答情緒"],"conditional_reactions":[1,2],"capabilities_limits":"可規劃，不可全知","competing_models":[{"id":"A"},{"id":"B"}],"state_distribution":"baseline/stress/recovery","formation_history":"事件到策略","arc_candidates":["正向","平弧"],"relationship_map":["mentor"],"source_families":[{"source_family_id":"sf1","original_source_url":"canon:ch1"}],"validation_tests":[{"type":"counterexample"},{"type":"contrast_scene"},{"type":"interchangeability"}]})
        code,out=run(d); self.assertEqual(code,0,out)
    def test_duplicate_source_family_fails(self):
        d=base("L2"); d.update({"character_importance":"lead","model_status":"SCENE_TESTED","strategy_cost":"x","relationship_variation":"x","voice_cues":["x"],"conditional_reactions":[1,2],"capabilities_limits":"x","competing_models":[1,2],"state_distribution":"x","formation_history":"x","arc_candidates":["x"],"relationship_map":["x"],"source_families":[{"source_family_id":"a","original_source_url":"u"},{"source_family_id":"b","original_source_url":"u"}],"validation_tests":[{"type":"counterexample"},{"type":"voice_blind"},{"type":"interchangeability"}]})
        code,out=run(d); self.assertEqual(code,1); self.assertTrue(any("duplicate_original" in x for x in out["errors"]))
if __name__=="__main__": unittest.main()
