#!/usr/bin/env bash
set -euo pipefail
[[ "$(hostname)" == ETYY && "$(id -un)" == suma ]] || { echo SAFE_STOP; exit 2; }
ROOT=${ETTY_AGENT_ROOT:-/mnt/disk1/0714_control}; REPO=${ETTY_AGENT_REPO:-$ROOT/agent_runtime}; Q=$ROOT/queue_repo; J=$ROOT/job_repo; mkdir -p "$ROOT/state" "$ROOT/logs" "$ROOT/queue"
[[ -d "$REPO/.git" ]] || git clone git@github.com:linrenzhang98-afk/0714.git "$REPO"
[[ -d "$Q/.git" ]] || git clone git@github.com:linrenzhang98-afk/0714.git "$Q"
[[ -d "$J/.git" ]] || git clone git@github.com:linrenzhang98-afk/0714.git "$J"
PIN="$(git -C "${ETTY_AGENT_BOOTSTRAP:-$REPO}" rev-parse HEAD)"; git -C "$REPO" fetch origin "$PIN"; git -C "$REPO" cat-file -e "$PIN^{commit}"; git -C "$REPO" checkout --detach "$PIN"; test "$(git -C "$REPO" rev-parse HEAD)" = "$PIN"
mkdir -p "$Q" "$J"
mkdir -p "$HOME/.config/systemd/user"; cat > "$HOME/.config/systemd/user/etty-job-agent.service" <<EOF
[Unit]
Description=0714 ETYY reviewed job agent
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=/usr/bin/env python3 -m scripts.etty_job_agent --queue-repo $Q --job-repo $J --state $ROOT/state/jobs.json --once
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
