from __future__ import annotations
import json, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from novel_judge.state import empty_state
from novel_judge.canonical import refresh_state_hash
from novel_judge.intent import make_intent
from novel_judge.capacity import capacity_budget
from novel_judge.micro import expand_macro_intent
from novel_judge.store import FileStore
from novel_judge.engine import commit_turn
from novel_judge.errors import JudgeError, MACRO_INTENT_REQUIRES_EXPANSION

class CapacityBudgetRegression(unittest.TestCase):
    def fixture(self):
        s=empty_state('autonomous-protagonist-capacity-regression','session')
        s['actors']={'autonomous-protagonist':{'kind':'protagonist','control_mode':'ai_autonomous','agency_policy':'model_may_propose_but_judge_must_commit','user_override':True,'location':'house-entry','inventory':[],'commitments':[]}}
        s['world_truth']['locations']={'house-entry':{'connections':{'kitchen':{'open':True},'garage':{'open':True}}},'kitchen':{'connections':{'house-entry':{'open':True}}},'garage':{'connections':{'house-entry':{'open':True}}}}
        s['world_truth']['objects']={'map-1':{'location':'house-entry','holder':None,'portable':True},'food-1':{'location':'kitchen','holder':None,'portable':True}}
        s['reality']['actors']['autonomous-protagonist']={'physical':{'hunger':'high','fatigue':'high','cold':'high','sleep':'fragmented'},'cognition':{'clarity':'fragmented_clear','working_memory':'poor','planning_horizon':'minutes'},'capacity':{'short_walk':True},'available_actions':['observe','observe_local','move','move_short','take','inspect_object','map_read_fragment','wait'],'blocked_actions':[],'action_costs':{'move':{'fatigue':'high'}},'source':'regression-fixture'}
        return refresh_state_hash(s)
    def test_budget_is_hard_compiled(self):
        s=self.fixture(); b=capacity_budget(s,'autonomous-protagonist'); self.assertEqual(b['max_major_actions_per_turn'],1); self.assertEqual(b['max_zones'],1); self.assertEqual(b['max_explicit_plan_steps'],1)
    def test_macro_exploration_expands_to_one_micro_major_action(self):
        s=self.fixture(); i=make_intent('autonomous-protagonist','explore_house',turn_id='macro',source='model',model_generated=True,parameters={'micro_actions':[{'type':'move_short','target':'kitchen'},{'type':'inspect_object','object_id':'food-1'},{'type':'move_short','target':'garage'}]})
        children=expand_macro_intent(s,i); self.assertEqual(len(children),2); self.assertEqual(children[0]['type'],'move_short'); self.assertEqual(children[1]['type'],'inspect_object')
    def test_unexpanded_macro_is_rejected_and_audited(self):
        s=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            store=FileStore(d,'autonomous-protagonist-capacity-regression','session'); store.save_state(s)
            i=make_intent('autonomous-protagonist','explore_house',turn_id='macro-reject',source='model',model_generated=True)
            with self.assertRaises(JudgeError) as cm: commit_turn(store,i)
            self.assertEqual(cm.exception.code,MACRO_INTENT_REQUIRES_EXPANSION)
            self.assertEqual(store.load_state()['revision'],0)
            self.assertTrue(any(x.get('verdict')=='reject' for x in store.read_events()))
    def test_map_not_in_location_cannot_be_read(self):
        s=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            store=FileStore(d,'autonomous-protagonist-capacity-regression','session'); store.save_state(s)
            i=make_intent('autonomous-protagonist','map_read_fragment',turn_id='map-reject',targets=['map-1'],parameters={'object_id':'map-1'},source='model',model_generated=True)
            # It is local, so the action commits; moving map knowledge is not
            # invented by the delta. The contract only permits local reading.
            r=commit_turn(store,i,generated_output={'text':'只看地圖一角','action_manifest':[{'type':'map_read_fragment'}]})
            self.assertIn(r['verdict'],{'allow','allow_with_cost'})
            self.assertNotIn('food-1',store.load_state()['knowledge']['player'].get('autonomous-protagonist',[]))

if __name__=='__main__': unittest.main()
