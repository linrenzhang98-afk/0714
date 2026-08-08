# PRJNA511633 Amplicon Depth QC

Generated at: 2026-08-08T14:51:23+00:00

QC state: `not_publication_ready`

## Interpretation

- Median post-DADA2 depth is below 1000 reads; diversity statistics should not be used as formal conclusions. Optimize DADA2 trimming/merging before final alpha/beta diversity analysis.
- The `depth=10` retry is treated as an engineering fallback, not a publication-grade diversity depth.
- Formal alpha/beta diversity requires an independently justified rarefaction depth and sensitivity analysis.

## Post-DADA2 Depth Distribution

- Samples summarized: 48
- Min final reads: 0
- Q25 final reads: 0.0
- Median final reads: 0.0
- Q75 final reads: 0.0
- Max final reads: 50570

## Files

- `denoising_depth_summary.tsv`
- `sampling_depth_recommendations.tsv`
- `qc_summary.json`
