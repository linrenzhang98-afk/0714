#!/usr/bin/env bash
set -euo pipefail
ROOT=/mnt/disk1; B=$ROOT/0714_control/bootstrap; R=$ROOT/0714_control/repo; P=$ROOT/0714_control/handoff_repo; H=$ROOT/0714_handoff/20260822T160000Z-prjca046985-source-inventory; PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
[[ "$(hostname)" == ETYY && "$(id -un)" == suma ]] || exit 2
git -C "$B" fetch origin main; git -C "$B" checkout --detach origin/main
git -C "$R" fetch origin main; git -C "$R" checkout --detach origin/main
mkdir -p "$H"; "$PY" "$B/scripts/inventory_prjca046985_sources.py" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$H" "$R/jobs/20260822T120000Z-prjca046985-native-kraken2-pilot.json"; "$PY" "$B/scripts/validate_prjca046985_source_inventory.py" "$H/source_inventory.json" "$H/source_inventory_summary.json"; echo 'INVENTORY_ONLY_NO_KRAKEN2'
if [[ ! -d "$P/.git" ]]; then git clone git@github.com:linrenzhang98-afk/0714.git "$P"; git -C "$P" checkout --orphan etty-handoff; else git -C "$P" fetch origin etty-handoff; git -C "$P" checkout etty-handoff; fi
"$PY" "$B/scripts/publish_prjca046985_source_inventory_handoff.py" "$H" "$P"
