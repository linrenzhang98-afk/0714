# Manuscript Skeleton

## Working Title

Diagnosis-associated pathogen signatures in BALF mNGS distinguish pulmonary infections from lung cancer disease controls

## Short Running Title

BALF mNGS pathogen-marker prioritization

## Article Type

Bioinformatics-led brief report or short communication with targeted wet-lab validation.

## Abstract

Bronchoalveolar lavage fluid metagenomic next-generation sequencing can support broad pathogen detection in pulmonary disease, but public mNGS datasets require careful metadata reconstruction and conservative interpretation before they can inform experimental validation. We re-analyzed PRJNA1056765, a public BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. After excluding unavailable public WGS records, the final cohort contained 400 analyzable DNA WGS/mNGS runs. Kraken2/Bracken profiling and group-level species detection testing prioritized `Pseudomonas aeruginosa` in bacterial infection, `Mycobacterium tuberculosis` in pulmonary tuberculosis, and `Aspergillus fumigatus` in fungal infection as the strongest validation candidates. A 30-sample deep-review set retained the same top pathogen after QC re-analysis, supporting stability of selected calls. Host-removal and AMRFinderPlus screening completed for all deep-review samples and detected no AMR hit rows in capped host-removed short-read subsets. These findings support a focused bioinformatics-led short project in which public BALF mNGS data are used to prioritize pathogen markers for targeted validation, while antimicrobial-resistance and clinical diagnostic claims remain outside the supported scope.

## Keywords

- BALF
- mNGS
- pulmonary infection
- public-data re-analysis
- pathogen prioritization
- Kraken2
- Bracken

## Introduction

Pulmonary infections and malignancy can produce overlapping clinical and radiological presentations, and bronchoalveolar lavage fluid (BALF) metagenomic next-generation sequencing (mNGS) provides a broad, culture-independent route for microbial detection. Public BALF mNGS datasets are therefore valuable beyond their original study questions because they can be re-used to prioritize pathogen markers for focused validation.

However, public mNGS re-analysis is vulnerable to overinterpretation. Metadata may be incomplete, clinically relevant labels may require reconstruction from supplementary tables, and low classified fractions can amplify the importance of background or low-specificity taxa. These issues are especially important when the downstream goal is a short translational study, where the strongest project is usually not broad discovery but a small, defensible validation panel.

PRJNA1056765 provides a large BALF clinical mNGS resource with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. We re-analyzed this BioProject to reconstruct analyzable diagnosis groups, profile species-level pathogen spectra, prioritize wet-lab validation candidates, and define interpretation boundaries through selected-sample QC re-analysis plus host-removal/AMR screening.

## Methods

### Public-data reconstruction

SRA RunInfo records for PRJNA1056765 were integrated with published clinical labels from the associated article and data descriptor supplementary materials. DNA WGS/mNGS runs were retained when public records were available for analysis. Lung cancer BALF samples were treated as disease controls, not healthy controls.

### First-pass taxonomic profiling

Analyzable DNA WGS/mNGS runs were profiled using Kraken2 and Bracken. The analysis summarized classified fractions, species-level detections, and top-pathogen fractions by run and diagnosis group. Broadly recurrent host, plant-associated, or low-specificity taxa were kept in output tables but excluded from biological claim-building.

### Group-level candidate prioritization

Species detection was compared between each diagnosis group and the remaining groups using two-sided Fisher exact testing with Benjamini-Hochberg false-discovery-rate correction. Candidate species were ranked using statistical support, clinical coherence, and practical validation feasibility.

### Deep-review QC re-analysis

Thirty selected pathogen-positive samples spanning major pathogen groups underwent deep-review re-analysis. The main stability endpoint was whether the top pathogen remained the same after the additional QC pass.

### Host-removal and exploratory AMR screen

The 30 deep-review samples were further evaluated with host-removal and AMRFinderPlus screening on capped host-removed short-read subsets. This step was used only as an exploratory guardrail for genotypic resistance signals and was not treated as phenotypic antimicrobial susceptibility testing.

### Wet-lab validation planning

Validation targets were prioritized for a minimal qPCR/ddPCR-oriented panel. The shortest practical panel emphasizes `Pseudomonas aeruginosa` and `Aspergillus fumigatus`; `Cryptococcus neoformans` is optional depending on fungal-positive sample availability, and `Mycobacterium tuberculosis` is biosafety-dependent.

## Results

### Public-data reconstruction defined a four-group BALF mNGS cohort

We reconstructed the PRJNA1056765 analysis cohort by integrating public SRA RunInfo records with published clinical labels. The analyzable DNA WGS/mNGS cohort contained 400 runs, including 114 bacterial infection runs, 78 fungal infection runs, 86 pulmonary tuberculosis runs, and 122 lung cancer runs (Table 1; Fig. 1). Two expected WGS records, SRR27343810 from the fungal infection group and SRR27343463 from the lung cancer group, had `size_MB=0` in SRA RunInfo and were therefore treated as unavailable public records rather than pipeline failures.

### First-pass profiling showed low classified fractions but recoverable pathogen signals

First-pass Kraken2/Bracken profiling completed for all 400 analyzable runs. The median classified fraction was 1.797%, with a range from 0.418% to 10.427%. Median classified fractions by clinical group were 1.9034% for bacterial infection, 1.5793% for fungal infection, 1.6587% for pulmonary tuberculosis, and 2.0530% for lung cancer. These values support conservative pathogen prioritization but argue against overinterpreting weak low-abundance signals.

### Group-level testing prioritized clinically coherent pathogen candidates

Species-level detection testing identified diagnosis-associated candidates (Table 2; Fig. 2). `Pseudomonas aeruginosa` was enriched in bacterial infection, detected in 23 of 114 bacterial infection runs compared with a 0.02448 detection rate in the remaining groups (FDR 2.48792e-05). `Mycobacterium tuberculosis` was enriched in pulmonary tuberculosis, detected in 9 of 86 tuberculosis runs and absent from the comparison groups (FDR 0.000533876). `Aspergillus fumigatus` was enriched in fungal infection, detected in 8 of 78 fungal infection runs compared with a 0.00932 detection rate in the remaining groups (FDR 0.0332815). `Cryptococcus neoformans` showed a weaker fungal-enrichment pattern and was retained as a secondary candidate (FDR 0.110067).

### Deep-review re-analysis supported stability of selected top-pathogen calls

Thirty selected pathogen-positive samples spanning Acinetobacter, Candida, Enterobacterales, Haemophilus, Mycobacteria, Pseudomonas, Staphylococcus, Stenotrophomonas, and Streptococcus groups were deep-reviewed. All 30 retained the same top pathogen after QC re-analysis (Table 3; Fig. 4). This supports stability for selected high-priority calls but does not prove stability of every first-pass call in the full cohort.

### Host-removal and AMR screening defined a conservative resistance boundary

Host-removal and AMRFinderPlus screening completed for all 30 deep-review samples. AMRFinderPlus detected no AMR hit rows in the capped host-removed short-read subsets (Table 3; Fig. 4). This result does not establish absence of antimicrobial resistance; rather, it indicates that the current workflow does not support resistance claims.

## Discussion

This re-analysis positions PRJNA1056765 as a practical resource for pathogen-marker prioritization in BALF mNGS. The strongest findings converged on clinically coherent organisms, especially `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus`, each of which has a direct validation route. The project should therefore be framed as a focused bioinformatics-led prioritization study rather than a stand-alone diagnostic or antimicrobial-resistance analysis.

The main translational value is the connection between public mNGS signals and a feasible validation panel. `P. aeruginosa` is the clearest first validation target for bacterial infection, while `A. fumigatus` is the most defensible fungal target. `C. neoformans` can be included only if fungal-positive sample numbers are sufficient. `M. tuberculosis` should remain conditional because targeted validation depends on existing biosafety and approved clinical workflow capacity.

The deep-review and host-AMR analyses add guardrails. Stable top-pathogen calls in 30 selected samples support the selected candidate set, while the absence of AMRFinderPlus hits in capped host-removed subsets argues against making resistance claims. These checks improve the manuscript by defining what the public-data workflow can and cannot support.

## Limitations

This study is limited by public metadata reconstruction, two unavailable WGS records with `size_MB=0`, absence of healthy BALF controls, database dependence of Kraken2/Bracken profiling, low classified fractions, selected rather than full-cohort deep-review, and capped-subset AMR screening. Targeted wet-lab validation is required before translational or diagnostic claims can be made.

## Conclusion

PRJNA1056765 supports a focused public-data re-analysis for BALF mNGS pathogen-marker prioritization. The most defensible short-project validation targets are `P. aeruginosa` and `A. fumigatus`, with `M. tuberculosis` treated as biosafety-dependent. The current evidence supports candidate prioritization and robustness checking, not clinical diagnostic performance or antimicrobial-resistance inference.

## Main Table And Figure Callouts

- Table 1: Reconstructed cohort and analyzable run counts.
- Table 2: Prioritized pathogen candidates and validation markers.
- Table 3: Deep-review stability and host-AMR guardrail summary.
- Figure 1: Public-data reconstruction and analysis workflow.
- Figure 2: Diagnosis-associated pathogen spectra.
- Figure 3: Wet-lab validation candidate prioritization.
- Figure 4: Robustness checks and interpretation boundaries.

## Immediate Next Step

After target journal selection, convert this skeleton into journal-specific formatting and decide whether the abstract should be structured or unstructured.
