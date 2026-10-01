import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import capability_probe
FIX=Path(__file__).parents[1]/'fixtures/capability-report.json'
def test_l5():
 r=capability_probe.load(FIX); x={**r,'probes':r['probes']}; out={**capability_probe.assess(x['probes'])}; assert out['level']=='L5' and out['passed']
def test_l1_degrades():
 out=capability_probe.assess({'text':{'passed':True}}); assert out['level']=='L1'; assert 'automatic_tool_calls' in out['disabled_features']
def test_empty_tool_arguments_fail():
 r={'choices':[{'message':{'tool_calls':[{'id':'x','function':{'name':'f','arguments':'{}'}}]}}]}; assert capability_probe.tool_probe(r)['passed'] is False
if __name__=='__main__': test_l5();test_l1_degrades();test_empty_tool_arguments_fail();print('capability-probe-tests: 3 passed')
