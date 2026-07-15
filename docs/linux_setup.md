# Linux Setup Checklist

Example target layout:

```text
/srv/github-analysis-control/
  config.json
  runner/
  scripts/
  repo/
  state/
  logs/
  results/
/data/analysis/
```

## 1. Create A Dedicated User

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin analysis-runner
```

## 2. Create Directories

```bash
sudo mkdir -p /srv/github-analysis-control/{runner,scripts,repo,state,logs,results,example-data}
sudo mkdir -p /data/analysis
sudo chown -R analysis-runner:analysis-runner /srv/github-analysis-control
sudo chown -R analysis-runner:analysis-runner /data/analysis
```

## 3. Clone The GitHub Control Repository

```bash
sudo -u analysis-runner git clone https://github.com/linrenzhang98-afk/0714.git /srv/github-analysis-control/repo
```

For private repositories, configure a deploy key or a fine-grained read-only token for pulling jobs.

## 4. Install Runner Files

Copy these project files to the Linux workstation:

```text
runner/runner.py -> /srv/github-analysis-control/runner/runner.py
scripts/*.py -> /srv/github-analysis-control/scripts/
runner/config.example.json -> /srv/github-analysis-control/config.json
```

Then edit `/srv/github-analysis-control/config.json` for real paths.

## 5. Dry Run

```bash
sudo -u analysis-runner python3 /srv/github-analysis-control/runner/runner.py \
  --config /srv/github-analysis-control/config.json \
  --dry-run
```

## 6. Enable systemd Timer

```bash
sudo cp systemd/github-analysis-runner.service /etc/systemd/system/
sudo cp systemd/github-analysis-runner.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now github-analysis-runner.timer
```

## 7. Inspect Logs

```bash
journalctl -u github-analysis-runner.service -n 100 --no-pager
tail -n 100 /srv/github-analysis-control/logs/runner.jsonl
```

## 8. Submit A Job

Add a JSON file under `jobs/` in the GitHub repository, commit, and push:

```bash
git add jobs/my_job.json
git commit -m "Add analysis job"
git push
```

The workstation will pull it on the next timer run.

