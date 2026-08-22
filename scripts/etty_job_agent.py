#!/usr/bin/env python3
import argparse,hashlib,json,os,re,subprocess,time,fcntl
from pathlib import Path
from scripts.etty_bounded_job import JobError,acquire,atomic,execute,validate_manifest
SHA=re.compile(r'^[0-9a-f]{40}$')
REQ={'schema_version','job_id','authorized','authorization_record','execution_commit','job_definition_path','job_definition_sha256','transfer_cap_bytes','allowed_source_hosts','allowed_destination_roots','resource_caps','handoff_allowlist'}
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _bounded_job(job, e):
 resource=e['resource_caps']; hosts=job.get('allowed_hosts',job.get('allowed_source_hosts',[])); roots=job.get('allowed_destination_roots',[])
 if not set(hosts).issubset(e['allowed_source_hosts']): raise JobError('source host scope expansion')
 if not set(roots).issubset(e['allowed_destination_roots']): raise JobError('destination scope expansion')
 if job.get('transfer_cap_bytes',0)>e['transfer_cap_bytes']: raise JobError('transfer cap expansion')
 for key in ('allowed_executables','allowed_working_roots','allowed_environment_keys'):
  requested=job.get(key,[]); allowed=resource.get(key,[])
  if not set(requested).issubset(allowed): raise JobError(key+' scope expansion')
 for key in ('executable_path','version_command','version_expected'):
  if key in job and job[key]!=resource.get(key): raise JobError(key+' scope expansion')
 if job.get('wall_seconds',0)>resource.get('wall_seconds',0): raise JobError('wall-time expansion')
 effective=dict(job); effective['allowed_hosts']=hosts; effective['allowed_destination_roots']=roots; effective['transfer_cap_bytes']=job['transfer_cap_bytes']
 for key in ('allowed_executables','executable_path','version_command','version_expected','allowed_working_roots','allowed_environment_keys','wall_seconds'):
  if key in resource: effective[key]=resource[key]
 return effective
def envelope(e):
 if not REQ.issubset(e): raise JobError('malformed envelope')
 if e['schema_version']!=1 or e['authorized'] is not True or not e['authorization_record'] or not SHA.fullmatch(e['execution_commit']): raise JobError('authorization/commit')
 if not isinstance(e['transfer_cap_bytes'],int) or e['transfer_cap_bytes']<=0: raise JobError('cap')
 for k in ('allowed_source_hosts','allowed_destination_roots','resource_caps','handoff_allowlist'):
  if not e[k]: raise JobError(k)
 if Path(e['job_definition_path']).is_absolute() or '..' in Path(e['job_definition_path']).parts: raise JobError('definition path')
def queue_entries(repo):
 names=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only','origin/main','automation/etty_jobs'],text=True).splitlines()
 return [name for name in names if Path(name).parent==Path('automation/etty_jobs') and Path(name).suffix=='.json']
def failure_payload(job_id, job, acquisition_state, phase, exc):
 acquisition_data=json.loads(Path(acquisition_state).read_text()) if Path(acquisition_state).exists() else {'items':{},'network_bytes':0}
 item_states=acquisition_data.get('items',{}); failed_ids=sorted(item_id for item_id,item_state in item_states.items() if item_state.get('status') in {'retry_pending','transient_failed'})
 completed=sum(item_state.get('status') in {'done','reused'} for item_state in item_states.values())
 return {'job_id':job_id,'status':'SAFE_STOP','phase':phase,'completed_items':completed,'total_items':len(job.get('items',[])),'failed_items':len(failed_ids),'failed_item_ids':failed_ids[:200],'network_bytes':acquisition_data.get('network_bytes',0),'error':' '.join(str(exc).split())[:500]}
def handoff(e,repo,state):
 h=e.get('handoff_allowlist',[]); out=Path(state).parent/(e['job_id']+'-handoff'); out.mkdir(parents=True,exist_ok=True)
 if any(Path(x).name!=x or Path(x).suffix not in {'.json','.md','.txt'} for x in h): raise JobError('handoff allowlist')
 remote=subprocess.check_output(['git','-C',str(repo),'remote','get-url','origin'],text=True).strip();
 if os.getenv('ETTY_SYNTHETIC_HANDOFF')!='1' and remote!='git@github.com:linrenzhang98-afk/0714.git': raise JobError('handoff remote')
 subprocess.run(['git','-C',str(repo),'fetch','origin','etty-handoff'],check=True)
 if subprocess.run(['git','-C',str(repo),'rev-parse','origin/etty-handoff'],capture_output=True).returncode: raise JobError('missing etty-handoff')
 subprocess.run(['git','-C',str(repo),'checkout','-B','etty-handoff','origin/etty-handoff'],check=True)
 subprocess.run(['git','-C',str(repo),'merge','--ff-only','origin/etty-handoff'],check=True)
 dest=repo/'handoffs'/e['job_id']; existed=dest.exists()
 for name in h:
  src=out/name
  if not src.is_file() or src.stat().st_size>5*1024*1024: raise JobError('handoff file')
 if existed:
  if not all((dest/name).is_file() for name in h): raise JobError('partial handoff')
  if all((dest/name).read_bytes()==(out/name).read_bytes() for name in h): return 'ALREADY_PUBLISHED'
  raise JobError('conflicting handoff')
 dest.mkdir(parents=True,exist_ok=True)
 for name in h:
  (dest/name).write_bytes((out/name).read_bytes())
 subprocess.run(['git','-C',str(repo),'add','--']+['handoffs/'+e['job_id']+'/'+x for x in h],check=True)
 subprocess.run(['git','-C',str(repo),'config','user.name','ETYY Job Agent'],check=True); subprocess.run(['git','-C',str(repo),'config','user.email','etty-job-agent@localhost'],check=True)
 subprocess.run(['git','-C',str(repo),'commit','-m','Handoff '+e['job_id']],check=True)
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
 job=_bounded_job(json.loads(d.read_text()),e); validate_manifest(job)
 st.parent.mkdir(parents=True,exist_ok=True); acquisition_state=st.with_name(jid+'.acquisition.json'); execution_state=st.with_name(jid+'.execution.json')
 phase='acquisition' if job.get('acquire') else 'execution'
 try:
  if job.get('acquire'): acquire(job,acquisition_state)
  phase='execution'; execute(job,execution_state)
 except JobError as exc:
  payload=failure_payload(jid,job,acquisition_state,phase,exc)
  hout=Path(state).parent/(jid+'-handoff'); hout.mkdir(parents=True,exist_ok=True); (hout/'result.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
  data[jid]={'status':'safe_stop','execution_commit':e['execution_commit'],'envelope_sha256':hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest(),'phase':phase,'error':payload['error']}; atomic(st,data)
  if 'result.json' in e.get('handoff_allowlist',[]):
   failure_envelope={**e,'handoff_allowlist':['result.json']}; handoff(failure_envelope,handoffrepo,state)
  raise
 hout=Path(state).parent/(jid+'-handoff'); hout.mkdir(parents=True,exist_ok=True); (hout/'result.json').write_text(json.dumps({'job_id':jid,'status':'done'})); handoff(e,handoffrepo,state); data[jid]={'status':'done','execution_commit':e['execution_commit'],'envelope_sha256':hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()}; atomic(st,data); return 'DONE'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--queue-repo',type=Path,required=True); p.add_argument('--job-repo',type=Path,required=True); p.add_argument('--handoff-repo',type=Path,required=True); p.add_argument('--queue-glob',default='automation/etty_jobs/*.json'); p.add_argument('--state',type=Path,required=True); p.add_argument('--once',action='store_true'); a=p.parse_args(); lock=a.state.with_suffix('.lock'); lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('w') as f:
  try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError: raise SystemExit('BUSY')
  while True:
   subprocess.run(['git','-C',str(a.queue_repo),'fetch','origin','main'],check=True)
   for n in queue_entries(a.queue_repo):
    try:
     raw=subprocess.check_output(['git','-C',str(a.queue_repo),'show','origin/main:'+n],text=True)
     print(Path(n).name,process(json.loads(raw),a.queue_repo,a.job_repo,a.handoff_repo,a.state),flush=True)
    except Exception as e: print(Path(n).name,'SAFE_STOP',e,flush=True)
   if a.once:return
   time.sleep(180)
if __name__=='__main__':main()
