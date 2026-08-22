#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/disk1; B=$ROOT/0714_control/bootstrap; R=$ROOT/0714_control/repo; P=$ROOT/0714_control/handoff_repo; H=$ROOT/0714_handoff/20260822T160000Z-prjca046985-source-inventory; PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
[[ "$(hostname)" == ETYY && "$(id -un)" == suma ]] || exit 2
git -C "$B" fetch origin main; git -C "$B" checkout --detach origin/main
CONTROL_MAIN_COMMIT="$(git -C "$B" rev-parse HEAD)"; export CONTROL_MAIN_COMMIT
git -C "$R" fetch origin main; git -C "$R" checkout --detach "$CONTROL_MAIN_COMMIT"
INVENTORY_JOB="$R/jobs/20260822T160000Z-prjca046985-source-inventory.json"; [[ -f "$INVENTORY_JOB" ]]
PILOT_JOB_REL="$($PY -c 'import json,sys; j=json.load(open(sys.argv[1])); assert j["job_id"]=="20260822T160000Z-prjca046985-source-inventory"; print(j["params"]["pilot_job"])' "$INVENTORY_JOB")"
PILOT_JOB="$R/$PILOT_JOB_REL"; [[ -f "$PILOT_JOB" ]]
"$PY" -c 'import json,sys; j=json.load(open(sys.argv[1])); assert j["job_id"]=="20260822T120000Z-prjca046985-native-kraken2-pilot"; assert len(j["params"]["pilot_runs"])==8' "$PILOT_JOB"
mkdir -p "$H"; "$PY" "$R/scripts/inventory_prjca046985_sources.py" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$H" "$PILOT_JOB"; "$PY" "$R/scripts/validate_prjca046985_source_inventory.py" "$H/source_inventory.json" "$H/source_inventory_summary.json" "$H/provenance.json" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$PILOT_JOB"
if [[ ! -d "$P/.git" ]]; then git clone git@github.com:linrenzhang98-afk/0714.git "$P"; git -C "$P" fetch origin etty-handoff; git -C "$P" checkout -B etty-handoff origin/etty-handoff; else git -C "$P" fetch origin etty-handoff; git -C "$P" checkout etty-handoff; git -C "$P" merge --ff-only origin/etty-handoff; fi
"$PY" "$R/scripts/publish_prjca046985_source_inventory_handoff.py" "$H" "$P" "$R"
