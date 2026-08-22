#!/usr/bin/env bash
set -euo pipefail
CONFIG=/mnt/disk1/0714_control/config.local.json
PY=/home/suma/anaconda3/envs/mgshotgun/bin/python
LOG=/mnt/disk1/0714_control/logs/pilot_poll.log
exec >>"$LOG" 2>&1
while :; do
  date -Is
  "$PY" /mnt/disk1/0714_control/repo/runner/runner.py --config "$CONFIG"
  sleep 300
done
