#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
CONDA_SH="${CONDA_SH:-/home/suma/anaconda3/etc/profile.d/conda.sh}"
CONDA_ENV="${CONDA_ENV:-mgshotgun}"
PLAN_DIR="${PLAN_DIR:-jobs/planned_production_prjna1056765}"
ACTIVE_DIR="${ACTIVE_DIR:-jobs}"
STATE_FILE="${STATE_FILE:-.runner_state/runner_state.json}"
CONFIG_FILE="${CONFIG_FILE:-runner/config.local.json}"
MAX_BATCH="${MAX_BATCH:-3}"
LOG_FILE="${LOG_FILE:-reports_public/autopilot_production.log}"

cd "$REPO_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  printf '%s %s\n' "$(date -Iseconds)" "$*" | tee -a "$LOG_FILE"
}

if pgrep -f "runner/runner.py --config $CONFIG_FILE" >/dev/null 2>&1; then
  log "runner already active; autopilot will not start another job"
  exit 0
fi

if [ ! -d "$PLAN_DIR" ]; then
  log "planned production directory missing: $PLAN_DIR"
  exit 0
fi

if [ ! -f "$CONDA_SH" ]; then
  log "conda activation script missing: $CONDA_SH"
  exit 0
fi

next_job=""
for batch in $(seq -f "%03g" 1 "$MAX_BATCH"); do
  planned="$(find "$PLAN_DIR" -maxdepth 1 -type f -name "*batch-${batch}.json" | sort | head -n 1)"
  if [ -z "$planned" ]; then
    log "no planned job found for batch-$batch"
    continue
  fi
  job_id="$(python - "$planned" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["job_id"])
PY
)"
  if [ -f "$STATE_FILE" ] && python - "$STATE_FILE" "$job_id" <<'PY'
import json, sys
state_path, job_id = sys.argv[1], sys.argv[2]
with open(state_path, encoding="utf-8") as f:
    state = json.load(f)
job = state.get("jobs", {}).get(job_id, {})
sys.exit(0 if job.get("status") in {"done", "failed", "rejected"} else 1)
PY
  then
    log "batch-$batch already final: $job_id"
    continue
  fi
  active="$ACTIVE_DIR/$(basename "$planned")"
  if [ ! -f "$active" ]; then
    cp "$planned" "$active"
    log "activated $active"
  fi
  next_job="$job_id"
  break
done

if [ -z "$next_job" ]; then
  log "no eligible production batch to run up to MAX_BATCH=$MAX_BATCH"
  exit 0
fi

source "$CONDA_SH"
conda activate "$CONDA_ENV"
log "starting runner for $next_job"
python runner/runner.py --config "$CONFIG_FILE" --no-pull
log "runner finished for $next_job"
