#!/usr/bin/env python3
"""Unattended ETYY queue agent. Jobs are reviewed envelopes, never shell strings."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from scripts.etty_bounded_job import JobError,validate_manifest,acquire,execute
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def process(env,repo,state):
 if not env.get('authorized') or not env.get('execution_commit'): raise JobError('unauthorized/missing commit')
 if not (repo/'.git').exists(): raise JobError('control checkout missing')
 subprocess.run(['git','-C',str(repo),'fetch','origin',env['execution_commit']],check=True)
 subprocess.run(['git','-C',str(repo),'checkout','--detach',env['execution_commit']],check=True)
 d=repo/env['job_definition_path']
 if sha(d)!=env['job_definition_sha256']: raise JobError('job definition hash mismatch')
 job=json.loads(d.read_text()); validate_manifest(job)
 s=Path(state); s.parent.mkdir(parents=True,exist_ok=True); old=json.loads(s.read_text()) if s.exists() else {}
 if old.get(env['job_id'],{}).get('status')=='done': return 'ALREADY_COMPLETED'
 if job.get('acquire'): acquire(job,s.with_name(env['job_id']+'.acquisition.json'))
 execute(job,s.with_name(env['job_id']+'.execution.json')); old[env['job_id']]={'status':'done','execution_commit':env['execution_commit']}; s.write_text(json.dumps(old,indent=2)+'\n'); return 'DONE'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--repo',type=Path,required=True); p.add_argument('--queue',type=Path,required=True); p.add_argument('--state',type=Path,required=True); p.add_argument('--once',action='store_true'); a=p.parse_args()
 while True:
  for q in sorted(a.queue.glob('*.json')):
   try: print(q.name,process(json.loads(q.read_text()),a.repo,a.state),flush=True)
   except Exception as e: print(q.name,'SAFE_STOP',e,flush=True)
  if a.once: return
  time.sleep(180)
if __name__=='__main__': main()
