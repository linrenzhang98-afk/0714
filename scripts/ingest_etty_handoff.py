#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
JOB="20260822T120000Z-prjca046985-native-kraken2-pilot"; SCI="03cff4d403bcb1ab0d87848a0b22b06762345070"; DB="6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3"
def main():
 repo=Path(sys.argv[1]); out=Path(sys.argv[2]); subprocess.run(["git","-C",str(repo),"fetch","origin","etty-handoff"],check=True)
 base=subprocess.check_output(["git","-C",str(repo),"rev-parse","origin/etty-handoff"],text=True).strip(); prefix=f"{base}:handoffs/{JOB}"
 manifest=json.loads(subprocess.check_output(["git","-C",str(repo),"show",prefix+"/manifest.json"],text=True))
 if manifest.get("job_id")!=JOB or manifest.get("target_branch")!="etty-handoff": raise SystemExit("SAFE_STOP manifest")
 out.mkdir(parents=True,exist_ok=True)
 (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
 for rel,h in manifest["files"].items():
  p=out/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(subprocess.check_output(["git","-C",str(repo),"show",prefix+"/"+rel]))
  if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise SystemExit("SAFE_STOP hash")
 prov=json.loads((out/"provenance.json").read_text())
 if prov.get("frozen_scientific_execution_commit")!=SCI or prov.get("database_manifest_identity_sha256")!=DB or not (out/"STATUS.txt").read_text().startswith("STATUS=PILOT_COMPLETED"): raise SystemExit("SAFE_STOP provenance")
 print("INGESTED")
if __name__=="__main__": main()
