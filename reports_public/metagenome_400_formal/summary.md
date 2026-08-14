# PRJNA1056765 formal taxonomy/community analysis

The complete available cohort contains 400 unique patient/BioSample runs with 400/400 completed production records and exact Bracken-matrix membership. Published diagnosis is the primary independent phenotype; abundance-derived dominant-pathogen labels are descriptive only.

Primary analysis retained 30 microbial species at prevalence ≥10%. 281 samples were prespecified QC/low-information flags; none were deleted, and key inference was repeated in the 119-sample sensitivity cohort.

## Main findings and evidence class

1. **Formal, compositionally supported but small diagnosis association.** Aitchison PERMANOVA gave R²=0.0194, p=0.0001 in all 400 samples, with PERMDISP p=0.487; the QC-sensitivity result was also significant. Diagnosis therefore explains a small fraction of composition rather than defining sharply separated communities.
2. **Bray result is not location-specific.** Bray PERMANOVA gave R²=0.0153, p=0.0115, but PERMDISP was also significant (p=0.0013). This cannot be written as an unqualified diagnosis centroid shift.
3. **Formal differential evidence is sparse and prevalence-driven.** 5 species passed full-cohort BH FDR <0.05; 3 also passed BH FDR in the strict QC-sensitivity cohort. Full-cohort candidates were Parvimonas micra, Porphyromonas endodontalis, Porphyromonas gingivalis, Campylobacter rectus, Fusobacterium nucleatum. Their group medians were generally zero, so effect sizes/CLR contrasts and raw distributions are essential.
4. **No defensible stable ecotype solution.** Bray silhouette reached its boundary maximum at k=10, while Bray/Aitchison adjusted Rand agreement was approximately zero across k=2..10. Clusters are exploratory community states, not clinical subtypes.
5. **The fixed 30 are strongly selected.** Median classified fraction was 0.0459 versus 0.0175; median dominant-species abundance was 0.956 versus 0.390. The 30 cover 3/4 k=10 states representing ≥5% of the cohort and miss a state containing 7.5% of all samples. Their HUMAnN results cannot represent the 400-run functional landscape.

Formal inference statistics and paired dispersion tests are in `statistics/permanova_permdisp.tsv`. Differential tables use published diagnosis, cohort-stratified permutations, effect sizes, raw P and BH FDR in both full and QC-sensitivity cohorts, with CLR group-mean sensitivity. Clusters, dominant taxa and CLR networks remain descriptive/exploratory.

The fixed-30 HUMAnN analysis is suitable only as a selected functional supplement; it must not be presented as a functional survey of all 400 runs.
