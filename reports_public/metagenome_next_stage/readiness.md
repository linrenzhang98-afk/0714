# Metagenome Next-Stage Readiness

Generated at: 2026-08-06T13:19:34+00:00
Deep-review samples: 30
Recommended stage: `host_removal_and_amr_ready`

## Readiness

- QC ready: True
- Host-removal tools ready: True
- Host index ready: True
- AMR tool ready: True
- AMR database ready: True
- Host index prefix: `/mnt/disk1/db/host_indexes/GRCh38_noalt_as/GRCh38_noalt_as`

## Blockers

- None.

## Decision

Do not start AMR or host-removal execution until the setup status reports host index and AMRFinderPlus database ready.
The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.

## Output Files

- `tool_readiness.tsv`
