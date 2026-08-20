# Title options

1. **Compositional robustness reveals small diagnosis-associated variation and continuous heterogeneity in BALF metagenomes** — preferred title
2. Diagnosis explains a small and analysis-dependent fraction of variation in cross-disease BALF metagenomes
3. Prespecified compositional analysis bounds diagnosis-associated variation in BALF metagenomes
4. Feature definition and dispersion shape cross-disease comparisons of BALF metagenomes
5. Analytical robustness of diagnosis-associated heterogeneity in bronchoalveolar lavage metagenomes

# Compositional robustness reveals small diagnosis-associated variation and continuous heterogeneity in BALF metagenomes

## Abstract

### Background

Bronchoalveolar lavage fluid metagenomes from patients with pulmonary infections and lung cancer vary within as well as between diagnoses. Quantifying the diagnosis-associated component requires methods that respect compositional data, distinguish centroid from dispersion effects, and expose dependence on feature definition and quality-control populations.

### Methods

We performed a secondary compositional robustness reanalysis of 400 downloadable BALF DNA runs from PRJNA1056765. The primary analysis tested four-level published diagnosis in a prespecified 30-species Aitchison space with 9,999 permutations restricted within the published training/test split. PERMANOVA was paired with PERMDISP. A frozen 18-cell sensitivity grid varied prevalence-defined feature space, two zero-replacement choices, Aitchison versus Bray–Curtis distance, and a separate n=119 pipeline-dependent sensitivity population. Earlier frozen clustering outputs were used to assess representation stability.

### Results

In the full-cohort 30-species Aitchison anchor, diagnosis accounted for 1.94% of compositional variation (R²=0.01941; permutation P=0.0001), with no evidence of differential dispersion (PERMDISP P=0.487). The alternative prespecified pseudocount changed R² by 0.00033 and retained the same dispersion qualification. Across prevalence-defined feature spaces, full-cohort Aitchison R² ranged from 0.00179 to 0.01941, and the 90-species cells showed differential dispersion. Every full-cohort Bray–Curtis cell was dispersion-qualified. Estimates in the n=119 pipeline-dependent sensitivity population described a different selected population and ranged more widely. Clustering was representation-dependent: the best Bray–Curtis silhouette occurred at the tested k=10 boundary, whereas Bray–Curtis and Aitchison clusterings had adjusted Rand indices near zero across k=2–10.

### Conclusions

Diagnosis contributes a statistically detectable but very small conditional component of BALF composition in the frozen anchor. This estimate is insensitive to the two tested zero replacements but depends more strongly on feature space, distance metric, and analytical population. The data support continuous, representation-dependent community heterogeneity rather than a metric-stable ecotype solution under the tested design.

## Introduction

Bronchoalveolar lavage fluid provides a window onto the lower respiratory tract, where microbial communities are shaped by immigration, elimination, growth conditions, host responses, treatment, and disease. Healthy-airway studies established topographical continuity between upper and lower respiratory sites while also showing spatially structured lower-airway communities [1–4]. In disease cohorts, oral-taxon enrichment and community composition have been associated with inflammatory phenotypes and clinical outcomes [5–10]. These observations motivate cross-disease comparisons, but they also show why a diagnostic label is unlikely to capture most community variation.

BALF is a low-biomass specimen. Reagent contaminants, well-to-well transfer, bronchoscope and procedural effects, and the relation between microbial and host sequence yield can materially influence observed profiles [11–14]. Negative controls and explicit provenance are therefore central to interpretation. Bioinformatic choices add another layer. Taxonomic classifiers and reference databases differ in coverage and assignment, while filtering changes which parts of the sparse community enter an analysis [15–18]. A secondary analysis can test the stability of a result within its own frozen pipeline, but cross-pipeline differences remain ambiguous until upstream equivalence is demonstrated.

Microbiome profiles are also compositions. Centered log-ratio transformation and Aitchison distance represent relative information in Euclidean geometry, but zeros require an explicit replacement rule [19–22]. Distance-based tests introduce a separate concern: PERMANOVA can respond to differences in multivariate location, dispersion, or both, making paired dispersion assessment necessary [23,24]. In large cohorts, a small effect may produce a low permutation P value, so the variance component and its stability are more informative than significance alone [25–27].

Han et al. reported disease-associated BALF metagenomic patterns and internally tested diagnostic models in PRJNA1056765, while Tang et al. described the 402-patient multi-omic resource, controls, processed data, and code [28,29]. Their ecological analyses used the 284-patient training population. We used the 400 downloadable DNA runs to ask a narrower question: how much of cross-disease BALF composition is conditionally associated with published diagnosis under a prespecified compositional analysis, and how stable is that estimate to zero replacement, feature definition, metric, dispersion, and a pipeline-dependent sensitivity population? We further examined whether previously frozen cluster solutions were stable across Aitchison and Bray–Curtis representations. The study is an analytical robustness reanalysis of the shared source cohort, not a reconstruction of the original upstream workflow.

## Results

### The shared source cohort supports a distinct analytical estimand

PRJNA1056765 contains 402 published patient records spanning bacterial infection, fungal infection, lung cancer, and pulmonary tuberculosis. Four hundred DNA runs were downloadable and available in the frozen taxonomic pipeline; two mapped records were unavailable. The primary analytical population therefore comprised 114 bacterial infection, 78 fungal infection, 122 lung cancer, and 86 pulmonary tuberculosis samples. Han et al. used 284 records for ecological analyses and a fixed 284/118 split for diagnostic modelling. Our primary estimand was instead a four-level diagnosis omnibus across all 400 available runs, with the published split used only to restrict permutations (Fig. 1).

The current and published pipelines share broad preprocessing and Kraken2/Bracken taxonomic assignment, but exact database builds, parts of filtering, operational negative-control handling, feature scope, and statistical contrasts could not be made equivalent. The cohort is shared, whereas the analytical populations and estimands are not. The n=119 subset generated by the frozen local QC rules was consequently treated only as a pipeline-dependent sensitivity population.

### Diagnosis accounts for a very small component of full-cohort Aitchison variation

The exact anchor replay retained 30 species detected in at least 10% of the 400 samples. Using half the smallest positive retained abundance for zero replacement, four-level diagnosis explained 1.94% of Aitchison variation (R²=0.0194095; permutation P=0.0001). The paired dispersion test was unqualified (PERMDISP P=0.487). The exact replay recovered the locked statistics, feature order, pseudocount, and seeds from the frozen input hashes. This establishes computational reproducibility of the anchor within the current pipeline.

The magnitude, rather than the low permutation P value, defines the biological scale of the result. Approximately 98% of the distance variation remained outside the conditional diagnosis component captured by this omnibus model. Diagnosis was therefore detectable but accounted for a very small share of compositional heterogeneity.

### Zero replacement has little influence within the 30-species feature space

The second prespecified zero replacement used one tenth of the minimum positive retained abundance. In the same 30-species space and full cohort, it produced R²=0.0190746, an absolute change of 0.0003349 from the anchor (Fig. 2A). Its paired PERMDISP result was also unqualified (P=0.4677). Thus, the diagnosis-associated variance estimate and its dispersion interpretation were nearly identical under the two tested replacements. This comparison isolates zero replacement because the samples, features, metric, model, and permutation scheme were unchanged.

### Feature space changes both effect magnitude and dispersion qualification

The 5%, 10%, and 20% prevalence rules retained 90, 30, and 2 species, respectively. In the full cohort, 90-species Aitchison R² values were 0.0163698 and 0.0158287 for the two replacements. Both cells showed differential dispersion (PERMDISP P=0.0145 and 0.0187). The 30-species values were 0.0194095 and 0.0190746 without differential dispersion. At 20% prevalence, only two species remained, and R² fell to 0.0019795 and 0.0017942; neither cell was dispersion-qualified (Fig. 2A; Supplementary Table S1).

These are discrete, prespecified analytical spaces rather than points along a biological dose-response curve. Their contrast shows feature-space dependence: changing which taxa defined the geometry had more influence on the estimated variance component and dispersion qualification than changing the pseudocount within a fixed space.

### The pipeline-dependent sensitivity population defines a different estimation boundary

The frozen QC rules selected 119 samples comprising 42 bacterial infection, 19 fungal infection, 36 lung cancer, and 22 pulmonary tuberculosis cases. Across its six Aitchison cells, diagnosis-associated R² ranged from 0.0041007 to 0.0695841 (Fig. 2B). The 90-species values were 0.0591900 and 0.0586724 without differential dispersion. The 30-species values were 0.0695841 and 0.0691248, also without differential dispersion. The two-species values were 0.0041007 and 0.0046211, and both were dispersion-qualified.

Because the QC rules change the sample population and diagnosis composition, these values answer a different conditional question from the n=400 analysis. Their wider range sets a pipeline-dependent sensitivity boundary; it is not a same-estimand before/after comparison. The within-feature-space resemblance of the two pseudocount estimates remained visible in this population.

### Bray–Curtis comparisons are dispersion-sensitive in the full cohort

Full-cohort Bray–Curtis R² values were 0.0263302, 0.0153390, and 0.0096564 in the 90-, 30-, and two-species spaces. All three paired PERMDISP tests were below 0.05 (P=0.0001, 0.0009, and 0.0256; Supplementary Fig. S1). These tests therefore describe diagnosis-associated differences in multivariate location and/or dispersion, not an unqualified centroid shift. In the n=119 population, Bray–Curtis R² values were 0.0638835, 0.0607394, and 0.0796114; the 30- and two-species cells were dispersion-qualified, whereas the 90-species cell was not. Metric choice consequently altered both estimated magnitude and the qualification required for interpretation.

### Community partitions are not stable across representations

Average-linkage clustering was evaluated across k=2–10 using the previously frozen Bray–Curtis and Aitchison distances. Bray–Curtis silhouette values ranged from 0.4698 to 0.5167 and reached their maximum at k=10, the upper tested boundary. Aitchison silhouette values declined from 0.4485 at k=2 to 0.3829 at k=10. Despite moderate within-representation silhouettes, agreement between the two clusterings was poor: adjusted Rand indices ranged from −0.00844 to 0.00022 (Fig. 3; Supplementary Table S6). The tested representations therefore did not identify a metric-stable ecotype solution. The pattern is more consistent with continuous or representation-dependent heterogeneity than with a discrete partition that persists across reasonable geometries.

## Methods

### Study design and source cohort

We conducted a secondary compositional robustness reanalysis of PRJNA1056765. Published metadata assigned 402 patients to bacterial infection, fungal infection, lung cancer, or pulmonary tuberculosis [28,29]. Four hundred BALF DNA runs had downloadable reads and complete frozen production records. Each run mapped to one BioSample and one patient. The two unavailable records were documented as a data-availability difference. Published training/test assignment was retained for restricted permutation; abundance-derived labels were not used as phenotypes.

The analysis specification, executable, input hashes, feature list, seeds, and interpretation rules were version-locked before computation. Full hashes and repository provenance are provided in Supplementary Methods and the v5 manifest. No sensitivity cell, contrast, or interpretation rule was added after results were inspected.

### Taxonomic matrix and feature spaces

The checked-in species-level Bracken fraction matrix was generated after local host-read removal and Kraken2/Bracken processing. Six explicit non-target labels matching *Homo sapiens*, *Arabidopsis*, *Benincasa*, *Camelina*, *Cucurbita*, or *Toxoplasma* were excluded, and retained values were closed to unit sum within each sample. Exact equivalence to the database build and control-handling rules of Han et al. was not established.

Species prevalence was defined in the full 400-sample cohort before population-specific analysis. Prespecified thresholds of 5%, 10%, and 20% required detection in at least 20, 40, and 80 samples and retained 90, 30, and 2 species. These memberships were reused unchanged in the n=119 population.

### Aitchison and Bray–Curtis analyses

For Aitchison analysis, zeros were replaced by either half the smallest positive abundance in the retained feature space (P1) or one tenth of that minimum (P2). Profiles were centered log-ratio transformed, and Euclidean distance in CLR space defined Aitchison distance [19–22]. Bray–Curtis analysis retained observed zeros and renormalized relative abundance after feature filtering.

Diagnosis was tested using a pooled PERMANOVA statistic with 9,999 permutations. Labels were shuffled within the published training and test strata and reconstructed as a single permuted vector. Every cell was paired with PERMDISP using the same samples, distance, groups, strata, and permutation count [23,24]. The primary anchor used the 10% feature space, P1 zero replacement, and the full cohort. Its frozen pseudocount was 1.0097644219603566×10⁻⁵.

### Frozen sensitivity design

The 18-cell grid crossed three feature spaces with P1 Aitchison, P2 Aitchison, or Bray–Curtis analysis in the n=400 primary population and n=119 pipeline-dependent sensitivity population. The anchor replay served as an integrity check. P1 versus P2 within a feature space assessed zero-replacement sensitivity; prevalence-defined spaces assessed feature dependence; Bray–Curtis provided a metric and dispersion comparator; and n=119 cells described a selected population. Cells were not pooled or ranked by statistical result.

The sensitivity population contained samples without any of the prespecified flags: classified fraction below 0.5%, fewer than 1,000 estimated Bracken-assigned reads, observed richness of two or fewer, or an absolute robust median-absolute-deviation z score above 3.5 for log10 total reads, classified fraction, richness, or dominant-species abundance. The primary analysis retained all 400 samples.

### Clustering and taxon results

Clustering results were taken from the existing frozen analysis and were not recomputed. Average-linkage hierarchical clustering was evaluated at k=2–10 for Bray–Curtis and Aitchison distances. Silhouette summarized within-representation separation, and adjusted Rand index measured agreement between representations [30,31]. Clusters were treated as exploratory abundance-derived partitions.

Species-association results in Supplementary Table S5 were also inherited from the earlier frozen analysis. They used a 10% prevalence feature set, four-group Kruskal–Wallis statistics, split-restricted permutation P values, Benjamini–Hochberg correction, epsilon-squared effect sizes, and a sensitivity-population comparison. They were retained for audit transparency and were not used to define the primary community analysis or generate an ecological score.

### Interpretation and reporting

PERMANOVA R² was the principal effect-size estimate. Under the locked interpretation rule, R² below 0.05 was described as very small and 0.05 to below 0.10 as small. A cell was dispersion-qualified when PERMDISP P<0.05. Such results were described as location and/or dispersion differences. All 18 cells were reported irrespective of P value, R², or PERMDISP result. Statistical calculations were performed by the frozen executable; the present figure and manuscript build only formatted checked-in outputs.

## Discussion

Published diagnosis explained a detectable but very small share of BALF compositional variation in the frozen full-cohort anchor. The 1.94% estimate was almost unchanged by the two prespecified zero replacements, while feature definition, distance metric, and analytical population had greater influence on magnitude or dispersion qualification. Together with the absence of cross-metric cluster agreement, these results describe a heterogeneous lower-airway ecosystem in which broad diagnosis contributes one limited axis of variation.

The distinction between statistical detection and effect size is central in a cohort of this size. Permutation P=0.0001 indicates that the observed grouping was unlikely under the restricted-label null, but it does not make 1.94% a large explanatory component. Microbiome benchmarking studies likewise show that sample size, data characteristics, preprocessing, and method choice shape statistical calls [25–27]. Reporting R² beside its uncertainty and sensitivity context prevents a low P value from becoming an inflated biological narrative.

PERMANOVA and PERMDISP answered complementary questions. The primary Aitchison anchor was not dispersion-qualified, whereas every full-cohort Bray–Curtis comparison was. Bray–Curtis emphasizes abundance differences in the simplex and can reflect changes in within-group spread; Aitchison distance represents log-ratio information after zero replacement [19,23,24]. We therefore interpret the Bray–Curtis cells as combined location and/or dispersion results. Their significance cannot independently establish sharper disease centroids.

Within the 30-species geometry, reducing the zero replacement fivefold changed R² by only 0.00033 and left the dispersion conclusion unchanged. That result is useful but deliberately local: it evaluates two prespecified replacements, not all possible zero models. Feature filtering had a larger impact. Moving from 90 to 30 to two species changed the subcomposition being compared and, at 5% prevalence, changed dispersion qualification. Filtering sparse microbiome features may improve stability or remove noise, but it also changes the estimand and must be reported as an analytical choice rather than a biological gradient [20–22,25].

The n=119 results reinforce the importance of population definition in low-biomass respiratory samples. Low microbial yield and laboratory background can alter diversity and distance estimates, making quality information indispensable [11–14]. Yet the local flag rules do not create a biologically privileged cohort. They select a population with different technical characteristics and group composition. Its estimates therefore bound pipeline dependence rather than validate the n=400 result.

Community clustering provided a related view of heterogeneity. Bray–Curtis silhouette increased to its maximum at the upper k boundary, Aitchison silhouette favored k=2, and the adjusted Rand index was approximately zero throughout. A cluster solution that changes almost completely with representation is a weak basis for named ecotypes [30,31]. Lower-airway communities may still contain clinically informative structure, but the tested frozen outputs support continuous or representation-dependent variation rather than a stable discrete taxonomy.

Our result and the Han et al. report address different estimands. Han et al. examined the n=284 training population, cancer-versus-infection and pairwise contrasts, broader microbial feature domains, and diagnostic modelling [28]. We tested a four-level omnibus in 400 downloadable DNA runs with a locally frozen bacterial species matrix. Because database versions, control handling, parts of filtering, and feature definitions remain incompletely reconstructed, taxon overlap or mismatch is a pipeline/statistical concordance or discrepancy. The present contribution is the bounded effect-size and robustness analysis, not a claim that the original workflow was reproduced.

Several limitations remain. The study reuses a single public cohort and therefore offers no external biological replication. The local matrix cannot resolve viability or transcriptional activity, and it cannot separate immigration, persistence, or host response. Negative controls described with the source dataset were not operationally reconstructed in the local pipeline. The diagnosis categories are broad, treatment and clinical covariates may contribute unmodelled heterogeneity, and the 20% threshold leaves only two species. Finally, the frozen sensitivity grid samples a small, prospectively fixed set of reasonable choices rather than the full universe of pipelines.

In summary, diagnosis contributes a small conditional variance component to cross-disease BALF composition. Its full-cohort 30-species estimate is stable to the tested zero replacements, whereas feature space, metric, dispersion, and population definition set important interpretive boundaries. Community partitions are not stable across the tested representations. Effect-size-centered, prespecified reporting therefore provides a more defensible account of cross-disease lower-airway heterogeneity than a single significant community comparison.

## Data and code availability

Raw data are available from NCBI BioProject PRJNA1056765. The source articles describe processed data and released code [28,29]. The current analysis specification, frozen executable, input hashes, complete 18-cell grid, figure source data, and build script are versioned in the project repository. Repository identifiers and SHA-256 records are listed in the Supplementary Reproducibility Record.

## Figure legends

### Figure 1. Cohort provenance and analytical design

The published source cohort contained 402 patients. Four hundred DNA runs were downloadable; two mapped records were unavailable. Han et al. used 284 records for ecological/training analyses and 118 for internal testing. The current study uses n=400 for the primary four-level omnibus and n=119 for a separate pipeline-dependent sensitivity estimand. Stacked bars show diagnosis composition. Arrows denote provenance, not independent replication.

### Figure 2. Prespecified compositional robustness

PERMANOVA R² for all six Aitchison cells in (A) the full primary population and (B) the pipeline-dependent sensitivity population. Each prevalence rule defines a discrete feature space; P1 and P2 denote the two prespecified zero replacements. The anchor is the full-cohort 30-species P1 cell. Daggers mark paired PERMDISP P<0.05. The panels have a common scale but represent different populations and estimands. No line connects prevalence-defined spaces.

### Figure 3. Community heterogeneity and cluster instability

(A) Silhouette values for average-linkage Bray–Curtis and Aitchison clustering across k=2–10. The highest Bray–Curtis silhouette occurs at k=10, the tested boundary, while the highest Aitchison value occurs at k=2. (B) Adjusted Rand index between Bray–Curtis and Aitchison assignments remains near zero across k, indicating poor agreement between representations. Lines connect the ordered candidate k values, not prevalence thresholds.

### Supplementary Figure S1. Bray–Curtis and dispersion comparator

PERMANOVA R² for all Bray–Curtis cells in the full primary and pipeline-dependent sensitivity populations. Daggers mark paired PERMDISP P<0.05. All full-cohort cells are dispersion-qualified and are interpreted as diagnosis-associated differences in location and/or dispersion.

## References

1. Charlson ES, et al. Topographical continuity of bacterial populations in the healthy human respiratory tract. *Am J Respir Crit Care Med*. 2011;184:957–963. doi:10.1164/rccm.201104-0655OC.
2. Morris A, et al. Comparison of the respiratory microbiome in healthy nonsmokers and smokers. *Am J Respir Crit Care Med*. 2013;187:1067–1075. PMID:23491408.
3. Bassis CM, et al. Analysis of the upper respiratory tract microbiotas as the source of the lung and gastric microbiotas in healthy individuals. *mBio*. 2015;6:e00037. doi:10.1128/mBio.00037-15.
4. Dickson RP, et al. Bacterial topography of the healthy human lower respiratory tract. *mBio*. 2017;8:e02287-16. PMID:28196961.
5. Segal LN, et al. Enrichment of lung microbiome with supraglottic taxa is associated with increased pulmonary inflammation. *Microbiome*. 2013;1:19. doi:10.1186/2049-2618-1-19.
6. Segal LN, et al. Enrichment of the lung microbiome with oral taxa is associated with lung inflammation of a Th17 phenotype. *Nat Microbiol*. 2016;1:16031. doi:10.1038/nmicrobiol.2016.31.
7. Huang YJ, et al. Airway microbiome dynamics in exacerbations of chronic obstructive pulmonary disease. *J Clin Microbiol*. 2014;52:2813–2823. doi:10.1128/JCM.00035-14.
8. Tsay JJ, et al. Airway microbiota is associated with upregulation of the PI3K pathway in lung cancer. *Am J Respir Crit Care Med*. 2018;198:1188–1198. doi:10.1164/rccm.201710-2118OC.
9. Tsay JJ, et al. Lower airway dysbiosis affects lung cancer progression. *Cancer Discov*. 2021;11:293–307. doi:10.1158/2159-8290.CD-20-0263.
10. Sulaiman I, et al. Functional lower airways genomic profiling of the microbiome to capture active microbial metabolism. *Eur Respir J*. 2021;58:2003434. doi:10.1183/13993003.03434-2020.
11. Salter SJ, et al. Reagent and laboratory contamination can critically impact sequence-based microbiome analyses. *BMC Biol*. 2014;12:87. doi:10.1186/s12915-014-0087-z.
12. Drengenes C, et al. Laboratory contamination in airway microbiome studies. *BMC Microbiol*. 2019;19:187. doi:10.1186/s12866-019-1560-1.
13. Minich JJ, et al. Quantifying and understanding well-to-well contamination in microbiome research. *mSystems*. 2019;4:e00186-19. doi:10.1128/mSystems.00186-19.
14. Einarsson GG, et al. Community dynamics and the lower airway microbiota in stable chronic obstructive pulmonary disease, smokers and healthy non-smokers. *Thorax*. 2016;71:795–803. doi:10.1136/thoraxjnl-2015-207235.
15. Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. *Genome Biol*. 2019;20:257. doi:10.1186/s13059-019-1891-0.
16. Lu J, et al. Bracken: estimating species abundance in metagenomics data. *PeerJ Comput Sci*. 2017;3:e104. doi:10.7717/peerj-cs.104.
17. McIntyre ABR, et al. Comprehensive benchmarking and ensemble approaches for metagenomic classifiers. *Genome Biol*. 2017;18:182. doi:10.1186/s13059-017-1299-7.
18. Ye SH, et al. Benchmarking metagenomics tools for taxonomic classification. *Cell*. 2019;178:779–794. doi:10.1016/j.cell.2019.07.010.
19. Aitchison J. The statistical analysis of compositional data. *J R Stat Soc Series B*. 1982;44:139–177. doi:10.1111/j.2517-6161.1982.tb01195.x.
20. Martín-Fernández JA, Barceló-Vidal C, Pawlowsky-Glahn V. Dealing with zeros and missing values in compositional data sets using nonparametric imputation. *Math Geol*. 2003;35:253–278. doi:10.1023/A:1023866030544.
21. Fernandes AD, et al. Unifying the analysis of high-throughput sequencing datasets by compositional data analysis. *Microbiome*. 2014;2:15. doi:10.1186/2049-2618-2-15.
22. Gloor GB, et al. Microbiome datasets are compositional: and this is not optional. *Front Microbiol*. 2017;8:2224. doi:10.3389/fmicb.2017.02224.
23. Anderson MJ. A new method for non-parametric multivariate analysis of variance. *Austral Ecol*. 2001;26:32–46. doi:10.1111/j.1442-9993.2001.01070.pp.x.
24. Anderson MJ. Distance-based tests for homogeneity of multivariate dispersions. *Biometrics*. 2006;62:245–253. doi:10.1111/j.1541-0420.2005.00440.x.
25. Weiss S, et al. Normalization and microbial differential abundance strategies depend upon data characteristics. *Microbiome*. 2017;5:27. doi:10.1186/s40168-017-0237-y.
26. Nearing JT, et al. Microbiome differential abundance methods produce different results across 38 datasets. *Nat Commun*. 2022;13:342. doi:10.1038/s41467-022-28034-z.
27. McMurdie PJ, Holmes S. Waste not, want not: why rarefying microbiome data is inadmissible. *PLoS Comput Biol*. 2014;10:e1003531. doi:10.1371/journal.pcbi.1003531.
28. Han D, et al. Metagenomic fingerprints in bronchoalveolar lavage differentiate pulmonary diseases. *npj Digit Med*. 2025. doi:10.1038/s41746-025-01977-5.
29. Tang H, et al. Bronchoalveolar lavage fluid metagenomic datasets. *Sci Data*. 2025. doi:10.1038/s41597-025-06171-6.
30. Rousseeuw PJ. Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *J Comput Appl Math*. 1987;20:53–65. doi:10.1016/0377-0427(87)90125-7.
31. Hubert L, Arabie P. Comparing partitions. *J Classif*. 1985;2:193–218. doi:10.1007/BF01908075.
