#!/usr/bin/env python3
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from novel_judge.author_resume import load_project_adapter
from novel_judge.author_workbench import build_workbench_report, create_command_request
from novel_judge.command_executor import claim_author_command, execute_author_command, recover_author_commands, author_command_health
from novel_judge.author_workbench_html import render_workbench_html
p = argparse.ArgumentParser()
p.add_argument('--root', required=True)
sub = p.add_subparsers(dest='cmd', required=True)
b = sub.add_parser('build')
b.add_argument('--output', required=True)
b.add_argument('--json-output')
c = sub.add_parser('request')
c.add_argument('--kind', required=True)
c.add_argument('--payload', default='{}')
c.add_argument('--author-id', required=True)
c.add_argument('--reason', required=True)
cl = sub.add_parser('claim')
cl.add_argument('--command-id', required=True)
cl.add_argument('--worker-id', required=True)
cl.add_argument('--lease-seconds', type=int, default=120)
e = sub.add_parser('execute')
e.add_argument('--command-id', required=True)
e.add_argument('--worker-id', required=True)
e.add_argument('--lease-token', required=True)
sub.add_parser('recover')
sub.add_parser('command-health')
a = p.parse_args()
rt = load_project_adapter(a.root)
if a.cmd == 'build':
    r = build_workbench_report(rt)
    path = pathlib.Path(a.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_workbench_html(r))
    if a.json_output:
        pathlib.Path(a.json_output).write_text(json.dumps(r, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    out = {'status': r['health']['status'], 'output': str(path), 'report_hash': r['report_hash'], 'event_count': r['source']['event_count'], 'frozen': bool((r.get('resume') or {}).get('frozen'))}
elif a.cmd == 'request':
    out = create_command_request(rt, kind=a.kind, payload=json.loads(a.payload), author_id=a.author_id, reason=a.reason)
elif a.cmd == 'claim':
    out = claim_author_command(rt.store, a.command_id, worker_id=a.worker_id, lease_seconds=a.lease_seconds)
elif a.cmd == 'execute':
    out = execute_author_command(rt, a.command_id, worker_id=a.worker_id, lease_token=a.lease_token)
elif a.cmd == 'recover':
    out = recover_author_commands(rt.store)
else:
    out = author_command_health(rt.store)
print(json.dumps(out, ensure_ascii=False, indent=2))
