#!/usr/bin/env python3
import csv,hashlib,json,re,sys
from pathlib import Path
MANIFEST_SHA='d9195f2643bff0e8f611ff96ab0345a50c364eaf0b04658e762984e087521d58'; ROOT='/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/'
def fail(msg): raise ValueError(msg)
def validate(inv,summary,prov,manifest,pilot):
 rows=list(csv.DictReader(open(manifest),delimiter='\t')); ca=[r['run_accession'] for r in rows]; pr=json.load(open(pilot))['params']['pilot_runs']; pa=[x.get('run_accession') for x in pr]
 if hashlib.sha256(manifest.read_bytes()).hexdigest()!=MANIFEST_SHA: fail('canonical manifest hash')
 if len(ca)!=130 or len(set(ca))!=130 or len(pr)!=8 or len(set(pa))!=8 or not set(pa)<=set(ca): fail('cohort identity')
 expected=set(ca)-set(pa); data=json.load(open(inv)); runs=data.get('runs',[]); ia=[r.get('run_accession') for r in runs]
 if set(ia)!=expected or len(ia)!=122 or len(set(ia))!=122: fail('inventory accession set')
 s=json.load(open(summary));
 for k,v in [('status','SOURCE_INVENTORY_COMPLETE'),('eligible_count',122),('present_count',122),('missing_count',0),('byte_mismatch_count',0),('duplicate_accession_count',0),('duplicate_path_count',0),('sha256_count',122),('new_downloaded_bytes',0)]:
  if s.get(k)!=v: fail('summary '+k)
 for r in runs:
  if r.get('status')!='OK' or r.get('actual_bytes')!=r.get('expected_bytes') or not re.fullmatch(r'[0-9a-f]{64}',r.get('sha256','')) or not str(r.get('source_path','')).startswith(ROOT): fail('run '+str(r.get('run_accession')))
 p=json.load(open(prov));
 if p.get('canonical_manifest_sha256')!=MANIFEST_SHA or p.get('run_count')!=122 or p.get('new_downloaded_bytes')!=0 or p.get('kraken2_executed') is not False or p.get('source_files_modified') is not False or p.get('control_main_commit') in (None,'unknown',''): fail('provenance')
 if p.get('pilot_job_sha256')!=hashlib.sha256(pilot.read_bytes()).hexdigest(): fail('pilot hash')
 if p.get('inventory_script_sha256')!=hashlib.sha256(Path(__file__).with_name('inventory_prjca046985_sources.py').read_bytes()).hexdigest(): fail('inventory script hash')
 return True
if __name__=='__main__':
 try: validate(*map(Path,sys.argv[1:6])); print('VALID_SOURCE_INVENTORY')
 except Exception as e: print('SAFE_STOP: '+str(e),file=sys.stderr); sys.exit(1)
