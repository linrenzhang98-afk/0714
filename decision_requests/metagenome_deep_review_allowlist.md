# Allowlist metagenome_deep_review

The next deep-review step is a guarded planning job. It validates the 30 selected runs and writes `run_plan.sh`; it does not execute heavy analysis.

If this task is not yet in `runner/config.local.json`, add:

```json
"metagenome_deep_review": {
  "script": "/mnt/disk1/db/kraken2/0714/pipelines/metagenome_deep_review_runner.py",
  "timeout_seconds": 3600
}
```

This is required before `jobs/20260731T000000Z-prjna1056765-metagenome-deep-review-plan.json` can run.
