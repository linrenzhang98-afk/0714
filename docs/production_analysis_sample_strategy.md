# Production Analysis Sample Strategy

## Current Position

Travel-mode first-pass analysis is running and should continue without phone-heavy intervention. The next formal-analysis task is sample planning, not full production execution.

## Production Sample Definition

For `PRJNA1056765`, production candidates should be derived from SRA RunInfo using these technical filters:

- `LibraryStrategy == WGS`
- `LibrarySource == METAGENOMIC`
- `LibraryLayout == SINGLE`
- `LibraryName` contains `DNA`
- Run size is within a reviewed range

The first planning script writes both all candidate runs and one representative run per BioSample.

## Why BioSample Deduplication Matters

`PRJNA1056765` includes DNA/RNA and possible repeated technical records. Production analysis must avoid mixing independent samples with repeated measurements unless the model explicitly supports repeated observations.

Default planning rule:

- Keep all candidate DNA WGS runs in `candidate_dna_wgs_runs.tsv`.
- Also create `representative_runs_by_biosample.tsv` using the largest run per BioSample.
- Defer the final choice between all-runs and representative-runs until metadata review.

## What Can Continue During Travel

Allowed:

- Generate candidate sample tables.
- Generate public planning summaries.
- Continue focused first-pass up to the authorized 100-run limit.
- Prepare 16S backup dataset candidates.

Not allowed without confirmation:

- Full production cohort run.
- Final inclusion/exclusion decisions.
- Metadata editing.
- Clinical grouping design.
- Final biological or clinical conclusions.
- New large database download.

## Minimum Production Readiness Criteria

Before production execution:

1. Candidate sample table exists.
2. Representative BioSample table exists.
3. Metadata fields relevant to clinical grouping are reviewed.
4. Pilot/focused classification rates are reviewed.
5. Database and method versions are frozen.
6. Output and overwrite rules are confirmed.
