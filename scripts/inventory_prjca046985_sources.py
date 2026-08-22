#!/usr/bin/env python3
import csv,hashlib,json,os,sys,time,socket,getpass
from pathlib import Path
CHUNK=1<<20
ROOT='/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq'
def inputs(manifest,pilot_job):
 rows=list(csv.DictReader(open(manifest),delimiter='\t')); acc=[r['run_accession'] for r in rows]
 if len(rows)!=130 or len(set(acc))!=130: raise ValueError('canonical manifest must contain 130 unique accessions')
 pj=json.load(open(pilot_job)); pr=pj['params']['pilot_runs'];
 if len(pr)!=8 or any('run_accession' not in x for x in pr): raise ValueError('pilot must contain 8 accession rows')
 pa=[x['run_accession'] for x in pr]
 if len(set(pa))!=8 or not set(pa)<=set(acc): raise ValueError('pilot accession set invalid')
 rem=set(acc)-set(pa)
 if len(rem)!=122: raise ValueError('remaining accession count invalid')
 return [r for r in rows if r['run_accession'] in rem]
def main():
 if len(sys.argv)<4: raise SystemExit('usage: inventory manifest out pilot_job [source_root]')
 manifest,out,pilot=map(Path,sys.argv[1:4]); root=Path(sys.argv[4]) if len(sys.argv)>4 else Path(ROOT); start=time.time(); rows=inputs(manifest,pilot); records=[]; missing=[]; mismatch=[]
 for r in rows:
  a=r['run_accession']; p=root/(a+'.fq.gz'); rec={'run_accession':a,'clinical_group':r.get('group_raw'),'source_path':str(p),'expected_bytes':int(r['compressed_bytes'])}
  if not p.is_file(): rec['status']='MISSING'; missing.append(a); records.append(rec); continue
  rec['actual_bytes']=p.stat().st_size; h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(CHUNK),b''): h.update(b)
  rec['sha256']=h.hexdigest(); rec['status']='OK' if rec['actual_bytes']==rec['expected_bytes'] else 'BYTE_MISMATCH'
  if rec['status']!='OK': mismatch.append(a)
  records.append(rec)
 out.mkdir(parents=True,exist_ok=True); end=time.time(); dupacc=sorted({x for x in [r['run_accession'] for r in records] if [q['run_accession'] for q in records].count(x)>1}); paths=[r['source_path'] for r in records]; duppath=sorted({x for x in paths if paths.count(x)>1}); sha=sum('sha256' in r for r in records); status='SOURCE_INVENTORY_COMPLETE' if not missing and not mismatch and not dupacc and not duppath and sha==122 else 'SAFE_STOP'
 summary={'status':status,'eligible_count':122,'present_count':122-len(missing),'missing_count':len(missing),'byte_mismatch_count':len(mismatch),'duplicate_accession_count':len(dupacc),'duplicate_path_count':len(duppath),'sha256_count':sha,'total_source_bytes':sum(r.get('actual_bytes',0) for r in records),'new_downloaded_bytes':0,'missing_runs':missing,'byte_mismatch_runs':mismatch,'duplicate_accessions':dupacc,'duplicate_paths':duppath,'inventory_start':start,'inventory_end':end,'hostname':socket.gethostname()}
 (out/'source_inventory.json').write_text(json.dumps({'runs':records},indent=2)+'\n'); (out/'source_inventory_summary.json').write_text(json.dumps(summary,indent=2)+'\n'); (out/'STATUS.txt').write_text('STATUS='+status+'\n')
 prov={'job_id':'20260822T160000Z-prjca046985-source-inventory','control_main_commit':os.getenv('CONTROL_MAIN_COMMIT','unknown'),'inventory_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'canonical_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'pilot_job_sha256':hashlib.sha256(pilot.read_bytes()).hexdigest(),'hostname':socket.gethostname(),'user':getpass.getuser(),'python_executable':sys.executable,'python_version':sys.version.split()[0],'run_count':122,'new_downloaded_bytes':0,'kraken2_executed':False,'source_files_modified':False,'execution_start':start,'execution_end':end}
 (out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
if __name__=='__main__':
 try: main()
 except Exception as e: raise SystemExit('SAFE_STOP: '+str(e))
