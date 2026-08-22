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
def handoff(e,repo,state):
 h=e.get('handoff_allowlist',[]); out=Path(state).parent/(e['job_id']+'-handoff'); out.mkdir(parents=True,exist_ok=True)
 if any(Path(x).name!=x or Path(x).suffix not in {'.json','.md','.txt'} for x in h): raise JobError('handoff allowlist')
 remote=subprocess.check_output(['git','-C',str(repo),'remote','get-url','origin'],text=True).strip();
 if os.getenv('ETTY_SYNTHETIC_HANDOFF')!='1' and remote not in ('etty-handoff', 'file://etty-handoff') and 'github.com' not in remote: raise JobError('handoff remote')
 dest=repo/'handoffs'/e['job_id']; dest.mkdir(parents=True,exist_ok=True)
 for name in h:
  src=out/name
  if not src.is_file() or src.stat().st_size>5*1024*1024: raise JobError('handoff file')
  (dest/name).write_bytes(src.read_bytes())
 subprocess.run(['git','-C',str(repo),'add','--']+['handoffs/'+e['job_id']+'/'+x for x in h],check=True)
 subprocess.run(['git','-C',str(repo),'config','user.name','ETYY Job Agent'],check=True); subprocess.run(['git','-C',str(repo),'config','user.email','etty-job-agent@localhost'],check=True)
 subprocess.run(['git','-C',str(repo),'commit','-m','Handoff '+e['job_id']],check=False)
 subprocess.run(['git','-C',str(repo),'push','origin','HEAD:etty-handoff'],check=True); return 'PUBLISHED'
def process(e,queue,jobrepo,handoffrepo,state):
 envelope(e); jid=e['job_id']; st=Path(state); data=json.loads(st.read_text()) if st.exists() else {}
 if jid in data:
  if data[jid].get('envelope_sha256')!=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest(): raise JobError('conflicting reused job')
  if data[jid].get('status')=='done': return 'ALREADY_COMPLETED'
 subprocess.run(['git','-C',str(queue),'fetch','origin','main'],check=True); subprocess.run(['git','-C',str(jobrepo),'fetch','origin',e['execution_commit']],check=True); subprocess.run(['git','-C',str(jobrepo),'cat-file','-e',e['execution_commit']+'^{commit}'],check=True); subprocess.run(['git','-C',str(jobrepo),'checkout','--detach',e['execution_commit']],check=True)
 d=(jobrepo/e['job_definition_path']).resolve(); root=jobrepo.resolve()
 if root not in d.parents or d.is_symlink(): raise JobError('definition escape')
 if digest(d)!=e['job_definition_sha256']: raise JobError('definition hash')
 job=json.loads(d.read_text()); job['allowed_hosts']=e['allowed_source_hosts']; job['transfer_cap_bytes']=e['transfer_cap_bytes']; validate_manifest(job)
 st.parent.mkdir(parents=True,exist_ok=True); jobstate=st.with_name(jid+'.json');
 if job.get('acquire'): acquire(job,jobstate)
 execute(job,jobstate); hout=Path(state).parent/(jid+'-handoff'); hout.mkdir(parents=True,exist_ok=True); (hout/'result.json').write_text(json.dumps({'job_id':jid,'status':'done'})); handoff(e,handoffrepo,state); data[jid]={'status':'done','execution_commit':e['execution_commit'],'envelope_sha256':hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()}; st.write_text(json.dumps(data,indent=2)+'\n'); return 'DONE'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--queue-repo',type=Path,required=True); p.add_argument('--job-repo',type=Path,required=True); p.add_argument('--handoff-repo',type=Path,required=True); p.add_argument('--queue-glob',default='automation/etty_jobs/*.json'); p.add_argument('--state',type=Path,required=True); p.add_argument('--once',action='store_true'); a=p.parse_args(); lock=a.state.with_suffix('.lock'); lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('w') as f:
  try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError: raise SystemExit('BUSY')
  while True:
   subprocess.run(['git','-C',str(a.queue_repo),'fetch','origin','main'],check=True)
   names=subprocess.check_output(['git','-C',str(a.queue_repo),'ls-tree','-r','--name-only','origin/main','automation/etty_jobs'],text=True).splitlines()
   for n in names:
    try:
     raw=subprocess.check_output(['git','-C',str(a.queue_repo),'show','origin/main:'+n],text=True)
     print(Path(n).name,process(json.loads(raw),a.queue_repo,a.job_repo,a.handoff_repo,a.state),flush=True)
    except Exception as e: print(Path(n).name,'SAFE_STOP',e,flush=True)
   if a.once:return
   time.sleep(180)
if __name__=='__main__':main()
