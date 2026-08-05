#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
PYTHON_BIN="${PYTHON_BIN:-/home/suma/anaconda3/bin/python3}"
PUBLIC_STATUS_DIR="${PUBLIC_STATUS_DIR:-reports_public}"
PUBLIC_STATUS_FILE="$PUBLIC_STATUS_DIR/platform_status.md"
ENABLE_PRODUCTION_PLANNING="${ENABLE_PRODUCTION_PLANNING:-1}"
PRJNA1056765_RUNINFO="${PRJNA1056765_RUNINFO:-/mnt/disk1/public_datasets/prjna1056765_metadata/runinfo.csv}"
ENABLE_PRODUCTION_AUTOPILOT="${ENABLE_PRODUCTION_AUTOPILOT:-1}"
PATH="/home/suma/anaconda3/envs/mgshotgun/bin:/home/suma/anaconda3/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
export PATH

cd "$REPO_DIR"

git pull --ff-only || git pull --rebase

mkdir -p "$PUBLIC_STATUS_DIR"

if [ "$ENABLE_PRODUCTION_PLANNING" = "1" ] && [ -f "$PRJNA1056765_RUNINFO" ]; then
  "$PYTHON_BIN" scripts/plan_prjna1056765_production_samples.py \
    --runinfo "$PRJNA1056765_RUNINFO" \
    --out-dir "$PUBLIC_STATUS_DIR/production_planning/prjna1056765" \
    --max-size-mb 1000
fi

if [ "$ENABLE_PRODUCTION_AUTOPILOT" = "1" ] && [ -f scripts/autopilot_production_batches.sh ]; then
  MAX_BATCH=20 bash scripts/autopilot_production_batches.sh
fi

if [ -f scripts/summarize_metagenome_pilot.py ] && find results -maxdepth 1 -type d -name "20260724T170118Z-prjna1056765-production-descriptive-batch-*" | grep -q .; then
  "$PYTHON_BIN" scripts/summarize_metagenome_pilot.py \
    --results-root results \
    --pattern "20260724T170118Z-prjna1056765-production-descriptive-batch-*" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_production" \
    --title "PRJNA1056765 Production First-Pass Summary"
fi

if [ -f scripts/plan_second_stage_metagenome.py ] && [ -f "$PUBLIC_STATUS_DIR/metagenome_production/second_stage_candidates.tsv" ]; then
  "$PYTHON_BIN" scripts/plan_second_stage_metagenome.py \
    --candidates "$PUBLIC_STATUS_DIR/metagenome_production/second_stage_candidates.tsv" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_second_stage"
fi

if [ -f scripts/select_deep_review_metagenome_samples.py ] && [ -f "$PUBLIC_STATUS_DIR/metagenome_second_stage/shortlist.tsv" ]; then
  "$PYTHON_BIN" scripts/select_deep_review_metagenome_samples.py \
    --shortlist "$PUBLIC_STATUS_DIR/metagenome_second_stage/shortlist.tsv" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_deep_review"
fi

if [ -f scripts/publish_deep_review_run_status.py ] && [ -d results/20260731T000000Z-prjna1056765-metagenome-deep-review-plan ]; then
  "$PYTHON_BIN" scripts/publish_deep_review_run_status.py \
    --result-dir results/20260731T000000Z-prjna1056765-metagenome-deep-review-plan \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_deep_review_run"
fi

if [ -f scripts/summarize_deep_review_results.py ] && [ -f "$PUBLIC_STATUS_DIR/metagenome_deep_review_run/run_status.tsv" ]; then
  "$PYTHON_BIN" scripts/summarize_deep_review_results.py \
    --result-dir results/20260731T000000Z-prjna1056765-metagenome-deep-review-plan \
    --baseline "$PUBLIC_STATUS_DIR/metagenome_deep_review/deep_review_samples.tsv" \
    --run-status "$PUBLIC_STATUS_DIR/metagenome_deep_review_run/run_status.tsv" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_deep_review_summary"
fi

if [ "${ENABLE_NEXT_STAGE_DB_SETUP:-1}" = "1" ] && [ -f scripts/setup_metagenome_next_stage_databases.py ]; then
  SETUP_OUT_DIR="$PUBLIC_STATUS_DIR/metagenome_next_stage_setup"
  mkdir -p "$SETUP_OUT_DIR"
  if [ -f "$SETUP_OUT_DIR/setup_status.json" ] \
    && grep -q '"host_index_ready": true' "$SETUP_OUT_DIR/setup_status.json" \
    && grep -q '"amrfinder_db_ready": true' "$SETUP_OUT_DIR/setup_status.json"; then
    echo "$(date -Is) next-stage database setup already complete" > "$SETUP_OUT_DIR/setup_runner_status.txt"
  else
    echo "$(date -Is) next-stage database setup running in foreground" > "$SETUP_OUT_DIR/setup_runner_status.txt"
    if command -v timeout >/dev/null 2>&1; then
      timeout 3600 "$PYTHON_BIN" scripts/setup_metagenome_next_stage_databases.py \
        --host-index-root /mnt/disk1/db/host_indexes \
        --amr-root /mnt/disk1/db/amr \
        --out-dir "$SETUP_OUT_DIR" \
        --log "$SETUP_OUT_DIR/setup_log.jsonl" \
        > "$SETUP_OUT_DIR/setup_nohup.log" 2>&1 \
        || echo "Next-stage database setup reported errors or timed out; continuing status publication."
    else
      "$PYTHON_BIN" scripts/setup_metagenome_next_stage_databases.py \
        --host-index-root /mnt/disk1/db/host_indexes \
        --amr-root /mnt/disk1/db/amr \
        --out-dir "$SETUP_OUT_DIR" \
        --log "$SETUP_OUT_DIR/setup_log.jsonl" \
        > "$SETUP_OUT_DIR/setup_nohup.log" 2>&1 \
        || echo "Next-stage database setup reported errors; continuing status publication."
    fi
  fi
fi

if [ -f scripts/plan_metagenome_next_stage.py ] && [ -f "$PUBLIC_STATUS_DIR/metagenome_deep_review/deep_review_samples.tsv" ]; then
  "$PYTHON_BIN" scripts/plan_metagenome_next_stage.py \
    --deep-review "$PUBLIC_STATUS_DIR/metagenome_deep_review/deep_review_samples.tsv" \
    --summary "$PUBLIC_STATUS_DIR/metagenome_deep_review_summary/summary.json" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_next_stage"
fi

DEEP_REVIEW_JOB_ID="20260731T000000Z-prjna1056765-metagenome-deep-review-plan"
DEEP_REVIEW_ALLOWLIST_REQUEST="decision_requests/metagenome_deep_review_allowlist.md"
if [ -f "jobs/${DEEP_REVIEW_JOB_ID}.json" ]; then
  if "$PYTHON_BIN" - .runner_state/runner_state.json "$DEEP_REVIEW_JOB_ID" <<'PY'
import json
import sys

state_path, job_id = sys.argv[1], sys.argv[2]
try:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
except FileNotFoundError:
    sys.exit(1)
job = state.get("jobs", {}).get(job_id, {})
sys.exit(0 if job.get("status") == "done" else 1)
PY
  then
    rm -f "$DEEP_REVIEW_ALLOWLIST_REQUEST"
  else
    mkdir -p decision_requests
    cat > "$DEEP_REVIEW_ALLOWLIST_REQUEST" <<'EOF'
# Allowlist metagenome_deep_review

The next deep-review step is a guarded planning job. It validates the 30 selected runs and writes `run_plan.sh`; it does not execute heavy analysis.

If this task is not yet in `runner/config.local.json`, add:

```json
"metagenome_deep_review": {
  "script": "/mnt/disk1/db/kraken2/0714/pipelines/metagenome_deep_review_runner.py",
  "timeout_seconds": 3600
}
```

This is required before `jobs/20260731T000000Z-prjna1056765-metagenome-deep-review-plan.json` can run.
EOF
  fi
fi

"$PYTHON_BIN" scripts/write_status_summary.py \
  --state .runner_state/runner_state.json \
  --log .runner_logs/runner.jsonl \
  --out "$PUBLIC_STATUS_FILE"

{
  echo
  echo "## Public Safety Note"
  echo
  echo "This summary is intentionally compact. Raw FASTQ files, databases, full results, local runner config, and private logs are not committed."
} >> "$PUBLIC_STATUS_FILE"

git add "$PUBLIC_STATUS_DIR"

if [ -d decision_requests ]; then
  find decision_requests -maxdepth 1 -type f -name "*.md" -print0 | xargs -0 --no-run-if-empty git add
fi

if git diff --cached --quiet; then
  echo "No public status changes to publish."
  exit 0
fi

git commit -m "Update public analysis status"
git pull --rebase
git push
