#!/usr/bin/env bash
set -euo pipefail
[[ "${ETTY_AGENT_TEST_MODE:-0}" == 1 || ( "$(hostname)" == ETYY && "$(id -un)" == suma ) ]] || { echo SAFE_STOP; exit 2; }
ROOT=${ETTY_AGENT_ROOT:-/mnt/disk1/0714_control}; REPO=${ETTY_AGENT_REPO:-$ROOT/agent_runtime}; Q=$ROOT/queue_repo; J=$ROOT/job_repo; H=$ROOT/handoff_repo; mkdir -p "$ROOT/state" "$ROOT/logs" "$ROOT/queue"
REMOTE=${ETTY_AGENT_REMOTE:-git@github.com:linrenzhang98-afk/0714.git}
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; BOOTSTRAP=${ETTY_AGENT_BOOTSTRAP:-"$(git -C "$SCRIPT_DIR/.." rev-parse --show-toplevel)"}
[[ -d "$REPO/.git" ]] || git clone "$REMOTE" "$REPO"
[[ -d "$Q/.git" ]] || git clone "$REMOTE" "$Q"
[[ -d "$J/.git" ]] || git clone "$REMOTE" "$J"
[[ -d "$H/.git" ]] || git clone "$REMOTE" "$H"
git -C "$H" config user.name 'ETYY Job Agent'; git -C "$H" config user.email 'etty-job-agent@localhost'
PIN="$(git -C "$BOOTSTRAP" rev-parse HEAD)"; git -C "$REPO" fetch origin "$PIN"; git -C "$REPO" cat-file -e "$PIN^{commit}"; git -C "$REPO" checkout --detach "$PIN"; test "$(git -C "$REPO" rev-parse HEAD)" = "$PIN"
mkdir -p "$Q" "$J"
mkdir -p "$HOME/.config/systemd/user"; cat > "$HOME/.config/systemd/user/etty-job-agent.service" <<EOF
[Unit]
Description=0714 ETYY reviewed job agent
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=/usr/bin/env python3 -m scripts.etty_job_agent --queue-repo $Q --job-repo $J --handoff-repo $H --state $ROOT/state/jobs.json --once
EOF
cat > "$HOME/.config/systemd/user/etty-job-agent.timer" <<'EOF'
[Unit]
Description=0714 ETYY job polling
[Timer]
OnBootSec=2min
OnUnitActiveSec=3min
Persistent=true
Unit=etty-job-agent.service
[Install]
WantedBy=timers.target
EOF
if [[ "${ETTY_AGENT_TEST_MODE:-0}" == 1 ]]; then exit 0; fi
if [[ "$(loginctl show-user suma -p Linger --value 2>/dev/null || true)" != yes ]]; then echo 'SAFE_STOP: login-independent user systemd requires Linger=yes'; exit 3; fi
systemctl --user daemon-reload; systemctl --user enable --now etty-job-agent.timer; systemctl --user is-active etty-job-agent.timer
