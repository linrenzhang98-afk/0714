#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
PYTHON_BIN="${PYTHON_BIN:-/home/suma/anaconda3/bin/python3}"
INPUT_ROOT="${HUMANN_30_INPUT_ROOT:-/mnt/disk1/db/kraken2/0714/results/20260809T000000Z-prjna1056765-functional-profile}"
COHORT="${HUMANN_30_COHORT:-reports_public/metagenome_functional_profile/run_status.tsv}"
SPECIES_MATRIX="${HUMANN_30_SPECIES_MATRIX:-reports_public/metagenome_standard_shotgun/species_relative_abundance_matrix.tsv}"
PUBLIC_DIR="${HUMANN_30_PUBLIC_DIR:-reports_public/metagenome_humann_30_downstream}"
WORK_DIR="${HUMANN_30_WORK_DIR:-results/20260814T000000Z-prjna1056765-humann-30-downstream}"
LOCK_DIR="${HUMANN_30_LOCK_DIR:-.runner_state/humann_30_downstream.lock}"

cd "$REPO_DIR"
mkdir -p "$PUBLIC_DIR" "$WORK_DIR" .runner_state

write_status() {
  {
    echo "generated_at=$(date -Is)"
    echo "state=$1"
    echo "reason=$2"
    echo "input_root=$INPUT_ROOT"
    echo "cohort=$COHORT"
    echo "public_dir=$PUBLIC_DIR"
    echo "work_dir=$WORK_DIR"
  } > "$PUBLIC_DIR/runner_status.txt"
}

if [ -f "$PUBLIC_DIR/parameters.json" ] && [ -f "$PUBLIC_DIR/checksums.tsv" ]; then
  write_status "done" "audited downstream outputs already complete"
  exit 0
fi
if [ ! -d "$INPUT_ROOT" ]; then
  write_status "INPUT_UNAVAILABLE" "hospital HUMAnN input root is not visible; downstream NOT_RUN"
  exit 0
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  write_status "running" "downstream lock exists"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

AUDIT_DIR="$PUBLIC_DIR/audit"
write_status "auditing" "real hospital-side 90-file audit running"
set +e
"$PYTHON_BIN" scripts/audit_humann_30_outputs.py \
  --input-root "$INPUT_ROOT" --cohort "$COHORT" --output-dir "$AUDIT_DIR" \
  > "$PUBLIC_DIR/audit.log" 2>&1
AUDIT_RC=$?
set -e
if [ "$AUDIT_RC" -ne 0 ]; then
  write_status "AUDIT_FAILED" "real input QC did not pass rc=$AUDIT_RC; downstream NOT_RUN"
  exit 0
fi

write_status "running" "real audit passed; lightweight downstream analysis running"
set +e
"$PYTHON_BIN" scripts/run_humann_30_downstream.py \
  --input-root "$INPUT_ROOT" --cohort "$COHORT" \
  --audit-summary "$AUDIT_DIR/audit_summary.json" \
  --species-matrix "$SPECIES_MATRIX" --out "$WORK_DIR/public" \
  > "$PUBLIC_DIR/downstream.log" 2>&1
DOWNSTREAM_RC=$?
set -e
if [ "$DOWNSTREAM_RC" -ne 0 ]; then
  write_status "DOWNSTREAM_FAILED" "lightweight downstream exited rc=$DOWNSTREAM_RC"
  exit 0
fi

MAX_PUBLIC_FILE_BYTES="${HUMANN_30_MAX_PUBLIC_FILE_BYTES:-26214400}"
MAX_PUBLIC_TOTAL_BYTES="${HUMANN_30_MAX_PUBLIC_TOTAL_BYTES:-78643200}"
LARGEST_BYTES="$(find "$WORK_DIR/public" -type f -printf '%s\n' | sort -nr | head -n 1)"
TOTAL_BYTES="$(du -sb "$WORK_DIR/public" | awk '{print $1}')"
if [ "${LARGEST_BYTES:-0}" -gt "$MAX_PUBLIC_FILE_BYTES" ] || [ "$TOTAL_BYTES" -gt "$MAX_PUBLIC_TOTAL_BYTES" ]; then
  write_status "RETURN_SIZE_LIMIT" "downstream complete locally but lightweight Git return cap exceeded; no outputs copied"
  exit 0
fi

cp -a "$WORK_DIR/public/." "$PUBLIC_DIR/"
write_status "done" "real audit and fixed-30 lightweight downstream complete"
