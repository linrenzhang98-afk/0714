# PRJNA1056765 Production Descriptive Plan

## Decision

The production priority is descriptive clinical infection/pathogen-spectrum analysis, not pneumonia-vs-non-pneumonia comparison.

Reason:

- `candidate_dna_wgs_runs.tsv` contains 400 DNA WGS metagenomic single-end candidate runs.
- `Disease` is empty for all 400 candidates.
- `Body_Site` is empty for all 400 candidates.
- BioSample duplicates are absent among candidates.

Because public RunInfo metadata does not expose clinical grouping labels, group-comparison statistics should not be forced during travel mode.

## Production Candidate Set

Use:

- `reports_public/production_planning/prjna1056765/candidate_dna_wgs_runs.tsv`

Candidate definition:

- `LibraryStrategy == WGS`
- `LibrarySource == METAGENOMIC`
- `LibraryLayout == SINGLE`
- `LibraryName` contains `DNA`
- `size_MB` between 1 and 1000

Current count:

- 400 candidate runs
- 400 unique BioSamples
- 0 duplicate BioSample run rows

## Allowed Production First Pass

Run all 400 candidates in batches, using:

- Kraken2 + Bracken
- Database: `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`
- No large database download
- No metadata editing
- No clinical grouping
- No final biological conclusion

## Outputs

For each run:

- Kraken2 output
- Kraken2 report
- Bracken species table
- Per-run status

For the cohort:

- Run QC summary
- Species fraction matrix
- Frequently detected species
- Classification rate distribution
- Clinical-pathogen watchlist table

## Interpretation Boundary

Allowed:

- Describe pathogen-spectrum patterns.
- Identify frequently detected organisms.
- Flag potential contaminants or database artefacts.
- Stratify by technical features such as classification rate or read count.

Not allowed without additional metadata:

- Pneumonia vs non-pneumonia claims.
- Infection vs tumor claims.
- Patient-level clinical conclusions.
- Treatment or diagnostic recommendations.

## Stop Conditions

Stop and write `decision_requests/*.md` if:

- More than 20% of a batch fails.
- More than 10 runs fail in one batch.
- Disk free space drops below 500 GB.
- Required software or database is missing.
- GitHub status cannot be pushed repeatedly.
