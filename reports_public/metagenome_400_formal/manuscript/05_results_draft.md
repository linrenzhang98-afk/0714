# Results draft

## 3.1 Cohort construction and respiratory metagenomic landscape

The analyzable cohort contained 400 unique runs, BioSamples, and patients, with complete frozen Kraken2/Bracken production records. Two additional mapped published WGS records had size_MB=0 and therefore no sequence reads; neither was removed on the basis of an analysis result. Published diagnoses included lung cancer (n=122), bacterial infection (n=114), pulmonary tuberculosis (n=86), and fungal infection (n=78). Low microbial information was common: 281 samples carried at least one prespecified QC flag. These samples were retained in the primary analysis, and the 119 unflagged samples constituted the strict-QC sensitivity cohort.

## 3.2 Published diagnosis explains a small but reproducible fraction of compositional variation

Published diagnosis was associated with Aitchison community composition in the full cohort (PERMANOVA R²=0.0194, F=2.613, p=0.0001). PERMDISP was not significant (p=0.487), arguing against differential within-group dispersion as the explanation for this result. The prespecified strict-QC analysis also supported the association. The effect remained small: diagnosis explained approximately 1.9% of compositional variation, and ordination showed substantial overlap and inter-individual heterogeneity. Bray–Curtis PERMANOVA was also significant (R²=0.0153, F=2.056, p=0.0115), but PERMDISP was significant (p=0.0013); it therefore provides secondary, qualified evidence rather than an unambiguous centroid-shift result.

## 3.3 A limited set of oral-associated taxa shows diagnosis-associated differences

Five species passed full-cohort BH FDR: Parvimonas micra, Porphyromonas endodontalis, Porphyromonas gingivalis, Campylobacter rectus, and Fusobacterium nucleatum. Of these, P. gingivalis, C. rectus, and F. nucleatum also passed BH FDR in the strict-QC cohort. Prevalence was limited and group medians were generally zero; interpretation therefore rests on the combined prevalence, effect-size, raw-distribution, permutation, FDR, and CLR evidence rather than on separated boxplots. These taxa are diagnosis-associated candidates, not biomarkers.

## 3.4 Respiratory microbial communities do not form stable diagnosis-linked ecotypes

Exploratory clustering depended strongly on the distance representation and number of clusters. Bray silhouette reached its maximum at the tested k=10 boundary, while Bray–Aitchison adjusted Rand agreement remained approximately zero across k=2–10. Thus, data-driven community states provide descriptive organization of heterogeneity but do not support stable clinical subtypes or diagnosis-linked ecotypes.

## 3.5 The fixed deep-review subset is strongly enriched and not representative of the full cohort

The fixed 30 samples had a median classified fraction of 0.0459 compared with 0.0175 in the other 370 and a median dominant-species abundance of 0.956 compared with 0.390. They covered three of four k=10 community states representing at least 5% of the cohort and missed one state containing 7.5% of all samples. Their location and taxonomic enrichment demonstrate selection bias rather than a representative miniature cohort.

## 3.6 Functional profiling generates hypotheses but does not support cohort-wide functional inference

The fixed-30 HUMAnN review identified six samples without any biological pathway beyond UNMAPPED/UNINTEGRATED, while SRR27343296 was extremely pathway sparse. Sensitivity therefore compared n=30, n=24 after removing zero-biological-pathway samples, and n=23 after additionally removing SRR27343296. Although 101 pathway candidates retained direction and FDR across all three sets, the selected sampling, annotation dropout, taxonomy-derived grouping, and significant dispersion in functional PERMANOVA restrict these results to supplementary hypothesis generation. They do not support functional inference for the 400-run cohort.
