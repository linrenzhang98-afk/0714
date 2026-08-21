# Robustness results summary

## Status

This summary is restricted to the previously frozen 400-run outputs. No new sensitivity-grid statistic was run in this phase because the live DeepSeek pre-computation gate returned `STEER` through five review rounds. The final v5 grid is frozen for later execution, but it is not represented here as completed evidence.

## Frozen findings that support the audit storyline

1. **Diagnosis has a very small conditional variance component.** In the frozen full-cohort 10% P1 Aitchison analysis, diagnosis accounted for R²=0.0194 of community variation. PERMANOVA P=0.0001 and paired PERMDISP P=0.487. The permitted interpretation is that diagnosis accounts for approximately 1.9% of variation conditional on this pipeline; it is not evidence of distinct disease microbiomes.
2. **Bray–Curtis does not support an unqualified location claim.** Frozen Bray–Curtis PERMANOVA R²=0.0153, P=0.0115, while PERMDISP P=0.0013. This represents location and/or dispersion differences and cannot be written as disease-centroid separation.
3. **QC sensitivity changes the estimand.** The strict-QC subset retains 119/400 runs, with diagnosis counts 42 bacterial infection, 19 fungal infection, 36 lung cancer, and 22 TB. Its larger R² values cannot be compared directly with full-cohort estimates as though they were the same population. Agreement does not validate the upstream pipeline; disagreement is not biological evidence.
4. **Differential evidence is sparse and already biologically overlapping.** Five taxa passed full-cohort FDR and three passed strict-QC FDR. Key taxa overlap Han et al., group medians were generally zero, and some directions differ. These are pipeline/statistical concordance or discrepancy findings, not new taxa or biomarkers.
5. **No stable ecotype solution was found.** The Bray silhouette maximum occurred at the k=10 search boundary and Bray/Aitchison adjusted Rand agreement was approximately zero across k=2–10. The result supports continuous, metric-dependent heterogeneity rather than validated community types.

## What remains unresolved

Exact upstream equivalence with Han et al. is not established because database build/version, some filtering parameters, negative-control handling, and complete row-level ecological exclusions remain unresolved. Consequently, taxon-list or direction differences cannot be classified as biological disagreement.

## Current verdict

**CONDITIONAL GO** for a methodological reproducibility/robustness manuscript. The frozen evidence supports a narrow paper about effect size, dispersion, QC dependence, and failure of stable clustering. It does not support disease fingerprints, biomarkers, diagnostic claims, or causal interpretation. The v5 sensitivity grid remains pending DeepSeek approval and execution.
