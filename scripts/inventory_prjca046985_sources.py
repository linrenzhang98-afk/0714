#!/usr/bin/env python3
import csv,hashlib,json,os,sys,time,socket,getpass
from pathlib import Path
CHUNK=1<<20; PILOT=set(json.load(open(sys.argv[3]))["params"]["pilot_runs"]) if len(sys.argv)>3 else set()
def main():
 manifest,out=Path(sys.argv[1]),Path(sys.argv[2]); start=time.time(); rows=list(csv.DictReader(open(manifest),delimiter="\t")); rows=[r for r in rows if r["run_accession"] not in PILOT]
 if len(rows)!=122: raise SystemExit("SAFE_STOP: expected exactly 122 remaining runs")
 acc=[r["run_accession"] for r in rows]; paths=[f"/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/{x}.fq.gz" for x in acc]
 dupacc=sorted({x for x in acc if acc.count(x)>1}); duppath=sorted({x for x in paths if paths.count(x)>1}); records=[]; missing=[]; mismatch=[]
 for r,p in zip(rows,paths):
  rec={"run_accession":r["run_accession"],"clinical_group":r.get("group_raw"),"source_path":p,"expected_bytes":int(r["compressed_bytes"])}
  q=Path(p)
  if not q.is_file() or not q.stat().st_mode & 0o100000: rec["status"]="MISSING"; missing.append(r["run_accession"]); records.append(rec); continue
  rec["actual_bytes"]=q.stat().st_size; h=hashlib.sha256()
  with q.open("rb") as f:
   for b in iter(lambda:f.read(CHUNK),b""): h.update(b)
  rec["sha256"]=h.hexdigest(); rec["status"]="OK" if rec["actual_bytes"]==rec["expected_bytes"] else "BYTE_MISMATCH"
  if rec["status"]!="OK": mismatch.append(r["run_accession"])
  records.append(rec)
 out.mkdir(parents=True,exist_ok=True); end=time.time(); summary={"status":"SOURCE_INVENTORY_COMPLETE" if len(records)==122 and not missing and not mismatch and not dupacc and not duppath and sum("sha256" in x for x in records)==122 else "SAFE_STOP","eligible_count":122,"present_count":sum(x["status"]!="MISSING" for x in records),"missing_count":len(missing),"byte_mismatch_count":len(mismatch),"duplicate_accession_count":len(dupacc),"duplicate_path_count":len(duppath),"sha256_count":sum("sha256" in x for x in records),"total_source_bytes":sum(x.get("actual_bytes",0) for x in records),"new_downloaded_bytes":0,"missing_runs":missing,"byte_mismatch_runs":mismatch,"duplicate_accessions":dupacc,"duplicate_paths":duppath,"inventory_start":start,"inventory_end":end,"hostname":socket.gethostname()}
 json.dump({"runs":records},open(out/"source_inventory.json","w"),indent=2); json.dump(summary,open(out/"source_inventory_summary.json","w"),indent=2); (out/"STATUS.txt").write_text("STATUS="+summary["status"]+"\n"); json.dump({"job_id":"20260822T160000Z-prjca046985-source-inventory","control_main_commit":os.getenv("CONTROL_MAIN_COMMIT","unknown"),"inventory_script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"canonical_manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),"pilot_job_sha256":hashlib.sha256(Path(sys.argv[3]).read_bytes()).hexdigest(),"hostname":socket.gethostname(),"user":getpass.getuser(),"python_executable":sys.executable,"python_version":sys.version.split()[0],"run_count":122,"new_downloaded_bytes":0,"kraken2_executed":False,"source_files_modified":False,"execution_start":start,"execution_end":end},open(out/"provenance.json","w"),indent=2)
if __name__=="__main__": main()
