# PRJNA1056765 formal taxonomy/community analysis design

## Cohort and estimand

The analysis cohort is the complete available production set: 400 unique DNA-WGS BALF runs (400 unique patients/BioSamples), all marked `done`, with exact membership in the checked-in Bracken matrix. Two additional published clinical WGS records have `size_MB=0` and no available reads; they are reported but not manufactured into the cohort.

The primary independent phenotype is the published four-level diagnosis (Bacterial infection, Fungal infection, Lung cancer, Pulmonary tuberculosis). Published Training/Test cohort and collection date are independent design metadata used for stratification and technical sensitivity. Dominant species, top pathogen, pathogen group, diversity, and clusters are derived from the same abundance matrix and are never treated as independent phenotypes.

## Prespecified analysis

- Species is primary; genus aggregated from the first token of binomial species labels is sensitivity.
- Preserve all samples. Flag low-information/outliers by prespecified robust QC; repeat key analyses in the full cohort and a sensitivity cohort excluding flagged samples.
- Community analyses exclude explicit obvious non-microbial labels (Homo sapiens; the plants Arabidopsis, Benincasa, Camelina and Cucurbita; and Toxoplasma) and renormalize within retained species. Camelina was added during pre-analysis feature QC because it is an unambiguous plant label; it was not diagnosis-associated in the preliminary smoke output. The exclusion list is then frozen. All original features remain in the checked-in input matrix.
- Prevalence filter is 10% (40/400) for ordination/inference; 5% and 20% are sensitivity summaries. CLR uses a fixed pseudocount equal to half the smallest positive retained relative abundance.
- Alpha diversity: observed taxa, Shannon, Simpson, Pielou. Diagnosis associations use Kruskal-Wallis with effect size and BH correction.
- Beta diversity: Bray-Curtis PCoA primary; CLR/Aitchison sensitivity. Diagnosis PERMANOVA uses 9,999 deterministic permutations constrained within published Training/Test cohort; cohort PERMANOVA is separately descriptive of study split. Every PERMANOVA is paired with PERMDISP.
- Community states use unsupervised average-linkage clustering, candidate k=2..10, silhouette selection, and cross-metric agreement as a stability/sensitivity diagnostic. Cluster labels are not clinical subtypes.
- Differential abundance is performed only for published diagnosis: prevalence, group medians, Kruskal-Wallis effect/raw P/BH FDR, plus CLR group-mean contrast sensitivity. Thresholds are not tuned after viewing significance.
- Taxon associations use CLR Pearson association among prevalent taxa and are explicitly compositional hypotheses, never ecological interactions or causality.

## Interpretation classes

Published-diagnosis tests with prespecified filters, 9,999-permutation PERMANOVA and paired PERMDISP are formal inference for the available 400-run cohort. Landscape summaries, clusters/ecotypes, dominant taxa, network edges, and all analyses using abundance-derived labels are descriptive/exploratory. Generalization beyond this public cohort remains subject to its sampling and measurement design.
