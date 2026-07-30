#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
PYTHON_BIN="${PYTHON_BIN:-/home/suma/anaconda3/bin/python3}"
PUBLIC_STATUS_DIR="${PUBLIC_STATUS_DIR:-reports_public}"
PUBLIC_STATUS_FILE="$PUBLIC_STATUS_DIR/platform_status.md"
ENABLE_PRODUCTION_PLANNING="${ENABLE_PRODUCTION_PLANNING:-1}"
PRJNA1056765_RUNINFO="${PRJNA1056765_RUNINFO:-/mnt/disk1/public_datasets/prjna1056765_metadata/runinfo.csv}"
ENABLE_PRODUCTION_AUTOPILOT="${ENABLE_PRODUCTION_AUTOPILOT:-1}"

cd "$REPO_DIR"

git pull --ff-only

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
git push
