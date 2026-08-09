#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/disk1/db/kraken2/0714}"
PYTHON_BIN="${PYTHON_BIN:-/home/suma/anaconda3/bin/python3}"
PUBLIC_STATUS_DIR="${PUBLIC_STATUS_DIR:-reports_public}"
RUN_STATUS="${FUNCTIONAL_RUN_STATUS:-$PUBLIC_STATUS_DIR/metagenome_host_amr_screen/run_status.tsv}"
RESULT_DIR="${FUNCTIONAL_RESULT_DIR:-results/20260809T000000Z-prjna1056765-functional-profile}"
PUBLIC_DIR="${FUNCTIONAL_PUBLIC_DIR:-$PUBLIC_STATUS_DIR/metagenome_functional_profile}"
DB_ROOT="${HUMANN_DB_ROOT:-/mnt/disk1/db/humann}"
FUNCTIONAL_ENV_PREFIX="${HUMANN_FUNCTIONAL_ENV_PREFIX:-/home/suma/anaconda3/envs/humann-shotgun}"
THREADS="${FUNCTIONAL_THREADS:-4}"
MAX_SAMPLES="${FUNCTIONAL_MAX_SAMPLES:-30}"
LOCK_DIR="${FUNCTIONAL_LOCK_DIR:-.runner_state/metagenome_functional_profile.lock}"
AUTO_INSTALL="${ENABLE_FUNCTIONAL_AUTO_INSTALL:-1}"
AUTO_DOWNLOAD_DBS="${ENABLE_FUNCTIONAL_AUTO_DOWNLOAD_DBS:-1}"

cd "$REPO_DIR"
mkdir -p "$PUBLIC_DIR" "$RESULT_DIR" .runner_state

write_status() {
  local state="$1"
  local reason="$2"
  {
    echo "generated_at=$(date -Is)"
    echo "state=$state"
    echo "reason=$reason"
    echo "result_dir=$RESULT_DIR"
    echo "public_dir=$PUBLIC_DIR"
    echo "run_status_exists=$([ -f "$RUN_STATUS" ] && echo true || echo false)"
    echo "worker_script_exists=$([ -f scripts/run_metagenome_functional_profile.py ] && echo true || echo false)"
    echo "lock_dir=$LOCK_DIR"
  } > "$PUBLIC_DIR/runner_status.txt"
}

if [ -f "$PUBLIC_DIR/summary.json" ] && grep -q '"state": "done"' "$PUBLIC_DIR/summary.json"; then
  write_status "done" "functional profile already complete"
  exit 0
fi

if [ ! -f "$RUN_STATUS" ]; then
  write_status "blocked" "host-AMR run_status.tsv is missing"
  exit 0
fi

if [ ! -f scripts/run_metagenome_functional_profile.py ]; then
  write_status "blocked" "worker script missing"
  exit 0
fi

if mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "$$" > "$LOCK_DIR/pid"
  AUTO_FLAGS=()
  if [ "$AUTO_INSTALL" = "1" ]; then
    AUTO_FLAGS+=(--auto-install)
  fi
  if [ "$AUTO_DOWNLOAD_DBS" = "1" ]; then
    AUTO_FLAGS+=(--auto-download-dbs)
  fi
  write_status "running" "functional profiling worker running in foreground pid=$$"
  set +e
  "$PYTHON_BIN" scripts/run_metagenome_functional_profile.py \
    --run-status "$RUN_STATUS" \
    --out-dir "$RESULT_DIR" \
    --public-dir "$PUBLIC_DIR" \
    --db-root "$DB_ROOT" \
    --functional-env-prefix "$FUNCTIONAL_ENV_PREFIX" \
    --threads "$THREADS" \
    --max-samples "$MAX_SAMPLES" \
    "${AUTO_FLAGS[@]}" \
    > "$PUBLIC_DIR/worker.nohup.log" 2>&1
  WORKER_RC=$?
  set -e
  echo "$WORKER_RC" > "$PUBLIC_DIR/worker_return_code.txt"
  rm -rf "$LOCK_DIR"
  if [ "$WORKER_RC" -eq 0 ]; then
    write_status "done" "functional profiling worker completed"
  else
    write_status "blocked_or_failed" "functional profiling worker exited rc=$WORKER_RC"
  fi
else
  if [ -f "$LOCK_DIR/pid" ]; then
    PID="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
      write_status "running" "functional profiling worker is still active pid=$PID"
      exit 0
    fi
  fi
  rm -rf "$LOCK_DIR"
  write_status "stale_lock_cleared" "cleared stale functional profiling lock; next timer will restart"
fi
