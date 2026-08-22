#!/usr/bin/env python3
import argparse,hashlib,json,os,re,subprocess,time,fcntl
from pathlib import Path
from scripts.etty_bounded_job import JobError,validate_manifest,acquire,execute
SHA=re.compile(r'^[0-9a-f]{40}$')
REQ={'schema_version','job_id','authorized','authorization_record','execution_commit','job_definition_path','job_definition_sha256','transfer_cap_bytes','allowed_source_hosts','allowed_destination_roots','resource_caps','handoff_allowlist'}
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def envelope(e):
 if not REQ.issubset(e): raise JobError('malformed envelope')
 if e['schema_version']!=1 or e['authorized'] is not True or not e['authorization_record'] or not SHA.fullmatch(e['execution_commit']): raise JobError('authorization/commit')
 if not isinstance(e['transfer_cap_bytes'],int) or e['transfer_cap_bytes']<=0: raise JobError('cap')
 for k in ('allowed_source_hosts','allowed_destination_roots','resource_caps','handoff_allowlist'):
  if not e[k]: raise JobError(k)
 if Path(e['job_definition_path']).is_absolute() or '..' in Path(e['job_definition_path']).parts: raise JobError('definition path')
def process(e,queue,jobrepo,state):
 envelope(e); jid=e['job_id']; st=Path(state); data=json.loads(st.read_text()) if st.exists() else {}
 if jid in data:
  if data[jid].get('execution_commit')!=e['execution_commit']: raise JobError('conflicting reused job')
  if data[jid].get('status')=='done': return 'ALREADY_COMPLETED'
 subprocess.run(['git','-C',str(queue),'fetch','origin','main'],check=True); subprocess.run(['git','-C',str(jobrepo),'fetch','origin',e['execution_commit']],check=True); subprocess.run(['git','-C',str(jobrepo),'cat-file','-e',e['execution_commit']+'^{commit}'],check=True); subprocess.run(['git','-C',str(jobrepo),'checkout','--detach',e['execution_commit']],check=True)
 d=(jobrepo/e['job_definition_path']).resolve(); root=jobrepo.resolve()
 if root not in d.parents or d.is_symlink(): raise JobError('definition escape')
 if digest(d)!=e['job_definition_sha256']: raise JobError('definition hash')
 job=json.loads(d.read_text()); job['allowed_hosts']=e['allowed_source_hosts']; job['transfer_cap_bytes']=e['transfer_cap_bytes']; validate_manifest(job)
 st.parent.mkdir(parents=True,exist_ok=True); jobstate=st.with_name(jid+'.json');
 if job.get('acquire'): acquire(job,jobstate)
 execute(job,jobstate); data[jid]={'status':'done','execution_commit':e['execution_commit']}; st.write_text(json.dumps(data,indent=2)+'\n'); return 'DONE'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--queue-repo',type=Path,required=True); p.add_argument('--job-repo',type=Path,required=True); p.add_argument('--queue-glob',default='automation/etty_jobs/*.json'); p.add_argument('--state',type=Path,required=True); p.add_argument('--once',action='store_true'); a=p.parse_args(); lock=a.state.with_suffix('.lock'); lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('w') as f:
  try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError: raise SystemExit('BUSY')
  while True:
   subprocess.run(['git','-C',str(a.queue_repo),'fetch','origin','main'],check=True)
   for q in sorted((a.queue_repo/a.queue_glob).parent.glob(Path(a.queue_glob).name)):
    try: print(q.name,process(json.loads(q.read_text()),a.queue_repo,a.job_repo,a.state),flush=True)
    except Exception as e: print(q.name,'SAFE_STOP',e,flush=True)
   if a.once:return
   time.sleep(180)
if __name__=='__main__':main()
