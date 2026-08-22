#!/usr/bin/env python3
import hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ALLOWED={"STATUS.txt","pilot_summary.json","provenance.json","validation_report.json","runner_state.json","database_identity/hospital_readonly_inventory.json"}
JOB="20260822T120000Z-prjca046985-native-kraken2-pilot"; SCI="03cff4d403bcb1ab0d87848a0b22b06762345070"; DB="6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3"; CAP=5*1024*1024
def die(x): print("SAFE_STOP: "+x,file=sys.stderr); raise SystemExit(2)
def main():
 src=Path(sys.argv[1]); repo=Path(sys.argv[2]); branch="etty-handoff"; dest=repo/"handoffs"/JOB
 if branch=="main" or subprocess.check_output(["git","-C",str(repo),"branch","--show-current"],text=True).strip()!=branch: die("publisher checkout is not etty-handoff")
 if subprocess.check_output(["git","-C",str(repo),"remote","get-url","origin"],text=True).strip()!="git@github.com:linrenzhang98-afk/0714.git": die("wrong remote")
 status=(src/"STATUS.txt").read_text()
 if not status.startswith("STATUS=PILOT_COMPLETED"): die("handoff not completed")
 for rel in ALLOWED:
  p=src/rel
  if not p.is_file(): die("missing "+rel)
  if p.stat().st_size>CAP: die("file too large "+rel)
 total=sum((src/r).stat().st_size for r in ALLOWED)
 if total>CAP: die("handoff exceeds size cap")
 for rel in ALLOWED:
  text=(src/rel).read_bytes()
  if b"PRIVATE KEY" in text or re.search(rb"(api[_-]?key|password|secret|token)\s*[:=]\s*[^\s]{12,}",text,re.I): die("secret-like content")
 summary=json.loads((src/"pilot_summary.json").read_text()); prov=json.loads((src/"provenance.json").read_text())
 if prov.get("frozen_scientific_execution_commit")!=SCI or prov.get("database_manifest_identity_sha256")!=DB: die("provenance mismatch")
 if summary.get("final_status")!="done" or summary.get("new_downloaded_bytes")!=0 or len(summary.get("runs",[]))!=8: die("summary invariant")
 files={r:hashlib.sha256((src/r).read_bytes()).hexdigest() for r in sorted(ALLOWED)}
 manifest={"job_id":JOB,"handoff_published_at":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"ETYY_hostname":os.uname().nodename,"publisher_role":"compute-handoff-only","frozen_science_sha":SCI,"bootstrap_control_sha":prov.get("bootstrap_control_commit"),"source_handoff_path":str(src),"files":files,"total_bytes":total,"validation_status":"validated","sensitivity_classification":"non-sensitive","target_branch":branch}
 if (dest/"manifest.json").exists():
  old=json.loads((dest/"manifest.json").read_text())
  if old.get("files")==files: print("ALREADY_PUBLISHED"); return
  die("existing job has different handoff hashes")
 dest.mkdir(parents=True,exist_ok=True); (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
 for rel in ALLOWED: (dest/rel).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src/rel,dest/rel)
 subprocess.run(["git","-C",str(repo),"add","--","handoffs/"+JOB],check=True)
 if not subprocess.run(["git","-C",str(repo),"diff","--cached","--quiet"]).returncode: print("ALREADY_PUBLISHED"); return
 subprocess.run(["git","-C",str(repo),"diff","--cached","--check"],check=True)
 subprocess.run(["git","-C",str(repo),"commit","-m","Publish bounded ETYY handoff"],check=True)
 subprocess.run(["git","-C",str(repo),"push","origin",branch],check=True); print("PUBLISHED")
if __name__=="__main__": main()
