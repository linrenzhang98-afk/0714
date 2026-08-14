# Methods draft

## Cohort and independent metadata

The source project contained 402 mapped published clinical WGS records. Two records (SRR27343810 and SRR27343463) had size_MB=0 and no reads available, leaving 400 analyzable records. The analysis cohort comprised 400 unique runs, 400 unique BioSamples, and 400 unique patient identifiers. Frozen production Kraken2/Bracken results were complete for all 400. Published diagnosis was obtained from the checked-in clinical mapping and comprised bacterial infection (n=114), fungal infection (n=78), lung cancer (n=122), and pulmonary tuberculosis (n=86). No abundance-derived label was used as an independent phenotype.

## Taxonomic inputs and QC

Species-level Bracken relative abundance was primary; genus-level analysis was sensitivity. Six prespecified background/non-target labels were excluded before microbial community analysis, and the remaining profiles were closed to unit sum. QC flags were: classified fraction <0.5%; Bracken-assigned reads <1,000; observed species ≤2; or robust outlier status (absolute median-absolute-deviation z score >3.5) for log10 total reads, classified fraction, richness, or dominant-species abundance. A total of 281 samples had at least one flag. Flags were annotations, not deletion criteria: the primary cohort remained n=400, while the 119 samples without flags formed the prespecified strict-QC sensitivity cohort. This dual-track design avoided complete-case deletion of a non-random low-information phenotype while testing robustness.

## Diversity and community composition

Observed species, Shannon diversity, Simpson diversity, and Pielou evenness were calculated per sample. Bray–Curtis distances were calculated from relative abundance. For Aitchison analysis, a recorded pseudocount was applied before CLR transformation (see methods/parameters.json). Principal coordinate analysis summarized each distance matrix. Published-diagnosis PERMANOVA used 9,999 permutations constrained within the published cohort field; every PERMANOVA was paired with PERMDISP. Effect size (R²) and dispersion were interpreted before p values. The complete analysis was repeated in the strict-QC cohort.

## Differential species analysis

The frozen species analysis used prevalence ≥10%, effect-size reporting, cohort-stratified permutation p values, BH FDR, and diagnosis-specific CLR means. The strict-QC analysis used the same frozen feature set and parameters. No threshold or group was changed after inspecting results.

## Exploratory structure and selected functional review

Hierarchical community clustering was explored for k=2–10 using Bray–Curtis and Aitchison representations. Silhouette and cross-metric adjusted Rand index were used to evaluate stability; clusters were termed exploratory community states. CLR taxon associations were descriptive and not interpreted as ecological interactions. The fixed 30 deep-review samples were mapped into the 400-sample space and compared descriptively with the other 370. HUMAnN gene-family and pathway results were reviewed only as a selected functional supplement, including pathway annotation-dropout sensitivity at n=30, n=24, and n=23. No functional result was extrapolated to the 400-run cohort.

## Reproducibility

All manuscript values derive from checked-in frozen result tables. Figure source TSVs, table TSVs, legends, consistency checks, input hashes, and parameters accompany the package. The package builder performs no new inferential test.
