#!/usr/bin/env python3
import json, pathlib, sys
def main():
 root=pathlib.Path(sys.argv[1]); state=root/"state/runner_state.json"; log=root/"logs/runner.jsonl"; result=root/"results/20260822T120000Z-prjca046985-native-kraken2-pilot"
 evidence={"state":state.exists(),"log":log.exists(),"summary":(result/"pilot_summary.json").exists(),"kreport":False,"kraken_out":False,"command_evidence":False}
 for p in [result, root.parent/"0714_handoff/20260822T120000Z-prjca046985-native-kraken2-pilot"]:
  if p.exists():
   evidence["kreport"] |= any(p.rglob("*.kreport"))
   evidence["kraken_out"] |= any(p.rglob("*.kraken2.out"))
   evidence["command_evidence"] |= any("kraken2" in x.read_text(errors="ignore").lower() for x in p.rglob("*") if x.is_file() and x.stat().st_size < 5_000_000)
 classification="UNKNOWN"
 try:
  s=json.load(open(state)); row=s.get("jobs",{}).get("20260822T150000Z-prjca046985-native-kraken2-pilot",s.get("jobs",{}).get("20260822T120000Z-prjca046985-native-kraken2-pilot",{}))
  if row.get("status")=="done" and evidence["summary"]: classification="COMPLETED"
  elif row.get("status") in {"failed","rejected","stopped"} and not (evidence["kreport"] or evidence["kraken_out"] or evidence["command_evidence"]): classification="PRE_EXECUTION_FAILURE_ZERO_KRAKEN2"
  elif evidence["kreport"] or evidence["kraken_out"] or evidence["command_evidence"]: classification="PARTIAL_EXECUTION"
 except Exception: pass
 print(json.dumps({"classification":classification,"evidence":evidence,"state":str(state),"result":str(result)}))
if __name__=="__main__": main()
