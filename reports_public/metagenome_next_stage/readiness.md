# Metagenome Next-Stage Readiness

Generated at: 2026-08-04T13:20:34+00:00
Deep-review samples: 30
Recommended stage: `report_interpretation_only`

## Readiness

- QC ready: False
- Host-removal tools ready: False
- Host index ready: False
- AMR tool ready: False
- AMR database ready: False

## Blockers

- fastp is not available.
- bowtie2 and/or samtools are not available.
- HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.
- No AMR tool detected among abricate, rgi, amrfinder, diamond.
- AMR_DB_DIR is not configured or does not exist.

## Decision

Do not start AMR or host-removal execution until host index and AMR database paths are explicitly configured.
The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.

## Output Files

- `tool_readiness.tsv`
