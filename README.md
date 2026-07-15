# Safe GitHub-Controlled Analysis Runner

This project provides a safer alternative to "pull commands from GitHub and run them".

The runner pulls a GitHub repository, reads structured `jobs/*.json` files, and executes only locally configured allowlisted scripts. GitHub job files cannot provide arbitrary shell commands.

## Current Status

Created on 2026-07-15.

Included:

- `runner/runner.py`: whitelist-based Linux runner.
- `runner/config.example.json`: local config template.
- `jobs/*.json`: example GitHub-controlled job files.
- `scripts/*.py`: placeholder allowlisted analysis scripts.
- `systemd/*.service` and `systemd/*.timer`: Linux timer deployment examples.
- `docs/security_model.md`: security model and operating rules.
- `docs/linux_setup.md`: deployment checklist.

Not yet done:

- No real workstation path has been configured.
- No real GitHub repository has been cloned on Linux.
- Placeholder analysis scripts still need replacement with your real analysis scripts.
- No Linux workstation test has been run from this Windows Codex session.

## How It Works

1. A Linux workstation keeps a local clone of the control repository.
2. A systemd timer runs `runner.py` every few minutes.
3. `runner.py` runs `git pull --ff-only`.
4. It scans `jobs/*.json`.
5. It validates each job against a local allowlist.
6. It runs only the fixed local script for the requested task.
7. It records state in `runner_state.json` so jobs are not repeated.
8. It writes logs as JSON lines.

## Job Example

```json
{
  "job_id": "2026-07-15-demo-metabolomics-001",
  "task": "run_metabolomics_analysis",
  "created_at": "2026-07-15T00:00:00Z",
  "params": {
    "dataset_path": "/srv/github-analysis-control/example-data/metabolomics_demo.csv",
    "group_col": "group",
    "sample_id_col": "sample_id",
    "method": "summary"
  }
}
```

## Continue After Restart

Read these files first:

- `README.md`
- `brief_report.md`
- `docs/security_model.md`
- `docs/linux_setup.md`

Then customize:

1. Copy `runner/config.example.json` to the Linux workstation as `/srv/github-analysis-control/config.json`.
2. Replace script paths and data roots.
3. Replace placeholder scripts with reviewed real analysis scripts.
4. Install the systemd service and timer.

