#!/usr/bin/env python3
"""Single official Novel OS verification entry point."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;EXPORTER=HERE.parent;DEFAULT_BUNDLE=Path(os.environ.get('NOVEL_OS_BUNDLE_ROOT', str(EXPORTER))).resolve()

def resolve_skills(bundle: Path) -> Path:
    return bundle/'skills' if (bundle/'skills').is_dir() else (EXPORTER/'payload'/'skills' if (EXPORTER/'payload'/'skills').is_dir() else EXPORTER.parent)


def run(name,cmd,*,cwd=None,timeout=900):
 t=time.time();env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1';
 if cwd is not None: env['PYTHONPATH']=str(Path(cwd).resolve())
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=timeout,env=env);return {'name':name,'ok':p.returncode==0,'returncode':p.returncode,'seconds':round(time.time()-t,3),'stdout_tail':p.stdout[-4000:],'stderr_tail':p.stderr[-4000:]}
def main():
 a=argparse.ArgumentParser();a.add_argument('--profile',choices=['fast','full'],default='full');a.add_argument('--bundle-root');a.add_argument('--output');x=a.parse_args();rows=[]
 bundle=Path(x.bundle_root).resolve() if x.bundle_root else DEFAULT_BUNDLE
 skills=resolve_skills(bundle)
 interactive=skills/'immersive-interactive-fiction'/'scripts';long=skills/'long-form-novel-writer';reality=skills/'novel-reality-state-engine';cap=skills/'novel-model-capability-compatibility'
 rows.append(run('compileall',[sys.executable,'-m','compileall','-q',str(skills)]))
 rows.append(run('novel_judge',[sys.executable,'-m','unittest','discover','-s','novel_judge','-t','.','-p','test_*.py'],cwd=interactive))
 rows.append(run('behavior_calibration',[sys.executable,'-m','unittest','discover','-s',str(skills/'human-behavior-personality-consultant'/'scripts'),'-p','test_*.py']))
 rows.append(run('longform_behavior_integration',[sys.executable,'-m','unittest','discover','-s',str(long/'scripts'),'-p','test_behavior_integration.py']))
 rows.append(run('longform_regression',[sys.executable,str(long/'scripts/run_regression.py')]))
 rows.append(run('reality_regression',[sys.executable,str(reality/'tests/test_reality_state.py')]))
 rows.append(run('capability_regression',[sys.executable,str(cap/'tests/test_capability_probe.py')]))
 if x.profile=='full':
  with tempfile.TemporaryDirectory(prefix='novel-os-verify-') as td:
   evidence=Path(td)/'pilot.json';rows.append(run('phase_c_generalization',[sys.executable,str(long/'scripts/run_phase_c_pilot.py'),'--output',str(evidence)],timeout=1200))
 root=bundle
 rows.append(run('bundle_verify',[sys.executable,str(EXPORTER/'scripts/build_novel_os_bundle.py'),'verify','--bundle-root',str(root)]))
 report={'schema':'minis.novel-os-verification.v1','profile':x.profile,'status':'pass' if all(r['ok'] for r in rows) else 'fail','checks':rows}
 text=json.dumps(report,ensure_ascii=False,indent=2)+'\n';Path(x.output).write_text(text) if x.output else None;print(text);return 0 if report['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
