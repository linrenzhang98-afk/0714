# Metagenome Deep-Review Workflow

This stage starts after PRJNA1056765 production first-pass completion.

## Current Scope

- Input: `reports_public/metagenome_deep_review/deep_review_samples.tsv`
- Selected samples: 30
- Mode: guarded planning first
- Heavy execution: not enabled by default

## Runner

Allowlist task name:

```json
"metagenome_deep_review": {
  "script": "/mnt/disk1/db/kraken2/0714/pipelines/metagenome_deep_review_runner.py",
  "timeout_seconds": 3600
}
```

The runner writes:

- `validation_report.json`
- `selected_runs.tsv`
- `run_plan.sh`

It does not execute `run_plan.sh` unless a future explicit execution runner is added.

## Guardrails

- No software installation.
- No database download.
- No deletion of first-pass outputs.
- No host-removal execution until a valid host index is configured.
- No heavy execution unless `execute_mode` is deliberately changed in a future reviewed workflow.
