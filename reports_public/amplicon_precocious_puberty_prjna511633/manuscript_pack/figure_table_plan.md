# PRJNA511633 Figure And Table Plan

Generated at: 2026-08-12T00:36:56+00:00

## Main Figures

1. Study workflow and QC: public SRA retrieval, reverse-read DADA2 rescue, and retained-depth summary.
2. Alpha diversity boxplots at rarefaction depth 10000: Shannon, observed features, and evenness by group.
3. Beta diversity ordination: Bray-Curtis PCoA with group-significance visualization from QIIME2.
4. Genus-level composition: stacked relative-abundance bar plot for top genera plus 'Other'.
5. Differential candidate panel: effect-direction plot for FDR-significant or near-significant genera.

## Tables

1. Sample metadata and group assignment table.
2. DADA2 depth/QC table.
3. Alpha diversity group summary.
4. Genus-level differential candidate table.
5. qPCR validation target table.

## Notes

- Use genus-level conclusions as primary because V3-V4 16S species labels are not definitive.
- State clearly that reverse reads were used after paired/forward analyses retained too few samples.
- Include rarefaction sensitivity: 5000 retains 48/48; 10000 retains 47/48.
