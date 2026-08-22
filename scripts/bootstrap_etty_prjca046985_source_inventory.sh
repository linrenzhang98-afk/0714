#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/disk1; B=$ROOT/0714_control/bootstrap; R=$ROOT/0714_control/repo; P=$ROOT/0714_control/handoff_repo; H=$ROOT/0714_handoff/20260822T160000Z-prjca046985-source-inventory; PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
[[ "$(hostname)" == ETYY && "$(id -un)" == suma ]] || exit 2
git -C "$B" fetch origin main; git -C "$B" checkout --detach origin/main
CONTROL_MAIN_COMMIT="$(git -C "$B" rev-parse HEAD)"; export CONTROL_MAIN_COMMIT
git -C "$R" fetch origin main; git -C "$R" checkout --detach "$CONTROL_MAIN_COMMIT"
mkdir -p "$H"; "$PY" "$R/scripts/inventory_prjca046985_sources.py" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$H" "$R/jobs/20260822T160000Z-prjca046985-source-inventory.json"; "$PY" "$R/scripts/validate_prjca046985_source_inventory.py" "$H/source_inventory.json" "$H/source_inventory_summary.json" "$H/provenance.json" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$R/jobs/20260822T160000Z-prjca046985-source-inventory.json"
if [[ ! -d "$P/.git" ]]; then git clone git@github.com:linrenzhang98-afk/0714.git "$P"; git -C "$P" fetch origin etty-handoff; git -C "$P" checkout -B etty-handoff origin/etty-handoff; else git -C "$P" fetch origin etty-handoff; git -C "$P" checkout etty-handoff; git -C "$P" merge --ff-only origin/etty-handoff; fi
"$PY" "$R/scripts/publish_prjca046985_source_inventory_handoff.py" "$H" "$P" "$R"
