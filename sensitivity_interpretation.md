# Frozen v5 sensitivity interpretation

## Audit status

The frozen v5 grid completed all 18 prespecified cells. The manifest records exact input-hash verification and exact replay of the frozen full-cohort 10% prevalence, P1 Aitchison anchor: PERMANOVA F=2.612771519062346, R²=0.019409536625522597, P=0.0001; PERMDISP F=0.8066530620728115, R²=0.006073890452579873, P=0.487. This replay is an integrity check, not new evidence.

The complete cell-level results are in `reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv`. No cell was selected or omitted according to its P value, R², or dispersion result.

## Prespecified layers

### Layer 1: 10% prevalence pseudocount audit in the full cohort

With the same 30 species, changing P1 to P2 changed PERMANOVA R² from 0.0194095 to 0.0190746, an absolute difference of 0.0003349. PERMDISP remained unqualified at both P1 (P=0.487) and P2 (P=0.4677). Thus the 30-species Aitchison estimate is insensitive to the two prespecified zero replacements. Both estimates remain very small under the frozen interpretation rule.

### Layer 2: full-cohort Aitchison feature-space audit

At 5% prevalence, 90 species were retained. R² was 0.0163698 at P1 and 0.0158287 at P2; both cells were dispersion-qualified (PERMDISP P=0.0145 and 0.0187). At 20% prevalence, only two species remained. R² was 0.0019795 at P1 and 0.0017942 at P2; PERMDISP P=0.1591 and 0.2173. These feature spaces are reported separately. No pooled range or majority-of-cells statement is made across these feature spaces. The diagnosis-associated estimate and its dispersion qualification depend on the retained feature space; the 20% threshold is especially restrictive and is not evidence against or for any disease-specific biology.

### Layer 3: strict-QC population audit

The n=119 subset is designated only as a pipeline-dependent sensitivity population. At 5% prevalence, Aitchison R² was 0.0591900 at P1 and 0.0586724 at P2, with PERMDISP P=0.3906 and 0.4087. At 10%, R² was 0.0695841 and 0.0691248, with PERMDISP P=0.449 and 0.5025. At 20%, R² was 0.0041007 and 0.0046211, with PERMDISP P=0.0418 and 0.0413, so both cells were dispersion-qualified. These values cannot be treated as direct changes from full-cohort estimates because restricting the population changes the estimand. The effect-size estimates are conditional on the frozen QC definition and the resulting selected population; agreement or disagreement with the full cohort does not validate the pipeline or attribute the difference to biology.

### Layer 4: Bray–Curtis metric and dispersion audit

All full-cohort Bray–Curtis cells were dispersion-qualified: at 5%, R²=0.0263302 and PERMDISP P=0.0001; at 10%, R²=0.0153390 and P=0.0009; at 20%, R²=0.0096564 and P=0.0256. They support only location-and/or-dispersion differences, not unqualified centroid shifts.

In strict QC, Bray–Curtis at 5% had R²=0.0638835 and PERMDISP P=0.1022. At 10%, R²=0.0607394 and PERMDISP P=0.0414. At 20%, R²=0.0796114 and PERMDISP P=0.0002. The latter two are dispersion-qualified. The strict-QC 5% Bray–Curtis cell was dispersion-unqualified (PERMDISP P=0.1022). These strict-QC cells remain population-specific pipeline sensitivities and do not validate the full-cohort result.

## Bounded interpretation

Only the frozen 30-species Aitchison anchor is described as reproducible because its replay was exact. Diagnosis explains a very small conditional variance component in that full-cohort analysis, and the estimate is stable to the two prespecified pseudocounts. Estimated magnitude and dispersion qualification depend on prespecified feature space, metric, and QC population. All full-cohort Bray–Curtis cells are dispersion-qualified. The grid supports no stable disease fingerprint, biomarker, diagnostic signal, disease-specific taxon discovery, or mechanistic conclusion. It does not establish biological agreement or disagreement with Han et al.; taxon overlap or mismatch remains pipeline/statistical concordance or discrepancy until upstream equivalence is established.
