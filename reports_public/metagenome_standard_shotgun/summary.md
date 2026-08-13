# PRJNA1056765 Standard Shotgun Summary

Generated at: 2026-08-13T06:18:35+00:00

## Scope

- Standard reporting layer for the 30 deep-review mNGS/shotgun samples.
- Inputs are existing host-removed QC outputs, Kraken2/Bracken species profiles, and AMRFinderPlus short-read subset screen results.
- This is stronger than the previous first-pass Kraken2/Bracken screen, but functional pathway profiling remains a separate HUMAnN-style extension.

## Completion

- Samples summarized: 30
- Species/taxa in matrix: 253
- Bracken parse failures: 0
- Differential tests: 861
- FDR-significant species contrasts: 0
- q<0.10 screening contrasts: 0

## Status Counts

- done: 30

## AMR Screen

- done_short_read_subset: 30

## Standard Outputs

- `qc_host_removal_summary.tsv`
- `species_relative_abundance_matrix.tsv`
- `top_species_stacked_relative.tsv`
- `alpha_diversity.tsv`
- `bray_curtis_distance_matrix.tsv`
- `species_group_differentials.tsv`

## Interpretation Guardrails

- Species calls are Kraken2/Bracken database-dependent and should be interpreted as metagenomic classification signals.
- AMRFinderPlus used capped host-removed short-read subsets; negative AMR findings are not definitive absence calls.
- Group contrasts are pathogen-group descriptive contrasts, not clinical outcome associations unless specimen/diagnosis metadata are expanded.
