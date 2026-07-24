# Production Autopilot

The hourly status publisher can activate and run production descriptive batches without phone-heavy manual control.

Default safety settings:

- Autopilot is enabled by `ENABLE_PRODUCTION_AUTOPILOT=1`.
- It runs at most one batch per hourly timer invocation.
- It will not start a second runner if one is already active.
- It only runs planned jobs under `jobs/planned_production_prjna1056765`.
- Default cap is `MAX_BATCH=3`, so it starts only production batches 001-003 until reviewed.

Generated log:

- `reports_public/autopilot_production.log`

Disable:

```bash
ENABLE_PRODUCTION_AUTOPILOT=0 bash scripts/publish_status_to_github.sh
```

Extend beyond batch 003 after review:

```bash
PRODUCTION_AUTOPILOT_MAX_BATCH=10 bash scripts/publish_status_to_github.sh
```

Do not use this mechanism for deletion, large database downloads, metadata editing, or final biological conclusions.
