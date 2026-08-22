#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/disk1
CONTROL=$ROOT/0714_control
REPO=$CONTROL/repo
JOB=jobs/20260822T120000Z-prjca046985-native-kraken2-pilot.json
DB=$ROOT/db/kraken2/k2_pluspfp_16gb_20221209
AUDIT=$ROOT/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit
HANDOFF=$ROOT/0714_handoff/20260822T120000Z-prjca046985-native-kraken2-pilot
PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
[[ "$(hostname)" == ETYY ]] || { echo "hostname is not ETYY" >&2; exit 2; }
[[ "$(id -un)" == suma ]] || { echo "user is not suma" >&2; exit 2; }
[[ -d $ROOT && -r $DB && -d $AUDIT/fastq && -w $ROOT ]] || { echo "ETYY paths unavailable" >&2; exit 2; }
[[ -x $PY ]] || { echo "mgshotgun Python unavailable" >&2; exit 2; }
command -v git >/dev/null; git ls-remote https://github.com/linrenzhang98-afk/0714.git HEAD >/dev/null || { echo "GitHub connectivity failed" >&2; exit 2; }
mkdir -p "$CONTROL/state" "$CONTROL/logs" "$CONTROL/results" "$HANDOFF"
[[ -w $HANDOFF ]] || { echo "handoff not writable" >&2; exit 2; }
if [[ ! -d $REPO/.git ]]; then
  git clone https://github.com/linrenzhang98-afk/0714.git "$REPO"
else
  git -C "$REPO" fetch origin main
  git -C "$REPO" merge --ff-only origin/main
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$(git -C "$REPO" rev-parse origin/main)" ]] || { echo "control clone diverged" >&2; exit 2; }
[[ -f $REPO/$JOB ]] || { echo "pilot job absent" >&2; exit 2; }
EXECUTION_COMMIT=$(git -C "$REPO" rev-parse HEAD)
[[ "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["task"])' "$REPO/$JOB")" == metagenome_deep_review ]] || { echo "task not allowlisted" >&2; exit 2; }
python - "$REPO/$JOB" "$AUDIT/fastq" <<'PY'
import hashlib,json,os,sys
j=json.load(open(sys.argv[1])); rows=j['params']['pilot_runs']; root=sys.argv[2]
for r in rows:
 p=os.path.join(root,r['run_accession']+'.fq.gz')
 if os.path.getsize(p)!=r['expected_bytes']: raise SystemExit('FASTQ byte mismatch '+p)
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''): h.update(c)
 if h.hexdigest()!=r['sha256']: raise SystemExit('FASTQ checksum mismatch '+p)
PY
KR=$(PATH=/home/suma/anaconda3/envs/mgshotgun/bin:$PATH command -v kraken2) || { echo "Kraken2 unavailable" >&2; exit 2; }
[[ "$(PATH=/home/suma/anaconda3/envs/mgshotgun/bin:$PATH kraken2 --version 2>&1 | head -1)" == *"2.17.1"* ]] || { echo "Kraken2 version mismatch" >&2; exit 2; }
[[ "$(df -Pk "$ROOT" | awk 'NR==2{print $4}')" -gt 500000000 ]] || { echo "insufficient disk" >&2; exit 2; }
[[ "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" -gt 67108864 ]] || { echo "insufficient RAM" >&2; exit 2; }
INV=$REPO/reports_public/prjna1056765_external_cohort_pilot_package/hospital_pilot_result/database_identity/hospital_readonly_inventory.json
[[ "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["database_manifest_identity_sha256"])' "$INV")" == 6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3 ]] || { echo "database identity mismatch" >&2; exit 2; }
CONFIG=$CONTROL/config.local.json
cat > "$CONFIG" <<EOF
{"repo_path":"$REPO","jobs_glob":"$JOB","state_path":"$CONTROL/state/runner_state.json","log_path":"$CONTROL/logs/runner.jsonl","lock_path":"$CONTROL/state/runner.lock","results_root":"$CONTROL/results","allowed_data_roots":["$ROOT"],"git_timeout_seconds":120,"default_task_timeout_seconds":28800,"tasks":{"metagenome_deep_review":{"script":"$REPO/pipelines/metagenome_deep_review_runner.py","timeout_seconds":28800}}}
EOF
rm -f "$CONTROL/state/preflight_state.json" "$CONTROL/logs/preflight.jsonl"
sed "s#runner_state.json#preflight_state.json#; s#runner.jsonl#preflight.jsonl#" "$CONFIG" > "$CONTROL/config.preflight.json"
$PY "$REPO/runner/runner.py" --config "$CONTROL/config.preflight.json" --dry-run
[[ "$(python -c 'import json,sys; s=json.load(open(sys.argv[1])); print(len(s.get("jobs",{})))' "$CONTROL/state/preflight_state.json")" == 1 ]] || { echo "preflight did not accept exactly one job" >&2; exit 2; }
rm -f "$CONTROL/state/preflight_state.json" "$CONTROL/logs/preflight.jsonl"
JOB_SHA256=$(sha256sum "$REPO/$JOB" | awk '{print $1}')
DB_IDENTITY=6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3
echo "PREFLIGHT_OK commit=$EXECUTION_COMMIT job=$JOB kraken2_commands=0"
$PY "$REPO/runner/runner.py" --config "$CONFIG"
cp "$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot/pilot_summary.json" "$HANDOFF/pilot_summary.json"
cp "$CONTROL/results/20260822T120000Z-prjca046985-native-kraken2-pilot/validation_report.json" "$HANDOFF/validation_report.json"
cp "$CONTROL/logs/runner.jsonl" "$HANDOFF/runner.jsonl"
cp "$CONTROL/state/runner_state.json" "$HANDOFF/runner_state.json"
printf 'STATUS=pilot_runner_completed\nCOMMIT=%s\nJOB=%s\nJOB_SHA256=%s\nDATABASE_MANIFEST_IDENTITY_SHA256=%s\n' "$EXECUTION_COMMIT" "$JOB" "$JOB_SHA256" "$DB_IDENTITY" > "$HANDOFF/STATUS.txt"
echo "PILOT_HANDOFF=$HANDOFF"
