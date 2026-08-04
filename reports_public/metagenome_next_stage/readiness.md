# Metagenome Next-Stage Readiness

Generated at: 2026-08-04T22:03:42+00:00
Deep-review samples: 30
Recommended stage: `qc_kraken_bracken_completed_or_available`

## Readiness

- QC ready: True
- Host-removal tools ready: True
- Host index ready: False
- AMR tool ready: True
- AMR database ready: False

## Blockers

- HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.
- AMR_DB_DIR is not configured or does not exist.

## Decision

Do not start AMR or host-removal execution until host index and AMR database paths are explicitly configured.
The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.

## Output Files

- `tool_readiness.tsv`
