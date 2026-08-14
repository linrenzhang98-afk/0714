# PRJNA511633 Amplicon Depth QC

Generated at: 2026-08-14T18:03:55+00:00

QC state: `candidate_depth_possible`

## Interpretation

- Post-DADA2 depth may support diversity analysis after selecting a depth that preserves most samples in both groups and checking rarefaction stability.
- The `depth=10` retry is treated as an engineering fallback, not a publication-grade diversity depth.
- Formal alpha/beta diversity requires an independently justified rarefaction depth and sensitivity analysis.

## Post-DADA2 Depth Distribution

- Samples summarized: 48
- Min final reads: 6513
- Q25 final reads: 28288.0
- Median final reads: 38818.0
- Q75 final reads: 49843.2
- Max final reads: 55466

## Files

- `denoising_depth_summary.tsv`
- `sampling_depth_recommendations.tsv`
- `qc_summary.json`
