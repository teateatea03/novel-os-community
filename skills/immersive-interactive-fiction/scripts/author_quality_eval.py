#!/usr/bin/env python3
import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from novel_judge.author_quality_eval import build_project_fixtures,evaluate_fixture_dir,production_quality_telemetry
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--minimum',type=int,default=50);a=p.parse_args()
m=build_project_fixtures(a.root,a.output,minimum=a.minimum);r=evaluate_fixture_dir(a.output);r['production_telemetry']=production_quality_telemetry(a.root);path=pathlib.Path(a.output)/'baseline-report.json';path.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':m,'baseline':r},ensure_ascii=False,indent=2))
