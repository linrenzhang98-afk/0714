# Bioinformatics Strategy

## Amplicon

Default workflow: QIIME2.

First-pass steps:

1. Validate manifest and metadata.
2. Import FASTQ into QIIME2 artifact.
3. Generate demultiplexed summary.
4. Run DADA2 denoising.
5. Assign taxonomy with configured classifier.
6. Export feature table, representative sequences, taxonomy, and diversity-ready tables.
7. Write a run report with commands, versions, inputs, outputs, and warnings.

Automatic decisions are limited to low-risk workflow mechanics. DADA2 truncation lengths should be provided in the job or paused for review after demux summary, because aggressive truncation can change biological results.

## Metagenome

Default first-pass workflow: Kraken2 + Bracken.

Rationale:

- It is fast and suitable for unattended first-pass taxonomic profiling.
- It fits the current Linux path context under `/mnt/disk1/db/kraken2`.
- It provides immediate sample-level taxonomic output and failure diagnostics.

Adaptive escalation:

- Use MetaPhlAn when marker-based taxonomic profiling is preferred or Kraken2 database behavior is questionable.
- Use HUMAnN when gene-family/pathway profiling is required and reads/data quality support it.
- Consider assembly only when depth, sample count, and project goal justify the extra runtime and complexity.
- Consider host depletion when host reads dominate and the data policy allows it.

## Decision Boundaries

The platform may automatically retry network failures, create missing output directories, reduce thread counts, and skip already completed jobs.

The platform must not automatically delete raw data, overwrite results, alter metadata, exclude key samples, change group design, or make biological conclusions.
