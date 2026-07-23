# Travel Mode Runbook

## Goal

Keep the Linux workstation running unattended while only public, compact status summaries are pushed to GitHub for remote review.

## What Gets Uploaded

- `reports_public/platform_status.md`
- `decision_requests/*.md` when a workflow needs human confirmation

## What Must Not Be Uploaded

- Raw FASTQ
- Kraken2/QIIME2 result directories
- Databases
- `.runner_logs/`
- `.runner_state/`
- `runner/config.local.json`
- Any file containing patient identifiers or sensitive sample-level metadata

## Before Travel

Run:

```bash
cd /mnt/disk1/db/kraken2/0714
git pull --ff-only
conda activate mgshotgun
python runner/runner.py --config runner/config.local.json --no-pull --dry-run
bash scripts/publish_status_to_github.sh
git status
```

`git status` should be clean after publishing.

## Enable Status Publishing Timer

This modifies systemd and requires sudo:

```bash
sudo cp /mnt/disk1/db/kraken2/0714/systemd/github-analysis-status-publisher.service /etc/systemd/system/
sudo cp /mnt/disk1/db/kraken2/0714/systemd/github-analysis-status-publisher.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now github-analysis-status-publisher.timer
systemctl list-timers --all | grep github-analysis-status-publisher
```

## Emergency Stop

```bash
sudo systemctl disable --now github-analysis-status-publisher.timer
```

## GitHub Permissions

A public repository can be viewed and forked by strangers, but they cannot push to your repository unless you explicitly add them as collaborators or expose a write token/key. Keep private keys and tokens out of the repository.
