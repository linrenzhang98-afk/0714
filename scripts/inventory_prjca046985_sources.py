#!/usr/bin/env python3
import csv,hashlib,json,os,sys,time,socket
from pathlib import Path
def main():
 manifest=Path(sys.argv[1]); out=Path(sys.argv[2]); rows=list(csv.DictReader(open(manifest),delimiter='\t')); pilot=set(json.load(open(sys.argv[3]))['params']['pilot_runs']); rows=[r for r in rows if r['run_accession'] not in pilot]; start=time.time(); records=[]; missing=[]; mismatch=[]; paths=set()
 for r in rows:
  source=r.get('source_path') or f'/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/{r["run_accession"]}.fq.gz'; p=Path(source); rec={'run_accession':r['run_accession'],'clinical_group':r.get('group_raw'),'source_path':source,'expected_bytes':int(r['compressed_bytes'])}
  if not p.is_file(): missing.append(r['run_accession']); rec['status']='MISSING'; records.append(rec); continue
  rec['actual_bytes']=p.stat().st_size; rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest(); rec['status']='OK' if rec['actual_bytes']==rec['expected_bytes'] else 'BYTE_MISMATCH'; mismatch += [] if rec['status']=='OK' else [r['run_accession']]; paths.add(str(p)); records.append(rec)
 out.mkdir(parents=True,exist_ok=True); summary={'status':'SOURCE_INVENTORY_COMPLETE' if len(records)==122 and not missing and not mismatch and len(paths)==122 else 'SAFE_STOP','eligible_count':122,'present_count':sum(x.get('status')!='MISSING' for x in records),'missing_count':len(missing),'byte_mismatch_count':len(mismatch),'duplicate_path_count':122-len(paths),'total_source_bytes':sum(x.get('actual_bytes',0) for x in records),'inventory_start':start,'inventory_end':time.time(),'hostname':socket.gethostname(),'new_downloaded_bytes':0,'missing_runs':missing,'byte_mismatch_runs':mismatch}; json.dump({'runs':records},open(out/'source_inventory.json','w'),indent=2); json.dump(summary,open(out/'source_inventory_summary.json','w'),indent=2); (out/'STATUS.txt').write_text(summary['status']+'\n')
if __name__=='__main__': main()
