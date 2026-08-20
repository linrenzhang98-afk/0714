# Stage 1 manuscript draft

## A. Final title options

1. Analytical robustness of cross-disease BALF microbiome variation in PRJNA1056765
2. A secondary compositional robustness reanalysis of the PRJNA1056765 BALF microbiome cohort
3. A secondary compositional robustness reanalysis finds limited diagnosis-associated variation in BALF metagenomes
4. An analytical robustness audit of feature-space and dispersion dependence in BALF metagenomes
5. A secondary compositional robustness reanalysis identifies small conditional diagnosis effects in PRJNA1056765

Preferred working title: **Analytical robustness of cross-disease BALF microbiome variation in PRJNA1056765**

## B. Scientific storyline

This secondary compositional robustness reanalysis asks how much lower-airway community variation is attributable to published diagnosis after prespecified compositional, dispersion, feature-space, and quality-control safeguards. The analysis uses 400 downloadable BALF DNA runs from the same source cohort studied by Han et al., but it does not reproduce their n=284 cancer-versus-infection analysis because the analytical population, contrast, and parts of the upstream pipeline differ. In the frozen full-cohort 30-species Aitchison analysis, diagnosis explained a very small conditional variance component of 1.94%. The estimate was stable to two prespecified pseudocounts. Its magnitude and dispersion qualification changed across prespecified feature spaces, distance metrics, and the n=119 pipeline-dependent sensitivity population. All full-cohort Bray–Curtis cells were dispersion-qualified. The study therefore supports an analytical robustness audit, not a new disease fingerprint, biomarker, diagnostic signal, disease-specific taxon discovery, or mechanism.

## C. Structured abstract

### Background

Metagenomic analysis of PRJNA1056765 reported bronchoalveolar lavage fluid microbial differences among lung cancer and pulmonary infections. The same cohort offers an opportunity to assess how strongly published diagnosis structures community composition when compositional geometry, multivariate dispersion, feature filtering, and pipeline-dependent quality criteria are considered. Because upstream database versions, negative-control handling, filtering, and feature definitions remain incompletely reconstructed, this study is a secondary analytical robustness audit rather than a reproduction of the original analysis.

### Methods

We analyzed the 400 publicly downloadable BALF DNA runs with the frozen Kraken2/Bracken species matrix and four-level published diagnosis. The primary anchor retained 30 species detected in at least 10% of samples, applied centered log-ratio transformation with a prespecified zero replacement, and tested diagnosis by cohort-stratified PERMANOVA with 9,999 permutations. PERMDISP accompanied every distance-based test. Before computation, we froze an 18-cell grid spanning three prevalence thresholds, two Aitchison pseudocounts, Bray–Curtis distance, the full cohort, and an n=119 pipeline-dependent sensitivity population. The grid prohibited pairwise contrasts, taxon discovery, and outcome-guided parameter changes.

### Results

The 30-species Aitchison anchor replayed exactly from locked inputs and code. Diagnosis explained 1.94% of full-cohort variation (R²=0.01941; permutation P=0.0001), without evidence of differential dispersion (PERMDISP P=0.487). Changing the pseudocount reduced R² by 0.00033 and retained the same dispersion qualification. At 5% prevalence, 90-species Aitchison R² values were 0.01637 and 0.01583, and both cells were dispersion-qualified. At 20% prevalence, only two species remained and R² values were 0.0019795 and 0.0017942. Results in the n=119 pipeline-dependent sensitivity population ranged from R²=0.00410 to 0.06958 across Aitchison cells, but these estimates describe a selected population and are not direct replications of the full-cohort estimand. All three full-cohort Bray–Curtis cells were dispersion-qualified. The complete 18-cell grid was reported without selecting cells by P value, R², or dispersion behavior.

### Conclusions

Diagnosis explains a very small conditional variance component in the frozen full-cohort 30-species Aitchison analysis, and that estimate is stable to the two prespecified pseudocounts. Estimated magnitude and dispersion qualification depend on feature space, metric, and QC population. These findings do not support a stable disease fingerprint, biomarker, diagnostic signal, disease-specific taxon discovery, or mechanistic conclusion. Taxon overlap or mismatch with the original report remains pipeline/statistical concordance or discrepancy until upstream equivalence is established.

## D. Results

### The reanalysis uses the source cohort but a different estimand

Han et al. reported 402 patients with lung cancer, bacterial infection, fungal infection, or pulmonary tuberculosis. Their ecological analyses used the n=284 training set, while diagnostic modelling used a fixed 284/118 internal split. The associated data descriptor documented the same cohort and 32 DNA and 32 RNA negative controls (Han et al., 2025; Tang et al., 2025). We analyzed the 400 DNA runs with downloadable reads. The two unavailable records represent a data-availability difference rather than a new cohort (Fig. 1).

The current primary test is a four-level diagnosis omnibus in all 400 runs. It is not equivalent to the published n=284 cancer-versus-infection contrast or the reported pairwise comparisons. The pipelines share fastp preprocessing, human-read removal, Kraken2, and Bracken at a broad level. Exact database builds and versions, negative-control handling, parts of sample filtering, and feature definitions remain unresolved. We therefore classify cross-study taxon overlap or mismatch only as pipeline/statistical concordance or discrepancy. We do not infer biological agreement or disagreement (Fig. 2).

### Exact anchor replay recovers a very small conditional variance component

The locked full-cohort anchor retained 30 species detected in at least 40 of 400 samples. Its exact replay reproduced the frozen PERMANOVA and PERMDISP values from the same input hashes, species order, pseudocount, code path, and seeds. Diagnosis explained 1.94% of Aitchison variation (R²=0.0194095; permutation P=0.0001). PERMDISP did not indicate differential dispersion (P=0.487). Only this exact anchor replay is described as reproducible. It does not reproduce Han et al.'s original ecological analysis because the population, contrast, and upstream equivalence differ (Fig. 3; Supplementary Table S1).

### The pseudocount result is stable within the 30-species space

Replacing zeros with half the minimum positive retained abundance gave the anchor R² of 0.0194095. Replacing zeros with one tenth of that minimum gave R²=0.0190746, an absolute difference of 0.0003349. PERMDISP remained unqualified under both choices (P=0.487 and 0.4677). The estimated diagnosis-associated variance component was therefore stable to the two prespecified pseudocounts within this feature space. Both estimates remained very small (Fig. 3; Supplementary Table S1).

### Feature filtering changes magnitude and dispersion qualification

The prespecified 5% prevalence threshold retained 90 species. Full-cohort Aitchison R² was 0.0163698 with the half-minimum pseudocount and 0.0158287 with the tenth-minimum pseudocount. Both cells were dispersion-qualified (PERMDISP P=0.0145 and 0.0187). The 20% threshold retained only two species. Corresponding R² values were 0.0019795 and 0.0017942, with PERMDISP P=0.1591 and 0.2173. We report these feature spaces separately and make no pooled range or majority-of-cells statement. The two-species result reflects an especially restrictive analytical space and does not adjudicate disease-specific biology (Fig. 3; Supplementary Table S1).

### The QC analysis estimates a selected population

The frozen QC definition retained 119 samples, including 42 bacterial infection, 19 fungal infection, 36 lung cancer, and 22 pulmonary tuberculosis cases. This n=119 set is designated only as a pipeline-dependent sensitivity population. Across its six Aitchison cells, R² ranged from 0.0041007 to 0.0695841. The 5% and 10% cells were not dispersion-qualified under either pseudocount. Both 20% cells were dispersion-qualified (PERMDISP P=0.0418 and 0.0413). Restricting the population changes the estimand, so numerical differences from n=400 do not strengthen or weaken the full-cohort effect and cannot validate the pipeline or be attributed to biology (Fig. 4; Supplementary Table S1).

### Bray–Curtis results are qualified by dispersion in the full cohort

At 5%, 10%, and 20% prevalence, full-cohort Bray–Curtis R² values were 0.0263302, 0.0153390, and 0.0096564. PERMDISP P values were 0.0001, 0.0009, and 0.0256. All three cells therefore represent location and/or dispersion differences rather than unqualified centroid shifts. In the pipeline-dependent sensitivity population, Bray–Curtis R² values were 0.0638835, 0.0607394, and 0.0796114. The 5% cell was not dispersion-qualified (P=0.1022), whereas the 10% and 20% cells were qualified (P=0.0414 and 0.0002). These cells are metric and population sensitivities, not evidence that one analysis recovers a truer biological separation (Supplementary Fig. S1; Supplementary Table S1).

### The audit does not identify a stable disease fingerprint

The exact anchor replay, pseudocount stability, and complete sensitivity grid define the supported claim. Diagnosis explains a very small conditional variance component in the frozen 30-species full-cohort Aitchison analysis. Estimated magnitude and dispersion qualification depend on prespecified feature space, metric, and QC population. Five taxa had passed FDR in the earlier frozen full-cohort analysis and three passed FDR in the pipeline-dependent sensitivity population, but key taxa overlapped the original publication, group medians were generally zero, and some directions differed. These are pipeline/statistical concordance or discrepancy findings, not new disease-specific taxa. Bray and Aitchison clustering also produced adjusted Rand indices near zero across k=2–10, and the highest Bray silhouette occurred at the k=10 search boundary. Taken together, the frozen evidence supports continuous, analysis-dependent heterogeneity. It does not support a stable disease fingerprint, biomarker, diagnostic signal, disease-specific taxon discovery, or mechanism (Fig. 5).

## Evidence map for drafting

- Han et al. cohort, original ecological scope, taxa, and models: Han D et al. *npj Digital Medicine*. 2025. doi:10.1038/s41746-025-01977-5.
- Cohort resource, controls, and released modalities: Tang H et al. *Scientific Data*. 2025. doi:10.1038/s41597-025-06171-6.
- Complete v5 results: `reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv` and its locked `manifest.json`.
- Frozen anchor, differential taxa, and clustering: `reports_public/metagenome_400_formal/statistics/permanova_permdisp.tsv`, `associations/diagnosis_species_differential.tsv`, and `clustering/cluster_diagnostics.tsv`.
- Pipeline comparison: `original_pipeline_reconstruction.md` and `pipeline_difference_matrix.tsv`.
