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

git pull --ff-only

mkdir -p "$PUBLIC_STATUS_DIR"

if [ "$ENABLE_PRODUCTION_PLANNING" = "1" ] && [ -f "$PRJNA1056765_RUNINFO" ]; then
  "$PYTHON_BIN" scripts/plan_prjna1056765_production_samples.py \
    --runinfo "$PRJNA1056765_RUNINFO" \
    --out-dir "$PUBLIC_STATUS_DIR/production_planning/prjna1056765" \
    --max-size-mb 1000
fi

EXTERNAL_PILOT_JOB="20260821T100000Z-prjca046985-bounded-technical-pilot"
EXTERNAL_PILOT_RESULT="results/$EXTERNAL_PILOT_JOB"
EXTERNAL_PILOT_PUBLIC="$PUBLIC_STATUS_DIR/prjna1056765_external_cohort_pilot_package/hospital_pilot_result"
if [ -f "$EXTERNAL_PILOT_RESULT/pilot_summary.json" ]; then
  mkdir -p "$EXTERNAL_PILOT_PUBLIC"
  cp "$EXTERNAL_PILOT_RESULT/pilot_summary.json" "$EXTERNAL_PILOT_PUBLIC/pilot_summary.json"
  find "$EXTERNAL_PILOT_RESULT" -maxdepth 2 -type f \( -name '*.kreport' -o -name '*.bracken.species.tsv' -o -name '*.log' -o -name 'hospital_readonly_inventory.json' -o -name 'bracken_redistributions.tsv' \) -print0 \
    | while IFS= read -r -d '' source; do
        relative="${source#$EXTERNAL_PILOT_RESULT/}"
        mkdir -p "$EXTERNAL_PILOT_PUBLIC/$(dirname "$relative")"
        cp "$source" "$EXTERNAL_PILOT_PUBLIC/$relative"
      done
  {
    echo "generated_at=$(date -Is)"
    echo "state=complete"
    echo "source_job=$EXTERNAL_PILOT_JOB"
  } > "$EXTERNAL_PILOT_PUBLIC/status.txt"
elif [ -f "jobs/$EXTERNAL_PILOT_JOB.json" ]; then
  mkdir -p "$EXTERNAL_PILOT_PUBLIC"
  {
    echo "generated_at=$(date -Is)"
    echo "state=pending"
    echo "source_job=$EXTERNAL_PILOT_JOB"
  } > "$EXTERNAL_PILOT_PUBLIC/status.txt"
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

if [ "${ENABLE_GENERAL_RUNNER:-1}" = "1" ] && [ -f runner/config.local.json ] && [ -f runner/runner.py ]; then
  GENERAL_RUNNER_STATUS="$PUBLIC_STATUS_DIR/general_runner_status.txt"
  GENERAL_RUNNER_LOG="$PUBLIC_STATUS_DIR/general_runner_last.log"
  {
    echo "generated_at=$(date -Is)"
    echo "enabled=true"
    echo "config_exists=true"
    echo "runner_exists=true"
    echo "host_amr_job_files=$(find jobs -maxdepth 1 -type f -name '20260807T000000Z-prjna1056765-host-amr-screen-*.json' | wc -l)"
    echo "prjna511633_amplicon_job_files=$(find jobs -maxdepth 1 -type f -name '*prjna511633*16s*.json' | wc -l)"
    if "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("runner/config.local.json").read_text(encoding="utf-8"))
tasks = config.get("tasks", {})
print("metagenome_deep_review_allowlisted=" + str("metagenome_deep_review" in tasks).lower())
print("amplicon_qiime2_allowlisted=" + str("amplicon_qiime2" in tasks).lower())
print("jobs_glob=" + str(config.get("jobs_glob", "")))
print("results_root=" + str(config.get("results_root", "")))
PY
    then
      :
    else
      echo "config_parse_ok=false"
    fi
  } > "$GENERAL_RUNNER_STATUS"

  set +e
  "$PYTHON_BIN" runner/runner.py --config runner/config.local.json --no-pull \
    > "$GENERAL_RUNNER_LOG" 2>&1
  GENERAL_RUNNER_RC=$?
  set -e
  {
    echo "runner_return_code=$GENERAL_RUNNER_RC"
    echo "runner_log_tail_start"
    tail -n 40 "$GENERAL_RUNNER_LOG" 2>/dev/null || true
    echo "runner_log_tail_end"
  } >> "$GENERAL_RUNNER_STATUS"
  if [ "$GENERAL_RUNNER_RC" -ne 0 ]; then
    echo "General runner reported errors; continuing status publication."
  fi
elif [ "${ENABLE_GENERAL_RUNNER:-1}" = "1" ]; then
  {
    echo "generated_at=$(date -Is)"
    echo "enabled=true"
    echo "config_exists=$([ -f runner/config.local.json ] && echo true || echo false)"
    echo "runner_exists=$([ -f runner/runner.py ] && echo true || echo false)"
    echo "host_amr_job_files=$(find jobs -maxdepth 1 -type f -name '20260807T000000Z-prjna1056765-host-amr-screen-*.json' | wc -l)"
    echo "prjna511633_amplicon_job_files=$(find jobs -maxdepth 1 -type f -name '*prjna511633*16s*.json' | wc -l)"
    echo "runner_return_code=not_run"
  } > "$PUBLIC_STATUS_DIR/general_runner_status.txt"
fi

READONLY_INVENTORY_RESULT="results/20260821T070000Z-external-cohort-readonly-inventory"
READONLY_INVENTORY_PUBLIC="$PUBLIC_STATUS_DIR/prjna1056765_external_cohort_pilot_package/hospital_runner_inventory"
if [ -f "$READONLY_INVENTORY_RESULT/hospital_readonly_inventory.json" ]; then
  mkdir -p "$READONLY_INVENTORY_PUBLIC"
  cp "$READONLY_INVENTORY_RESULT/hospital_readonly_inventory.json" "$READONLY_INVENTORY_PUBLIC/hospital_readonly_inventory.json"
  cp "$READONLY_INVENTORY_RESULT/bracken_redistributions.tsv" "$READONLY_INVENTORY_PUBLIC/bracken_redistributions.tsv"
  {
    echo "generated_at=$(date -Is)"
    echo "state=complete"
    echo "source_job=20260821T070000Z-external-cohort-readonly-inventory"
  } > "$READONLY_INVENTORY_PUBLIC/status.txt"
elif [ -f jobs/20260821T070000Z-external-cohort-readonly-inventory.json ]; then
  mkdir -p "$READONLY_INVENTORY_PUBLIC"
  {
    echo "generated_at=$(date -Is)"
    echo "state=pending"
    echo "source_job=20260821T070000Z-external-cohort-readonly-inventory"
  } > "$READONLY_INVENTORY_PUBLIC/status.txt"
fi

if [ -f scripts/summarize_host_amr_screen.py ] \
  && find results -maxdepth 1 -type d -name "20260807T000000Z-prjna1056765-host-amr-screen-*" | grep -q .; then
  "$PYTHON_BIN" scripts/summarize_host_amr_screen.py \
    --results-root results \
    --pattern "20260807T000000Z-prjna1056765-host-amr-screen-*" \
    --out-dir "$PUBLIC_STATUS_DIR/metagenome_host_amr_screen"
fi

if [ -f scripts/summarize_shotgun_standard.py ] \
  && [ -f "$PUBLIC_STATUS_DIR/metagenome_host_amr_screen/run_status.tsv" ]; then
  SHOTGUN_STANDARD_DIR="$PUBLIC_STATUS_DIR/metagenome_standard_shotgun"
  SHOTGUN_STANDARD_LOG="$SHOTGUN_STANDARD_DIR/runner.log"
  mkdir -p "$SHOTGUN_STANDARD_DIR"
  set +e
  "$PYTHON_BIN" scripts/summarize_shotgun_standard.py \
    --run-status "$PUBLIC_STATUS_DIR/metagenome_host_amr_screen/run_status.tsv" \
    --out-dir "$SHOTGUN_STANDARD_DIR" \
    > "$SHOTGUN_STANDARD_LOG" 2>&1
  SHOTGUN_STANDARD_RC=$?
  set -e
  {
    echo "generated_at=$(date -Is)"
    echo "runner_return_code=$SHOTGUN_STANDARD_RC"
    echo "summary_md_exists=$([ -f "$SHOTGUN_STANDARD_DIR/summary.md" ] && echo true || echo false)"
    echo "qc_summary_exists=$([ -f "$SHOTGUN_STANDARD_DIR/qc_host_removal_summary.tsv" ] && echo true || echo false)"
    echo "species_matrix_exists=$([ -f "$SHOTGUN_STANDARD_DIR/species_relative_abundance_matrix.tsv" ] && echo true || echo false)"
    echo "alpha_diversity_exists=$([ -f "$SHOTGUN_STANDARD_DIR/alpha_diversity.tsv" ] && echo true || echo false)"
    echo "beta_distance_exists=$([ -f "$SHOTGUN_STANDARD_DIR/bray_curtis_distance_matrix.tsv" ] && echo true || echo false)"
    echo "differentials_exists=$([ -f "$SHOTGUN_STANDARD_DIR/species_group_differentials.tsv" ] && echo true || echo false)"
  } > "$SHOTGUN_STANDARD_DIR/runner_status.txt"
  if [ "$SHOTGUN_STANDARD_RC" -ne 0 ]; then
    echo "Standard shotgun summary reported errors; continuing status publication."
  fi
fi

if [ "${ENABLE_METAGENOME_FUNCTIONAL_PROFILE:-1}" = "1" ] \
  && [ -f scripts/autopilot_metagenome_functional_profile.sh ]; then
  FUNCTIONAL_PROFILE_PUBLIC_DIR="$PUBLIC_STATUS_DIR/metagenome_functional_profile"
  mkdir -p "$FUNCTIONAL_PROFILE_PUBLIC_DIR"
  set +e
  bash scripts/autopilot_metagenome_functional_profile.sh \
    > "$FUNCTIONAL_PROFILE_PUBLIC_DIR/autopilot_launcher.log" 2>&1
  FUNCTIONAL_PROFILE_RC=$?
  set -e
  {
    echo "generated_at=$(date -Is)"
    echo "launcher_return_code=$FUNCTIONAL_PROFILE_RC"
    echo "summary_md_exists=$([ -f "$FUNCTIONAL_PROFILE_PUBLIC_DIR/summary.md" ] && echo true || echo false)"
    echo "summary_json_exists=$([ -f "$FUNCTIONAL_PROFILE_PUBLIC_DIR/summary.json" ] && echo true || echo false)"
    echo "run_status_exists=$([ -f "$FUNCTIONAL_PROFILE_PUBLIC_DIR/run_status.tsv" ] && echo true || echo false)"
    echo "runner_status_exists=$([ -f "$FUNCTIONAL_PROFILE_PUBLIC_DIR/runner_status.txt" ] && echo true || echo false)"
  } > "$FUNCTIONAL_PROFILE_PUBLIC_DIR/launcher_status.txt"
  if [ "$FUNCTIONAL_PROFILE_RC" -ne 0 ]; then
    echo "Functional profile launcher reported errors; continuing status publication."
  fi
fi

# Run only the fixed-30 lightweight HUMAnN downstream stage. Its own audit gate
# prevents analysis unless the 90 real hospital-side final files pass QC.
if [ "${ENABLE_HUMANN_30_DOWNSTREAM:-1}" = "1" ] \
  && [ -f scripts/autopilot_humann_30_downstream.sh ]; then
  mkdir -p "$PUBLIC_STATUS_DIR/metagenome_humann_30_downstream"
  set +e
  bash scripts/autopilot_humann_30_downstream.sh \
    > "$PUBLIC_STATUS_DIR/metagenome_humann_30_downstream/autopilot_launcher.log" 2>&1
  HUMANN_30_DOWNSTREAM_RC=$?
  set -e
  echo "launcher_return_code=$HUMANN_30_DOWNSTREAM_RC" \
    >> "$PUBLIC_STATUS_DIR/metagenome_humann_30_downstream/runner_status.txt"
fi

AMP_PRJNA511633_RESULT_DIR="results/20260808T143000Z-prjna511633-icpp-16s-single-reverse-retry"
AMP_PRJNA511633_PUBLIC_DIR="$PUBLIC_STATUS_DIR/amplicon_precocious_puberty_prjna511633"
mkdir -p "$AMP_PRJNA511633_PUBLIC_DIR"
{
  echo "generated_at=$(date -Is)"
  echo "target_result_dir=$AMP_PRJNA511633_RESULT_DIR"
  echo "target_job_id=20260808T143000Z-prjna511633-icpp-16s-single-reverse-retry"
} > "$AMP_PRJNA511633_PUBLIC_DIR/current_target.txt"

if [ -f scripts/summarize_amplicon_prjna511633_status.py ]; then
  rm -f "$PUBLIC_STATUS_DIR/amplicon_precocious_puberty_prjna511633/status.md" \
        "$PUBLIC_STATUS_DIR/amplicon_precocious_puberty_prjna511633/status.json"
  "$PYTHON_BIN" scripts/summarize_amplicon_prjna511633_status.py \
    --result-dir "$AMP_PRJNA511633_RESULT_DIR" \
    --out-dir "$AMP_PRJNA511633_PUBLIC_DIR"
fi

if [ -f scripts/summarize_amplicon_qc_depth.py ]; then
  "$PYTHON_BIN" scripts/summarize_amplicon_qc_depth.py \
    --result-dir "$AMP_PRJNA511633_RESULT_DIR" \
    --metadata "$AMP_PRJNA511633_PUBLIC_DIR/sample_metadata.tsv" \
    --qiime-bin /home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime \
    --out-dir "$AMP_PRJNA511633_PUBLIC_DIR/depth_qc"
fi

if [ -f scripts/summarize_amplicon_prjna511633_results.py ]; then
  AMP_PUBLICATION_LOG="$AMP_PRJNA511633_PUBLIC_DIR/publication_summary_runner.log"
  set +e
  "$PYTHON_BIN" scripts/summarize_amplicon_prjna511633_results.py \
    --result-dir "$AMP_PRJNA511633_RESULT_DIR" \
    --metadata "$AMP_PRJNA511633_PUBLIC_DIR/sample_metadata.tsv" \
    --qiime-bin /home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime \
    --out-dir "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary" \
    > "$AMP_PUBLICATION_LOG" 2>&1
  AMP_PUBLICATION_RC=$?
  set -e
  {
    echo "generated_at=$(date -Is)"
    echo "runner_return_code=$AMP_PUBLICATION_RC"
    echo "summary_md_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/summary.md" ] && echo true || echo false)"
    echo "alpha_summary_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/alpha_diversity_group_summary.tsv" ] && echo true || echo false)"
    echo "genus_differentials_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/genus_group_differentials.tsv" ] && echo true || echo false)"
    echo "species_differentials_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/species_group_differentials.tsv" ] && echo true || echo false)"
  } > "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary_runner_status.txt"
  if [ "$AMP_PUBLICATION_RC" -ne 0 ]; then
    echo "PRJNA511633 publication summary reported errors; continuing status publication."
  fi
fi

if [ -f scripts/build_amplicon_prjna511633_manuscript_pack.py ] \
  && [ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/summary.json" ]; then
  AMP_MANUSCRIPT_PACK_LOG="$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack_runner.log"
  set +e
  "$PYTHON_BIN" scripts/build_amplicon_prjna511633_manuscript_pack.py \
    --summary-dir "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary" \
    --depth-qc "$AMP_PRJNA511633_PUBLIC_DIR/depth_qc" \
    --out-dir "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack" \
    > "$AMP_MANUSCRIPT_PACK_LOG" 2>&1
  AMP_MANUSCRIPT_PACK_RC=$?
  set -e
  {
    echo "generated_at=$(date -Is)"
    echo "runner_return_code=$AMP_MANUSCRIPT_PACK_RC"
    echo "manifest_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack/manifest.json" ] && echo true || echo false)"
    echo "figure_table_plan_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack/figure_table_plan.md" ] && echo true || echo false)"
    echo "interpretation_draft_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack/results_interpretation_draft.md" ] && echo true || echo false)"
    echo "wetlab_targets_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack/wetlab_validation_targets.tsv" ] && echo true || echo false)"
    echo "review_risk_notes_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack/review_risk_notes.md" ] && echo true || echo false)"
  } > "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack_runner_status.txt"
  if [ "$AMP_MANUSCRIPT_PACK_RC" -ne 0 ]; then
    echo "PRJNA511633 manuscript pack reported errors; continuing status publication."
  fi
else
  {
    echo "generated_at=$(date -Is)"
    echo "runner_return_code=not_run"
    echo "reason=script_or_publication_summary_json_missing"
    echo "script_exists=$([ -f scripts/build_amplicon_prjna511633_manuscript_pack.py ] && echo true || echo false)"
    echo "summary_json_exists=$([ -f "$AMP_PRJNA511633_PUBLIC_DIR/publication_summary/summary.json" ] && echo true || echo false)"
  } > "$AMP_PRJNA511633_PUBLIC_DIR/manuscript_pack_runner_status.txt"
fi

PROGRESS_GOVERNOR_DIR="$PUBLIC_STATUS_DIR/progress_governor"
mkdir -p "$PROGRESS_GOVERNOR_DIR"
if [ -f scripts/write_progress_governor_status.py ]; then
  set +e
  "$PYTHON_BIN" scripts/write_progress_governor_status.py \
    --jobs-dir jobs \
    --state .runner_state/runner_state.json \
    --public-dir "$PUBLIC_STATUS_DIR" \
    --out-dir "$PROGRESS_GOVERNOR_DIR" \
    > "$PROGRESS_GOVERNOR_DIR/runner.log" 2>&1
  PROGRESS_GOVERNOR_RC=$?
  set -e
else
  PROGRESS_GOVERNOR_RC=127
  echo "scripts/write_progress_governor_status.py not found" > "$PROGRESS_GOVERNOR_DIR/runner.log"
fi
{
  echo "generated_at=$(date -Is)"
  echo "runner_return_code=$PROGRESS_GOVERNOR_RC"
  echo "status_md_exists=$([ -f "$PROGRESS_GOVERNOR_DIR/status.md" ] && echo true || echo false)"
  echo "status_json_exists=$([ -f "$PROGRESS_GOVERNOR_DIR/status.json" ] && echo true || echo false)"
} > "$PROGRESS_GOVERNOR_DIR/runner_status.txt"
if [ ! -f "$PROGRESS_GOVERNOR_DIR/status.md" ]; then
  cat > "$PROGRESS_GOVERNOR_DIR/status.md" <<'EOF'
# Progress Governor Status

Progress state: `stalled_status_generation_failed`

## Reason

- Progress governor status generation did not produce `status.md`.

## Required Next Action

- Codex should inspect `reports_public/progress_governor/runner_status.txt` and `runner.log`, then patch the smallest repository-side cause.
EOF
fi
if [ ! -f "$PROGRESS_GOVERNOR_DIR/status.json" ]; then
  cat > "$PROGRESS_GOVERNOR_DIR/status.json" <<'EOF'
{
  "progress_state": "stalled_status_generation_failed",
  "reason": "Progress governor status generation did not produce status.json.",
  "next_action": "Inspect runner_status.txt and runner.log, then patch the smallest repository-side cause."
}
EOF
fi

DEEP_REVIEW_JOB_ID="20260731T000000Z-prjna1056765-metagenome-deep-review-plan"
DEEP_REVIEW_ALLOWLIST_REQUEST="decision_requests/metagenome_deep_review_allowlist.md"
HOST_AMR_DECISION_REQUEST="decision_requests/metagenome_host_amr_requirements.md"
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

AMP_DEPTH_QC_DIR="$PUBLIC_STATUS_DIR/amplicon_precocious_puberty_prjna511633/depth_qc"
if [ -d "$AMP_DEPTH_QC_DIR" ]; then
  git add -f "$AMP_DEPTH_QC_DIR"
fi

if [ -d decision_requests ]; then
  find decision_requests -maxdepth 1 -type f -name "*.md" -print0 | xargs -0 --no-run-if-empty git add
fi
if git ls-files --error-unmatch -- "$HOST_AMR_DECISION_REQUEST" >/dev/null 2>&1; then
  git add -- "$HOST_AMR_DECISION_REQUEST"
fi

if git diff --cached --quiet; then
  echo "No public status changes to publish."
  exit 0
fi

git commit -m "Update public analysis status"
git pull --no-rebase --no-edit
git push origin main
