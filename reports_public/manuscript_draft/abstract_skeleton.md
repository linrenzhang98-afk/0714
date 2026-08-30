# Abstract skeleton

## Background

Lower-airway shotgun datasets are increasingly available, but cohort-specific processing and heterogeneous clinical definitions limit ecological comparison. We used a common native classifier-assignment definition to study community structure at two resolutions: between diagnoses and within tuberculosis by drug-resistance status.

## Methods

We studied 400 unique PRJNA1056765 BALF patients across four published diagnoses and 130 unique PRJCA046985 BALF subjects with Drug_Resistance or Drug_Sensitive tuberculosis. Cohorts were analyzed independently using species direct-assigned Kraken2 counts, a 10% within-cohort prevalence filter, exact CZM zero replacement, CLR transformation, Aitchison distance, 9,999-permutation PERMANOVA and paired residual-permutation PERMDISP. Richness, Shannon, Gini-Simpson, dominance and classified fraction were secondary. Prespecified sensitivity analyses used 5%/20% filters, addition of 0.5 to every retained feature, and one 10% Bray-Curtis comparator without zero replacement.

## Results

All 530 reports passed the frozen common-layer audit. The anchor and external inventories contained 5,198 and 4,888 observed species, with 166 species prevalent in at least 10% of each cohort. In the anchor, diagnosis explained [ANCHOR_AITCHISON_R2] of Aitchison variation (P=[ANCHOR_PERMANOVA_P]; PERMDISP P=[ANCHOR_PERMDISP_P]). In the external cohort, resistance status explained [EXTERNAL_AITCHISON_R2] (P=[EXTERNAL_PERMANOVA_P]; PERMDISP P=[EXTERNAL_PERMDISP_P]). [ONE_SENTENCE_SECONDARY_AND_ROBUSTNESS_SUMMARY_WITHOUT_OVERCLAIM].

## Conclusions

[SELECT_BRANCH_CONCLUSION: STRONG / MODEST / NULL / DISPERSION_QUALIFIED]. The common definition supports comparable measurement and taxonomic observability, while the different clinical contrasts preclude pooling, formal meta-analysis or a replication claim.
