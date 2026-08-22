#!/usr/bin/env python3
"""Generic, manifest-driven bounded ETYY job primitives (no project logic)."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, tempfile, time, urllib.parse, urllib.request
from pathlib import Path

class JobError(Exception): pass
def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def validate_manifest(m):
 if not m.get('authorized'): raise JobError('job is not authorized')
 items=m.get('items',[]); cap=int(m.get('transfer_cap_bytes',0));
 if not items or len({x.get('id') for x in items})!=len(items): raise JobError('duplicate item')
 dest=[]; total=0
 for x in items:
  u=urllib.parse.urlparse(x.get('url','')); d=Path(x.get('destination',''))
  if u.scheme!='https' or u.hostname not in m.get('allowed_hosts',[]): raise JobError('URL host')
  if not d.is_absolute() or d in dest: raise JobError('destination')
  if int(x.get('expected_bytes',0))<=0: raise JobError('expected bytes')
  dest.append(d); total+=int(x['expected_bytes'])
 if total>cap: raise JobError('manifest exceeds transfer cap')
 return items
def acquire(m,state_path):
 items=validate_manifest(m); state=json.loads(state_path.read_text()) if state_path.exists() else {'items':{},'network_bytes':0}
 for x in items:
  d=Path(x['destination']); d.parent.mkdir(parents=True,exist_ok=True); old=state['items'].get(x['id'])
  if d.exists():
   if d.stat().st_size!=int(x['expected_bytes']) or (x.get('sha256') and sha256(d)!=x['sha256']): raise JobError('conflicting existing file')
   state['items'][x['id']]={'status':'reused','bytes':d.stat().st_size,'sha256':sha256(d)}; continue
  part=d.with_name(d.name+'.part'); req=urllib.request.Request(x['url'])
  with urllib.request.urlopen(req,timeout=60) as r:
   n=0
   with open(part,'wb') as f:
    for b in iter(lambda:r.read(1024*1024),b''):
     n+=len(b)
     if state['network_bytes']+n>int(m['transfer_cap_bytes']): raise JobError('transfer cap exceeded')
     f.write(b)
   if n!=int(x['expected_bytes']): raise JobError('byte mismatch')
   etag=r.headers.get('ETag')
  part.replace(d); state['network_bytes']+=n; state['items'][x['id']]={'status':'done','bytes':n,'sha256':sha256(d),'etag':etag}
 state_path.parent.mkdir(parents=True,exist_ok=True); state_path.write_text(json.dumps(state,indent=2)+'\n'); return state
def execute(m,state_path):
 items=validate_manifest(m); st=json.loads(state_path.read_text()) if state_path.exists() else {}
 for x in items:
  cmd=x.get('command');
  if not isinstance(cmd,list) or not cmd or any(not isinstance(a,str) for a in cmd): raise JobError('command must be argv list')
  r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=int(m.get('wall_seconds',3600)))
  st.setdefault('items',{})[x['id']]={'returncode':r.returncode,'stdout_tail':r.stdout[-1000:],'stderr_tail':r.stderr[-1000:]}
  if r.returncode: raise JobError('command failed: '+x['id'])
 state_path.write_text(json.dumps(st,indent=2)+'\n'); return st
def main():
 p=argparse.ArgumentParser(); p.add_argument('job'); p.add_argument('--acquire',action='store_true'); p.add_argument('--state',required=True); a=p.parse_args(); m=json.loads(Path(a.job).read_text()); (acquire if a.acquire else execute)(m,Path(a.state))
if __name__=='__main__': main()
