#!/usr/bin/env bash
set -euo pipefail
usage(){ echo "usage: $0 --commit SHA --job JOB_JSON [--out LOCAL_HANDOFF] [--preflight-only]"; }
COMMIT=""; JOB=""; LOCAL_OUT=""; PREFLIGHT_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit) COMMIT="$2"; shift 2 ;;
    --job) JOB="$2"; shift 2 ;;
    --out) LOCAL_OUT="$2"; shift 2 ;;
    --preflight-only) PREFLIGHT_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ -n "$COMMIT" && -n "$JOB" ]] || { usage >&2; exit 2; }
ROOT=$(git rev-parse --show-toplevel)
[[ "$(git rev-parse "$COMMIT^{commit}")" == "$COMMIT" ]] || { echo "commit must be a full exact SHA" >&2; exit 2; }
[[ -f "$ROOT/$JOB" ]] || { echo "job not found: $JOB" >&2; exit 2; }
[[ -z "$(git status --porcelain)" ]] || { echo "WSL worktree must be clean" >&2; exit 2; }
ssh -o BatchMode=yes suma@ETYY true
REMOTE="/mnt/disk1/0714_handoff/executions/$(basename "$JOB" .json)/$COMMIT"
ARCHIVE=$(mktemp --suffix=.tar); trap 'rm -f "$ARCHIVE"' EXIT
git archive --format=tar --output="$ARCHIVE" "$COMMIT" "$JOB" pipelines/metagenome_deep_review_runner.py
ssh -o BatchMode=yes suma@ETYY "mkdir -p '$REMOTE/repo' '$REMOTE/out'"
scp -q "$ARCHIVE" "suma@ETYY:$REMOTE.bundle.tar"
ssh -o BatchMode=yes suma@ETYY "set -euo pipefail; test \"\$(hostname)\" = ETYY; tar -xf '$REMOTE.bundle.tar' -C '$REMOTE/repo'; test -r /mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209; test -w /mnt/disk1/0714_handoff"
if [[ "$PREFLIGHT_ONLY" == 1 ]]; then echo "REMOTE_PREFLIGHT_OK $REMOTE"; exit 0; fi
ssh -o BatchMode=yes suma@ETYY "set -euo pipefail; source /home/suma/anaconda3/etc/profile.d/conda.sh; conda activate mgshotgun; cd '$REMOTE/repo'; python pipelines/metagenome_deep_review_runner.py --job '$JOB' --out '$REMOTE/out'"
LOCAL_OUT=${LOCAL_OUT:-"$ROOT/etty_handoff/$(basename "$JOB" .json)"}; mkdir -p "$LOCAL_OUT"
scp -q -r "suma@ETYY:$REMOTE/out/." "$LOCAL_OUT/"
echo "REMOTE_HANDOFF $LOCAL_OUT"
