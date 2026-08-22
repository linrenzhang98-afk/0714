"""Generic bounded acquisition/execution primitives."""
import hashlib,json,os,subprocess,time,urllib.parse,urllib.request
from pathlib import Path
class JobError(Exception): pass
def atomic(path,data):
 tmp=Path(str(path)+'.tmp'); tmp.write_text(json.dumps(data,indent=2)+'\n');
 with tmp.open('r+') as f: f.flush(); os.fsync(f.fileno())
 tmp.replace(path)
def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def confined(p,roots):
 q=Path(p); 
 if not q.is_absolute(): raise JobError('destination must be absolute')
 for r in roots:
  base=Path(r).resolve(); parent=q.parent.resolve()
  if parent==base or base in parent.parents: return q
 raise JobError('destination escape')
def validate_manifest(m):
 items=m.get('items',[]); cap=int(m.get('transfer_cap_bytes',0)); roots=m.get('allowed_destination_roots',[]); hosts=m.get('allowed_hosts',m.get('allowed_source_hosts',[]))
 if not m.get('authorized',True) or not items or not roots: raise JobError('manifest authorization')
 seen=set(); dests=set(); total=0
 for x in items:
  if x['id'] in seen: raise JobError('duplicate item')
  seen.add(x['id']); u=urllib.parse.urlparse(x.get('url',''))
  if u.scheme!='https' or u.hostname not in hosts: raise JobError('URL host')
  confined(x['destination'],roots)
  if str(Path(x['destination']).resolve()) in dests: raise JobError('duplicate destination')
  dests.add(str(Path(x['destination']).resolve()))
  if int(x.get('expected_bytes',0))<=0: raise JobError('expected bytes')
  total+=int(x['expected_bytes'])
 if total>cap: raise JobError('transfer cap')
 return items
def acquire(m,state_path):
 items=validate_manifest(m); state=json.loads(state_path.read_text()) if Path(state_path).exists() else {'network_bytes':0,'items':{}}
 for x in items:
  d=Path(x['destination']);
  if d.exists():
   if d.stat().st_size!=x['expected_bytes'] or (x.get('sha256') and sha256(d)!=x['sha256']): raise JobError('conflicting existing file')
   state['items'][x['id']]={'status':'reused','sha256':sha256(d),'actual_bytes':d.stat().st_size}; atomic(state_path,state); continue
  confined(d,m['allowed_destination_roots']); d.parent.mkdir(parents=True,exist_ok=True); part=Path(str(d)+'.part'); attempts=0
  while attempts<2:
   attempts+=1
   try:
    req=urllib.request.Request(x['url'])
    with urllib.request.urlopen(req,timeout=30) as r:
     if urllib.parse.urlparse(r.geturl()).hostname not in m.get('allowed_hosts',[]): raise JobError('redirect host')
     n=0; h=hashlib.sha256()
     with part.open('wb') as f:
      for b in iter(lambda:r.read(1024*1024),b''):
       if state['network_bytes']+n+len(b)>m['transfer_cap_bytes']: atomic(state_path,state); raise JobError('transfer cap')
       f.write(b); n+=len(b); h.update(b); state['network_bytes']+=len(b); state['items'][x['id']]={'status':'downloading','attempts':attempts,'network_bytes':n}; atomic(state_path,state)
     if n!=x['expected_bytes'] or (x.get('sha256') and h.hexdigest()!=x['sha256']): raise JobError('byte/checksum mismatch')
    part.replace(d); state['items'][x['id']]={'status':'done','actual_bytes':n,'sha256':h.hexdigest(),'attempts':attempts}; atomic(state_path,state); break
   except JobError: raise
   except Exception:
    if attempts>=2: raise JobError('download failed')
def execute(m,state_path):
 st=json.loads(state_path.read_text()) if Path(state_path).exists() else {'items':{}}
 for x in validate_manifest(m):
  cmd=x.get('command');
  if not isinstance(cmd,list) or not cmd: raise JobError('argv')
  exe=Path(cmd[0]); allowed=m.get('allowed_executables',[])
  if allowed and str(exe) not in allowed and exe.name not in allowed: raise JobError('executable')
  ident=hashlib.sha256(json.dumps(cmd).encode()).hexdigest(); old=st['items'].get(x['id'])
  if old and old.get('command_hash')!=ident: raise JobError('command drift')
  if old and old.get('status')=='done': continue
  cwd=Path(x.get('cwd',m.get('cwd','/'))); confined(cwd,m.get('allowed_working_roots',[str(cwd)])); started=time.time();
  try:r=subprocess.run(cmd,cwd=cwd,env={k:v for k,v in os.environ.items() if k in m.get('allowed_environment_keys',[])},shell=False,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=int(m.get('wall_seconds',x.get('wall_seconds',3600))))
  except subprocess.TimeoutExpired: raise JobError('timeout')
  st['items'][x['id']]={'status':'done' if r.returncode==0 else 'failed','command_hash':ident,'returncode':r.returncode,'started_at':started,'finished_at':time.time(),'stdout_tail':r.stdout[-4000:],'stderr_tail':r.stderr[-4000:]}; atomic(state_path,st)
  if r.returncode: raise JobError('command failed')
 return st
