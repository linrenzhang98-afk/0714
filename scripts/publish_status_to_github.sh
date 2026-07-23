#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PUBLIC_STATUS_DIR="${PUBLIC_STATUS_DIR:-reports_public}"
PUBLIC_STATUS_FILE="$PUBLIC_STATUS_DIR/platform_status.md"

cd "$REPO_DIR"

git pull --ff-only

mkdir -p "$PUBLIC_STATUS_DIR"

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

git add "$PUBLIC_STATUS_FILE"

if [ -d decision_requests ]; then
  find decision_requests -maxdepth 1 -type f -name "*.md" -print0 | xargs -0 --no-run-if-empty git add
fi

if git diff --cached --quiet; then
  echo "No public status changes to publish."
  exit 0
fi

git commit -m "Update public analysis status"
git push
