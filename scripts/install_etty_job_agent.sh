#!/usr/bin/env bash
set -euo pipefail
[[ "$(hostname)" == ETYY && "$(id -un)" == suma ]] || { echo SAFE_STOP; exit 2; }
ROOT=${ETTY_AGENT_ROOT:-/mnt/disk1/0714_control}; REPO=${ETTY_AGENT_REPO:-$ROOT/repo}; mkdir -p "$ROOT/state" "$ROOT/logs" "$ROOT/queue"
mkdir -p "$HOME/.config/systemd/user"; cat > "$HOME/.config/systemd/user/etty-job-agent.service" <<EOF
[Unit]
Description=0714 ETYY reviewed job agent
[Service]
ExecStart=/usr/bin/env python3 $REPO/scripts/etty_job_agent.py --repo $REPO --queue $ROOT/queue --state $ROOT/state/jobs.json
Restart=always
EOF
cat > "$HOME/.config/systemd/user/etty-job-agent.timer" <<'EOF'
[Unit]
Description=0714 ETYY job polling
[Timer]
OnBootSec=2min
OnUnitActiveSec=3min
Unit=etty-job-agent.service
[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload; systemctl --user enable --now etty-job-agent.timer
systemctl --user is-active etty-job-agent.timer
