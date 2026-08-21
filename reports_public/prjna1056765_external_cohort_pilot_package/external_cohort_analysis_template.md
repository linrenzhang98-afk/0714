# Frozen external-cohort analysis grammar template

This template fixes the decision grammar before community results are viewed; it does not copy the anchor v5 thresholds.

1. **Eligibility.** Include only BAL/BALF DNA runs with direct accession-to-subject-to-clinical-label evidence. Preserve raw labels. Exclude unresolved labels. Select one prespecified sample per subject using collection time and clinical eligibility, never microbial composition.
2. **Contrast.** Define one independently documented within-cohort primary contrast. PRJCA039020 remains undefined until CAP/severe mapping is direct. CRA034880 may use raw `Drug_Resistance` versus `Drug_Sensitive` labels. PRJNA977832 remains undefined.
3. **Covariates.** Admit only covariates available before sequence inspection and sufficiently complete within the cohort. Record missingness. Do not harmonize merely to enlarge groups.
4. **Permutations.** Use 9,999 permutations; restrict within center, subject or verified technical batch when the design requires and permits it. Stop if diagnosis is not independently estimable.
5. **Features.** Freeze a cohort-specific prevalence rule after inspecting metadata and technical detection summaries but before disease-labelled community outcomes. Report retained count. Do not import anchor 5/10/20% thresholds automatically.
6. **Geometry.** Primary CLR/Aitchison with a prespecified zero-replacement rule; Bray-Curtis is a comparator. Freeze all choices before group-labelled ordination or PERMANOVA.
7. **Inference.** Report PERMANOVA effect size and uncertainty with PERMDISP qualification. Never define success as significance or pool raw matrices across studies.
8. **QC sensitivity.** Separate universal integrity metrics from cohort-specific sensitivity populations. Missing negative controls are a limitation, not permission to reuse another cohort's contamination cutoff.
9. **Clustering.** Run only when sample size and feature support are adequate; report silhouette and cross-representation agreement across a frozen k range. Do not infer absence of all ecotypes from instability under tested representations.
10. **Cross-cohort synthesis.** Compare cohort-level estimates descriptively first. Formal pooling requires later justification of estimand comparability and explicit approval.
