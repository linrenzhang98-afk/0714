# PRJNA1056765 Metagenome Analysis Report

Generated: 2026-08-01

## Scope

- Dataset: PRJNA1056765
- Data type: public SRA DNA WGS / METAGENOMIC / SINGLE-end runs
- First-pass scope: 400 candidate runs
- Deep-review scope: 30 selected runs
- Main tools used: Kraken2, Bracken, fastp for deep-review QC

## Completed Work

- Production first-pass completed for 400/400 runs across 20 batches.
- First-pass outputs were summarized into public QC and Bracken species tables.
- Second-stage candidates were selected from first-pass outputs.
- Deep-review shortlist was reduced to 30 representative samples.
- Deep-review run completed for 30/30 selected samples.
- Deep-review confirmation summary showed 30/30 `stable_same_top` calls and 0 `changed_top` calls.

## Deep-Review Groups

- Acinetobacter: 4
- Candida: 1
- Enterobacterales: 4
- Haemophilus: 4
- Mycobacteria: 4
- Pseudomonas: 4
- Staphylococcus: 4
- Stenotrophomonas: 1
- Streptococcus: 4

## High-Confidence Signal

The 30 selected deep-review samples retained the same top non-background pathogen after QC and Kraken2/Bracken rerun. This supports the first-pass screening calls for the selected high-priority samples.

Representative high-priority organisms include:

- Staphylococcus aureus
- Klebsiella pneumoniae
- Escherichia coli
- Pseudomonas aeruginosa
- Stenotrophomonas maltophilia
- Acinetobacter baumannii
- Candida albicans
- Haemophilus influenzae
- Streptococcus pneumoniae
- Mycobacterium tuberculosis

## Limitations

- Host removal was not performed because a host index was not configured.
- The database is the available Kraken2 PlusPFP 16 GB database, not a larger comprehensive database.
- Public RunInfo metadata lacks reliable disease/body-site labels for case-control inference.
- Current conclusions are pathogen-spectrum and technical-confirmation summaries, not clinical diagnostic claims.

## Recommended Next Step

Do not expand to another large compute stage immediately. The next useful step is report-level interpretation:

- Prepare a pathogen-group table for the 30 stable deep-review samples.
- Separate likely respiratory pathogens from possible background or commensal organisms.
- Mark Mycobacterium and Candida calls for cautious interpretation.
- Decide whether host-removal validation is worth doing for the 30 samples only.

Host-removal or AMR/functional profiling should require explicit approval because it changes compute scope and may require additional indexes or databases.

## Public Outputs

- `reports_public/metagenome_production/summary.md`
- `reports_public/metagenome_second_stage/plan.md`
- `reports_public/metagenome_deep_review/plan.md`
- `reports_public/metagenome_deep_review_run/status.md`
- `reports_public/metagenome_deep_review_summary/summary.md`
- `reports_public/metagenome_deep_review_summary/comparison.tsv`
