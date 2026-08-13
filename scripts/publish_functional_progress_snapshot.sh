#!/usr/bin/env bash
set -euo pipefail

# Publish only the small HUMAnN functional-progress status files without
# touching the repository's normal index, current branch, or working tree.
# This is intentionally independent from the long-running analysis worker.

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
STATUS_DIR="${FUNCTIONAL_PUBLIC_DIR:-reports_public/metagenome_functional_profile}"
LOCK_DIR="${FUNCTIONAL_STATUS_SNAPSHOT_LOCK_DIR:-.runner_state/functional_status_snapshot.lock}"
REMOTE="${FUNCTIONAL_STATUS_REMOTE:-origin}"
BRANCH="${FUNCTIONAL_STATUS_BRANCH:-main}"

cd "$REPO_DIR"
mkdir -p .runner_state

clear_own_lock() {
  if [ -d "$LOCK_DIR" ]; then
    if [ -f "$LOCK_DIR/pid" ]; then
      rm -f "$LOCK_DIR/pid"
    fi
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

if mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "$$" > "$LOCK_DIR/pid"
else
  if [ -f "$LOCK_DIR/pid" ]; then
    ACTIVE_PID="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
    if [ -n "$ACTIVE_PID" ] && kill -0 "$ACTIVE_PID" 2>/dev/null; then
      echo "functional_status_snapshot=already_running pid=$ACTIVE_PID"
      exit 0
    fi
  fi
  if [ -f "$LOCK_DIR/pid" ]; then
    rm -f "$LOCK_DIR/pid"
  fi
  rmdir "$LOCK_DIR" 2>/dev/null || true
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "functional_status_snapshot=lock_unavailable"
    exit 0
  fi
  echo "$$" > "$LOCK_DIR/pid"
fi
trap clear_own_lock EXIT INT TERM

SUMMARY="$STATUS_DIR/summary.json"
if [ ! -s "$SUMMARY" ]; then
  echo "functional_status_snapshot=no_summary"
  exit 0
fi

# Never publish a partially written JSON summary.
python3 - "$SUMMARY" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
json.loads(path.read_text(encoding="utf-8"))
PY

STATUS_FILES=(
  "$STATUS_DIR/summary.json"
  "$STATUS_DIR/summary.md"
  "$STATUS_DIR/run_status.tsv"
  "$STATUS_DIR/runner_status.txt"
  "$STATUS_DIR/launcher_status.txt"
  "$STATUS_DIR/worker_return_code.txt"
  "$STATUS_DIR/method_provenance.json"
)

publish_once() {
  git fetch "$REMOTE" "$BRANCH" --quiet
  local base_commit base_tree index_file new_tree commit_sha path
  base_commit="$(git rev-parse "$REMOTE/$BRANCH")"
  base_tree="$(git rev-parse "$base_commit^{tree}")"
  index_file="$(mktemp "$REPO_DIR/.runner_state/functional_status_index.XXXXXX")"
  rm -f "$index_file"

  cleanup_index() {
    rm -f "$index_file"
  }
  trap 'cleanup_index; clear_own_lock' EXIT INT TERM

  GIT_INDEX_FILE="$index_file" git read-tree "$base_commit"
  for path in "${STATUS_FILES[@]}"; do
    if [ -f "$path" ]; then
      GIT_INDEX_FILE="$index_file" git add -f -- "$path"
    fi
  done
  new_tree="$(GIT_INDEX_FILE="$index_file" git write-tree)"

  if [ "$new_tree" = "$base_tree" ]; then
    cleanup_index
    trap clear_own_lock EXIT INT TERM
    echo "functional_status_snapshot=no_change"
    return 0
  fi

  commit_sha="$(printf 'Update functional analysis progress\n' | git commit-tree "$new_tree" -p "$base_commit")"
  cleanup_index
  trap clear_own_lock EXIT INT TERM

  if git push "$REMOTE" "$commit_sha:refs/heads/$BRANCH" >/dev/null 2>&1; then
    echo "functional_status_snapshot=published commit=$commit_sha"
    return 0
  fi
  return 1
}

for attempt in 1 2 3; do
  if publish_once; then
    exit 0
  fi
  echo "functional_status_snapshot=push_race attempt=$attempt" >&2
  sleep 2
done

echo "functional_status_snapshot=failed_after_retries" >&2
exit 2
