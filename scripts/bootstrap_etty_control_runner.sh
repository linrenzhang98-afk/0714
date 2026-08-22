#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/disk1
CONTROL=$ROOT/0714_control
REPO=$CONTROL/repo
JOB=jobs/20260822T120000Z-prjca046985-native-kraken2-pilot.json
SCIENCE_COMMIT=03cff4d403bcb1ab0d87848a0b22b06762345070
DB=$ROOT/db/kraken2/k2_pluspfp_16gb_20221209
AUDIT=$ROOT/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit
HANDOFF=$ROOT/0714_handoff/20260822T120000Z-prjca046985-native-kraken2-pilot
PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
MGSHOTGUN_BIN=/home/suma/anaconda3/envs/mgshotgun/bin
export PATH="$MGSHOTGUN_BIN:$PATH"
VALIDATOR="$(cd "$(dirname "$0")" && pwd)/validate_etty_native_kraken2_pilot.py"
EXPECTED_DB=6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3
mkdir -p "$HANDOFF" 2>/dev/null || true
fail(){ local r="$*"; echo "SAFE_STOP: $r" >&2; if [[ -w "$HANDOFF" ]]; then printf 'STATUS=SAFE_STOP\nREASON=%s\n' "$r" > "$HANDOFF/STATUS.txt"; fi; exit 2; }
[[ "$(hostname)" == ETYY ]] || fail "hostname is not ETYY"
[[ "$(id -un)" == suma ]] || fail "user is not suma"
[[ -d $ROOT && -r $DB && -d $AUDIT/fastq && -w $ROOT ]] || fail "ETYY paths unavailable"
[[ -x $PY ]] || fail "mgshotgun Python unavailable"
command -v git >/dev/null || fail "git unavailable"
git ls-remote git@github.com:linrenzhang98-afk/0714.git HEAD >/dev/null || fail "GitHub SSH connectivity failed"
mkdir -p "$CONTROL/state" "$CONTROL/logs" "$CONTROL/results" "$CONTROL/preflight" "$HANDOFF"
[[ -w $HANDOFF ]] || fail "handoff not writable"
trap 'rc=$?; if [[ $rc -ne 0 && -w "$HANDOFF" ]]; then printf "STATUS=SAFE_STOP\nREASON=bootstrap exited rc=%s\n" "$rc" > "$HANDOFF/STATUS.txt"; fi' ERR
if [[ ! -d $REPO/.git ]]; then
  git clone git@github.com:linrenzhang98-afk/0714.git "$REPO" || fail "control clone failed"
else
  git -C "$REPO" fetch origin main || fail "control fetch failed"
  git -C "$REPO" checkout --detach origin/main || fail "control checkout failed"
fi
git -C "$REPO" fetch origin main || fail "science commit fetch failed"
BOOTSTRAP_COMMIT=$(git -C "$REPO" rev-parse origin/main)
export BOOTSTRAP_COMMIT
git -C "$REPO" checkout --detach "$SCIENCE_COMMIT" || fail "science commit unavailable"
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$SCIENCE_COMMIT" ]] || fail "scientific execution revision mismatch"
[[ -f "$REPO/$JOB" ]] || fail "pilot job absent"
JOB_ABS="$REPO/$JOB"
[[ -f "$JOB_ABS" ]] || fail "absolute pilot job absent"
KR=$($PY -c 'import shutil,sys; p=shutil.which("kraken2"); print(p or ""); sys.exit(0 if p else 2)') || fail "Kraken2 unavailable in mgshotgun PATH"
[[ "$KR" == "$MGSHOTGUN_BIN"/* ]] || fail "Kraken2 outside mgshotgun environment"
DBOUT=$CONTROL/preflight/database_identity
mkdir -p "$DBOUT"
"$PY" - "$REPO" "$DBOUT" "$DB" <<'PY'
import importlib.util, pathlib, sys
repo, out, db = map(pathlib.Path, sys.argv[1:])
spec=importlib.util.spec_from_file_location("pilot_runner", repo/"pipelines/metagenome_deep_review_runner.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
if m.readonly_inventory(pathlib.Path(out), pathlib.Path("/mnt/disk1/db/kraken2/0714"), pathlib.Path(db), pathlib.Path(db)) != 0: raise SystemExit(2)
PY
LIVE_DB=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["database_manifest_identity_sha256"])' "$DBOUT/hospital_readonly_inventory.json")
[[ "$LIVE_DB" == "$EXPECTED_DB" ]] || fail "live database identity mismatch: $LIVE_DB"
mkdir -p "$HANDOFF/database_identity"
cp "$DBOUT/hospital_readonly_inventory.json" "$HANDOFF/database_identity/hospital_readonly_inventory.json"
KRVER=$(kraken2 --version 2>&1 | head -1)
[[ "$KRVER" == *"2.17.1"* ]] || fail "Kraken2 version mismatch: $KRVER"
MIN_FREE_KIB=6000000 # df -Pk reports KiB; margin above the authorized 5 GB workspace cap.
[[ "$(df -Pk "$ROOT" | awk 'NR==2{print $4}')" -gt "$MIN_FREE_KIB" ]] || fail "insufficient disk"
[[ "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" -gt 67108864 ]] || fail "insufficient RAM"
JOB_SHA256=$(sha256sum "$JOB_ABS" | awk '{print $1}')
CONFIG=$CONTROL/config.local.json
cat > "$CONFIG" <<EOF
{"repo_path":"$REPO","jobs_glob":"$JOB","state_path":"$CONTROL/state/runner_state.json","log_path":"$CONTROL/logs/runner.jsonl","lock_path":"$CONTROL/state/runner.lock","results_root":"$CONTROL/results","allowed_data_roots":["$ROOT"],"git_timeout_seconds":120,"default_task_timeout_seconds":28800,"tasks":{"metagenome_deep_review":{"script":"$REPO/pipelines/metagenome_deep_review_runner.py","timeout_seconds":28800}}}
EOF
"$PY" - "$JOB_ABS" "$AUDIT/fastq" <<'PY'
import hashlib,json,os,sys
j=json.load(open(sys.argv[1])); root=sys.argv[2]
assert j["task"] == "metagenome_deep_review" and len(j["params"]["pilot_runs"]) == 8
for r in j["params"]["pilot_runs"]:
 p=os.path.join(root,r["run_accession"]+".fq.gz"); assert os.path.getsize(p)==r["expected_bytes"],p
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1<<20),b""): h.update(c)
 assert h.hexdigest()==r["sha256"],p
PY
STATE=$CONTROL/state/runner_state.json
ATTEMPT_JSON=$CONTROL/recovery/last_attempt.json
mkdir -p "$CONTROL/recovery"
if [[ -e "$STATE" || -e "$CONTROL/logs/runner.jsonl" || -d "$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot" || -e "$HANDOFF/STATUS.txt" ]]; then ATTEMPT_JSON_DATA=$($PY "$(dirname "$VALIDATOR")/classify_etty_pilot_attempt.py" "$CONTROL" 2>/dev/null || echo '{"classification":"UNKNOWN"}'); else ATTEMPT_JSON_DATA='{"classification":"NEW"}'; fi
printf '%s\n' "$ATTEMPT_JSON_DATA" > "$ATTEMPT_JSON"
CLASSIFICATION=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1])).get("classification","UNKNOWN"))' "$ATTEMPT_JSON")
if [[ "$CLASSIFICATION" == PRE_EXECUTION_FAILURE_ZERO_KRAKEN2 && ! -f "$CONTROL/recovery/retry_used" ]]; then
  REC="$CONTROL/recovery/$(date -u +%Y%m%dT%H%M%SZ)-preexecution-bootstrap-$BOOTSTRAP_COMMIT"
  mkdir -p "$REC"
  for x in "$STATE" "$CONTROL/logs/runner.jsonl" "$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot" "$HANDOFF/STATUS.txt" "$HANDOFF/provenance.json" "$HANDOFF/validation_report.json"; do [[ -e "$x" ]] && cp -a "$x" "$REC/" || true; done
  "$PY" - "$REC/recovery.json" <<PY
import json,datetime
json.dump({"prior_bootstrap_commit":"$BOOTSTRAP_COMMIT","replacement_bootstrap_commit":"$BOOTSTRAP_COMMIT","failure_classification":"PRE_EXECUTION_FAILURE_ZERO_KRAKEN2","KRAKEN2_COMMANDS_OBSERVED":0,"recovery_timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()},open("$REC/recovery.json","w"),indent=2)
PY
  touch "$CONTROL/recovery/retry_used"
  rm -f "$STATE" "$CONTROL/logs/runner.jsonl"
  rm -rf "$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot"
fi
[[ "$CLASSIFICATION" != PARTIAL_EXECUTION && "$CLASSIFICATION" != UNKNOWN ]] || fail "prior attempt classification=$CLASSIFICATION; no automatic retry"
if [[ -f "$HANDOFF/STATUS.txt" ]]; then
  status=$(sed -n 's/^STATUS=//p' "$HANDOFF/STATUS.txt" | head -1)
  if [[ "$status" == PILOT_COMPLETED ]]; then
    "$PY" "$VALIDATOR" --job "$JOB_ABS" --state "$HANDOFF/runner_state.json" --summary "$HANDOFF/pilot_summary.json" --live-db "$LIVE_DB" || fail "existing completion failed full validation"
    echo "ALREADY_COMPLETED=$HANDOFF"; exit 0
  fi
  [[ -z "$status" ]] || fail "existing final state: $status"
fi
if [[ -f "$STATE" ]]; then
  STATE_STATUS=$($PY -c 'import json,sys; s=json.load(open(sys.argv[1])); print(s.get("jobs",{}).get("20260822T120000Z-prjca046985-native-kraken2-pilot",{}).get("status","missing"))' "$STATE" 2>/dev/null || echo unreadable)
  if [[ "$STATE_STATUS" == done ]]; then
    [[ -f "$HANDOFF/pilot_summary.json" && -f "$HANDOFF/runner_state.json" ]] || fail "runner state done but persisted handoff incomplete"
    "$PY" "$VALIDATOR" --job "$JOB_ABS" --state "$HANDOFF/runner_state.json" --summary "$HANDOFF/pilot_summary.json" --live-db "$LIVE_DB" || fail "existing done state failed full validation"
    echo "ALREADY_COMPLETED=$HANDOFF"; exit 0
  fi
  fail "existing runner state status=$STATE_STATUS; no rerun permitted"
fi
find "$CONTROL/results" -mindepth 1 -maxdepth 1 -type d -print -quit | grep -q . && fail "partial results require manual review" || true
rm -f "$CONTROL/state/preflight_state.json" "$CONTROL/logs/preflight.jsonl"
sed "s#runner_state.json#preflight_state.json#; s#runner.jsonl#preflight.jsonl#" "$CONFIG" > "$CONTROL/config.preflight.json"
"$PY" "$REPO/runner/runner.py" --config "$CONTROL/config.preflight.json" --dry-run --no-pull
[[ "$("$PY" -c 'import json,sys; s=json.load(open(sys.argv[1])); print(len(s.get("jobs",{})))' "$CONTROL/state/preflight_state.json")" == 1 ]] || fail "preflight did not accept exactly one job"
rm -f "$CONTROL/state/preflight_state.json" "$CONTROL/logs/preflight.jsonl"
START=$(date -Is)
set +e; "$PY" "$REPO/runner/runner.py" --config "$CONFIG" --no-pull; RC=$?; set -e
RESULT=$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot
set +e
"$PY" - "$STATE" "$RESULT/pilot_summary.json" "$JOB_ABS" "$LIVE_DB" "$KR" "$KRVER" "$HANDOFF" "$START" <<'PY'
import json,os,sys
state,summary,job,dbid,kr,krver,handoff,start=sys.argv[1:]
failures=[]
def bad(x): failures.append(x)
try: s=json.load(open(state)); row=s["jobs"]["20260822T120000Z-prjca046985-native-kraken2-pilot"]
except Exception as e: bad(f"runner state unreadable: {e}"); row={}
if row.get("status")!="done" or row.get("returncode")!=0: bad("runner state is not done/zero")
try: p=json.load(open(summary))
except Exception as e: bad(f"pilot summary unreadable: {e}"); p={}
expected=[r["run_accession"] for r in json.load(open(job))["params"]["pilot_runs"]]
if p.get("final_status")!="done" or p.get("stop_event")!="" or p.get("new_downloaded_bytes")!=0: bad("summary completion/download invariant")
if [r.get("run_accession") for r in p.get("runs",[])]!=expected or len(p.get("runs",[]))!=8 or any(r.get("status")!="done" for r in p.get("runs",[])): bad("run membership/completion invariant")
if p.get("bracken_performed") is not False or p.get("trimming_performed") is not False or p.get("biological_inference")!="PROHIBITED" or p.get("database_manifest_identity_sha256")!=dbid: bad("scope/database invariant")
for r in p.get("runs",[]):
 cmd=r.get("kraken2_command") or r.get("command") or []
 text=" ".join(cmd) if isinstance(cmd,list) else str(cmd)
 if not cmd or "/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209" not in text or "--threads 4" not in text: bad("Kraken2 command invariant")
 if "--confidence" in text or "--minimum-hit-groups" in text: bad("forbidden Kraken2 override")
if len([r for r in p.get("runs",[]) if r.get("status")=="done"]) != 8: bad("Kraken2 command count")
os.makedirs(handoff,exist_ok=True)
json.dump({"bootstrap_control_commit":os.environ.get("BOOTSTRAP_COMMIT","unknown"),"frozen_scientific_execution_commit":"03cff4d403bcb1ab0d87848a0b22b06762345070","job_sha256":__import__("hashlib").sha256(open(job,"rb").read()).hexdigest(),"database_manifest_identity_sha256":dbid,"kraken2_path":kr,"kraken2_version":krver,"python_path":"/home/suma/anaconda3/envs/mgshotgun/bin/python","python_version":__import__("sys").version.split()[0],"hostname":os.uname().nodename,"user":"suma","run_ids":expected,"host_filtering_performed":False,"trimming_performed":False,"bracken_performed":False,"new_downloaded_bytes":0,"execution_start":start,"execution_end":__import__("datetime").datetime.now().astimezone().isoformat()},open(os.path.join(handoff,"provenance.json"),"w"),indent=2)
if failures:
 open(os.path.join(handoff,"STATUS.txt"),"w").write("STATUS=SAFE_STOP\nREASON="+"; ".join(failures)+"\n"); raise SystemExit(3)
PY
TEST_RC=$?
set -e
"$PY" "$VALIDATOR" --job "$JOB_ABS" --state "$STATE" --summary "$RESULT/pilot_summary.json" --live-db "$LIVE_DB" || TEST_RC=3
cp "$RESULT/pilot_summary.json" "$HANDOFF/pilot_summary.json" 2>/dev/null || true
cp "$RESULT/validation_report.json" "$HANDOFF/validation_report.json" 2>/dev/null || true
cp "$CONTROL/logs/runner.jsonl" "$HANDOFF/runner.jsonl" 2>/dev/null || true
cp "$STATE" "$HANDOFF/runner_state.json" 2>/dev/null || true
[[ $RC -eq 0 && $TEST_RC -eq 0 ]] || fail "pilot validation failed; SAFE_STOP preserved"
mkdir -p "$HANDOFF/database_identity"
cp "$DBOUT/hospital_readonly_inventory.json" "$HANDOFF/database_identity/hospital_readonly_inventory.json"
printf 'STATUS=PILOT_COMPLETED\nEXECUTION_COMMIT=%s\nBOOTSTRAP_CONTROL_COMMIT=%s\nJOB_SHA256=%s\nDATABASE_MANIFEST_IDENTITY_SHA256=%s\nKRAKEN2_COMMANDS_COMPLETED=8\nSAMPLES_COMPLETED=8\nNEW_DOWNLOADED_BYTES=0\n' "$SCIENCE_COMMIT" "$BOOTSTRAP_COMMIT" "$JOB_SHA256" "$LIVE_DB" > "$HANDOFF/STATUS.txt"
echo "PILOT_HANDOFF=$HANDOFF"
