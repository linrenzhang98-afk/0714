# Functional HUMAnN status snapshot publisher

This helper publishes only the small files under `reports_public/metagenome_functional_profile` while the long-running HUMAnN worker continues separately.

## Safety properties

- Does not stop, restart, or signal the HUMAnN worker.
- Does not install software, alter conda environments, or download databases.
- Does not move the hospital repository's current branch or HEAD.
- Uses a temporary Git index and a status-only commit based on the latest `origin/main`.
- Publishes only summary/progress/provenance files; worker logs and raw data are excluded.
- Push races are retried up to three times without force push.

## Activation boundary

The repository contains user-level systemd unit templates for a 5-minute status cadence. They are intentionally **not installed or enabled by repository code**. Installing/enabling them changes hospital systemd state and requires explicit operator authorization.

The currently running HUMAnN production job can continue untouched. The snapshot publisher is designed to be independent from it.
