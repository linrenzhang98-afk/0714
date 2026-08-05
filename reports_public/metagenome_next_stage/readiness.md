# Metagenome Next-Stage Readiness

Generated at: 2026-08-05T11:13:26+00:00
Deep-review samples: 30
Recommended stage: `host_removal_validation_ready`

## Readiness

- QC ready: True
- Host-removal tools ready: True
- Host index ready: True
- AMR tool ready: True
- AMR database ready: False
- Host index prefix: `/mnt/disk1/db/host_indexes/GRCh38_noalt_as/GRCh38_noalt_as`

## Blockers

- AMR_DB_DIR is not configured or does not exist.

## Decision

Do not start AMR or host-removal execution until the setup status reports host index and AMRFinderPlus database ready.
The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.

## Output Files

- `tool_readiness.tsv`
