#!/usr/bin/env python3
"""Deterministic implementation-safety validator for the frozen eight-run pilot."""
import argparse, json, os, sys
DB="/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209"
EXPECTED=["CRR2423961","CRR2424000","CRR2423957","CRR2423986","CRR2423912","CRR2423921","CRR2423991","CRR2424010"]
def main():
 p=argparse.ArgumentParser(); p.add_argument("--job",required=True); p.add_argument("--state",required=True); p.add_argument("--summary",required=True); p.add_argument("--live-db",required=True); p.add_argument("--json-out")
 a=p.parse_args(); f=[]
 def load(x):
  try: return json.load(open(x))
  except Exception as e: f.append(f"unreadable:{x}:{e}"); return {}
 j,s,pilot=load(a.job),load(a.state),load(a.summary)
 row=s.get("jobs",{}).get("20260822T120000Z-prjca046985-native-kraken2-pilot",{})
 if row.get("status")!="done": f.append("runner.status!=done")
 if row.get("returncode")!=0: f.append("runner.returncode!=0")
 params=j.get("params",{}); runs=params.get("pilot_runs",[])
 if [x.get("run_accession") for x in runs]!=EXPECTED: f.append("job run membership mismatch")
 got=pilot.get("runs",[])
 if [x.get("run_accession") for x in got]!=EXPECTED or len(got)!=8: f.append("summary run membership mismatch")
 if pilot.get("final_status")!="done": f.append("final_status!=done")
 if pilot.get("stop_event")!="": f.append("stop_event!=empty")
 if pilot.get("new_downloaded_bytes")!=0: f.append("new_downloaded_bytes!=0")
 if pilot.get("database_manifest_identity_sha256")!=a.live_db: f.append("database identity mismatch")
 for k in ("host_filtering","trimming","bracken","biological_inference"):
  if params.get(k) is not False: f.append(f"job {k} not false")
 if pilot.get("bracken_performed") is not False: f.append("summary bracken_performed")
 if pilot.get("trimming_performed") is not False: f.append("summary trimming_performed")
 if pilot.get("biological_inference")!="PROHIBITED": f.append("summary biological_inference")
 manifest={x.get("run_accession"):x for x in runs}
 for r in got:
  acc=r.get("run_accession"); m=manifest.get(acc,{})
  if r.get("status")!="done": f.append(f"{acc}:status")
  if r.get("input_bytes")!=m.get("expected_bytes"): f.append(f"{acc}:input_bytes")
  if r.get("input_sha256")!=m.get("sha256"): f.append(f"{acc}:input_sha256")
  c=r.get("command")
  if not isinstance(c,list) or not c or os.path.basename(c[0])!="kraken2": f.append(f"{acc}:command")
  else:
   if "--db" not in c or c[c.index("--db")+1]!=DB: f.append(f"{acc}:db")
   if "--threads" not in c or c[c.index("--threads")+1]!="4": f.append(f"{acc}:threads")
   if "--confidence" in c or "--minimum-hit-groups" in c: f.append(f"{acc}:forbidden_override")
   expected_path=f"/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/{acc}.fq.gz"
   if expected_path not in c: f.append(f"{acc}:input_path")
  cr=r.get("command_result",{})
  if cr.get("returncode")!=0 or cr.get("stop_reason")!="": f.append(f"{acc}:command_result")
 if len([r for r in got if r.get("status")=="done"])!=8: f.append("successful_kraken2_count!=8")
 out={"valid":not f,"failures":f}
 if a.json_out: json.dump(out,open(a.json_out,"w"),indent=2); open(a.json_out,"a").write("\n")
 if f: print("\n".join(f),file=sys.stderr); return 1
 print("VALID"); return 0
if __name__=="__main__": sys.exit(main())
