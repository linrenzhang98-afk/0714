# Journal-Neutral Full Manuscript Draft

## Title

Diagnosis-associated pathogen signatures in BALF mNGS distinguish pulmonary infections from lung cancer disease controls

## Running Title

BALF mNGS pathogen-marker prioritization

## Abstract

Bronchoalveolar lavage fluid metagenomic next-generation sequencing can support broad pathogen detection in pulmonary disease, but public mNGS datasets require careful metadata reconstruction and conservative interpretation before they can inform experimental validation. We re-analyzed PRJNA1056765, a public BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. After excluding unavailable public WGS records, the final cohort contained 400 analyzable DNA WGS/mNGS runs. Kraken2/Bracken profiling and group-level species detection testing prioritized `Pseudomonas aeruginosa` in bacterial infection, `Mycobacterium tuberculosis` in pulmonary tuberculosis, and `Aspergillus fumigatus` in fungal infection as the strongest validation candidates. A 30-sample deep-review set retained the same top pathogen after QC re-analysis. Host-removal and AMRFinderPlus screening completed for all deep-review samples and detected no AMR hit rows in capped host-removed short-read subsets. These findings support a focused bioinformatics-led short project in which public BALF mNGS data are used to prioritize pathogen markers for targeted validation, while antimicrobial-resistance and clinical diagnostic claims remain outside the supported scope.

## Keywords

bronchoalveolar lavage fluid; metagenomic next-generation sequencing; pulmonary infection; pathogen prioritization; Kraken2; Bracken; public-data re-analysis

## Introduction

Pulmonary infections and malignancy can produce overlapping clinical and radiological presentations. Bronchoalveolar lavage fluid (BALF) metagenomic next-generation sequencing (mNGS) provides a broad, culture-independent strategy for microbial detection in this setting, and public BALF mNGS datasets can support secondary analyses beyond their original study questions. A practical use of such datasets is not necessarily broad microbiome discovery, but the prioritization of pathogen markers that can be tested in focused local validation studies.

Public mNGS re-analysis also has clear risks. Clinical labels may require reconstruction from supplementary metadata, some public sequencing records may be unavailable, and low classified fractions can make background taxa appear prominent. These problems are especially relevant when the analysis is intended to support a short translational project, where overclaiming diagnostic performance or antimicrobial resistance from public metagenomic data would weaken the study.

PRJNA1056765 is a public BALF clinical mNGS BioProject linked to pulmonary disease labels, including bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. We re-analyzed this dataset to reconstruct analyzable clinical groups, profile species-level pathogen spectra, prioritize validation candidates, and define interpretation boundaries using selected-sample QC re-analysis and host-removal/AMR screening.

## Methods

### Study design

This study was a retrospective public-data re-analysis of BALF mNGS data from PRJNA1056765. The main objective was to identify diagnosis-associated pathogen signals that could support targeted validation planning. Lung cancer BALF samples were treated as disease controls because the public dataset did not include true healthy BALF controls.

### Public data and metadata reconstruction

SRA RunInfo records for PRJNA1056765 were integrated with published clinical labels from the associated main article and data descriptor supplementary materials. DNA WGS/mNGS records with available public data were retained for analysis. RNA-seq and metatranscriptomic records were not included in the DNA WGS/mNGS analysis set.

The final analyzable cohort contained 400 DNA WGS/mNGS runs: 114 bacterial infection runs, 78 fungal infection runs, 86 pulmonary tuberculosis runs, and 122 lung cancer disease-control runs. Two expected WGS records, SRR27343810 and SRR27343463, had `size_MB=0` in SRA RunInfo and were treated as unavailable public records rather than analysis failures.

### First-pass taxonomic profiling

All analyzable DNA WGS/mNGS runs were processed with a first-pass Kraken2/Bracken workflow. The analysis summarized classified fraction, top detected species, top-pathogen fraction, and species-level Bracken fractions for each run. Full result tables were retained for transparency, but recurrent host, plant-associated, or low-specificity taxa were not used as disease-associated pathogen findings unless supported by clinical coherence and group-level enrichment.

### Group-level differential detection

Species-level detection was compared between each diagnosis group and all remaining groups using two-sided Fisher exact testing. Benjamini-Hochberg false-discovery-rate correction was applied for multiple testing. Candidate pathogens were prioritized using statistical support, clinical coherence, and practical feasibility for targeted validation.

### Deep-review QC re-analysis

Thirty selected pathogen-positive samples underwent deep-review QC re-analysis. The selected set covered Acinetobacter, Candida, Enterobacterales, Haemophilus, Mycobacteria, Pseudomonas, Staphylococcus, Stenotrophomonas, and Streptococcus groups. The primary endpoint was whether the top pathogen call remained unchanged after the additional QC pass.

### Host-removal and exploratory AMR screen

The 30 deep-review samples were evaluated with host-removal and AMRFinderPlus screening on capped host-removed short-read subsets. AMRFinderPlus hit rows, if present, were considered exploratory genotypic signals. Absence of AMRFinderPlus hits was not interpreted as absence of antimicrobial resistance.

### Validation planning

Candidate validation markers were assigned according to clinical coherence, group-enrichment evidence, and feasibility. The minimal short-project panel prioritizes `Pseudomonas aeruginosa` and `Aspergillus fumigatus`. `Cryptococcus neoformans` is optional depending on fungal-positive sample availability. `Mycobacterium tuberculosis` is retained as a strong bioinformatic endpoint but should be wet-lab validated only if approved tuberculosis biosafety and clinical workflows are already available.

## Results

### Public-data reconstruction defined a four-group BALF mNGS cohort

We reconstructed the PRJNA1056765 analysis cohort by integrating public SRA RunInfo records with published clinical labels. The analyzable DNA WGS/mNGS cohort contained 400 runs, including 114 bacterial infection runs, 78 fungal infection runs, 86 pulmonary tuberculosis runs, and 122 lung cancer runs (Table 1; Fig. 1). Two expected WGS records, SRR27343810 from the fungal infection group and SRR27343463 from the lung cancer group, had `size_MB=0` in SRA RunInfo and were therefore treated as unavailable public records rather than pipeline failures.

This reconstruction established lung cancer BALF samples as a disease-control comparator rather than a healthy reference group. All downstream interpretation therefore focused on diagnosis-associated pathogen spectra within diseased BALF samples.

### First-pass profiling showed low classified fractions but recoverable pathogen signals

First-pass Kraken2/Bracken profiling completed for all 400 analyzable DNA WGS/mNGS runs. The median classified fraction was 1.797%, with a range from 0.418% to 10.427%. Median classified fractions by clinical group were 1.9034% for bacterial infection, 1.5793% for fungal infection, 1.6587% for pulmonary tuberculosis, and 2.0530% for lung cancer.

These values indicate that the dataset is suitable for conservative pathogen prioritization, but not for overinterpreting weak low-abundance signals. Several recurrent taxa appeared broadly across the cohort, including host, plant-associated, and low-specificity species. These taxa were not used as biological findings.

### Diagnosis-group testing prioritized clinically coherent pathogen candidates

Species-level detection testing identified several diagnosis-associated candidates (Table 2; Fig. 2). `Pseudomonas aeruginosa` was the strongest bacterial infection-associated candidate, detected in 23 of 114 bacterial infection runs compared with a 0.02448 detection rate in the remaining groups (FDR 2.48792e-05). This signal supports `P. aeruginosa` as the highest-priority bacterial target for follow-up validation.

`Mycobacterium tuberculosis` was enriched in pulmonary tuberculosis, detected in 9 of 86 tuberculosis runs and absent from the comparison groups (FDR 0.000533876). This finding supports `M. tuberculosis` as a strong bioinformatic endpoint, although wet-lab validation is biosafety-dependent.

`Aspergillus fumigatus` was enriched in fungal infection samples, detected in 8 of 78 fungal infection runs compared with a 0.00932 detection rate in the remaining groups (FDR 0.0332815). `Cryptococcus neoformans` showed a weaker fungal-enrichment pattern, detected in 6 of 78 fungal infection runs compared with a 0.00621 detection rate in other groups (FDR 0.110067), and was retained as a secondary validation candidate.

### Deep-review re-analysis supported selected-call stability

To evaluate the stability of selected pathogen-positive calls, we deep-reviewed 30 samples spanning nine pathogen groups. All 30 selected samples retained the same top pathogen after QC re-analysis (Table 3; Fig. 4). Diagnosis coverage in this subset included bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer disease-control samples.

This result supports stability of selected high-priority calls under an additional QC pass. It does not imply that every first-pass call across the full cohort is equally robust.

### Host-removal and AMR screening defined a resistance-interpretation boundary

Host-removal and AMRFinderPlus screening completed for all 30 deep-review samples. AMRFinderPlus detected no AMR hit rows in the capped host-removed short-read subsets (Table 3; Fig. 4). This result indicates that the current public-data workflow does not support antimicrobial-resistance claims. It does not establish absence of resistance and does not replace culture, antimicrobial susceptibility testing, or targeted resistance validation.

## Discussion

This re-analysis positions PRJNA1056765 as a practical resource for pathogen-marker prioritization in BALF mNGS. The strongest findings converged on clinically coherent organisms, especially `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus`, each of which has a direct validation route. The project should therefore be framed as a focused bioinformatics-led prioritization study rather than a stand-alone diagnostic or antimicrobial-resistance analysis.

The main translational value is the connection between public mNGS signals and a feasible validation panel. `P. aeruginosa` is the clearest first validation target for bacterial infection, while `A. fumigatus` is the most defensible fungal target. `C. neoformans` can be included only if fungal-positive sample numbers are sufficient. `M. tuberculosis` should remain conditional because targeted validation depends on existing biosafety and approved clinical workflow capacity.

The deep-review and host-AMR analyses add guardrails. Stable top-pathogen calls in 30 selected samples support the selected candidate set, while the absence of AMRFinderPlus hits in capped host-removed subsets argues against making resistance claims. These checks improve the manuscript by defining what the public-data workflow can and cannot support.

Several alternative explanations need to be handled explicitly. Low classified fractions may reflect database composition, host background, reagent or environmental contamination, or nonspecific mapping. Recurrent broad-detection taxa should be treated as analytical background unless independently supported. The lung cancer group should be described as a disease-control comparator, not a healthy reference group.

## Limitations

This study is limited by public metadata reconstruction, two unavailable WGS records with `size_MB=0`, absence of healthy BALF controls, database dependence of Kraken2/Bracken profiling, low classified fractions, selected rather than full-cohort deep-review, and capped-subset AMR screening. Targeted wet-lab validation is required before translational or diagnostic claims can be made.

## Conclusion

PRJNA1056765 supports a focused public-data re-analysis for BALF mNGS pathogen-marker prioritization. The most defensible short-project validation targets are `P. aeruginosa` and `A. fumigatus`, with `M. tuberculosis` treated as biosafety-dependent. The current evidence supports candidate prioritization and robustness checking, not clinical diagnostic performance or antimicrobial-resistance inference.

## Table And Figure Callouts

- Table 1: Reconstructed cohort and analyzable run counts.
- Table 2: Prioritized pathogen candidates and validation markers.
- Table 3: Deep-review stability and host-AMR guardrail summary.
- Figure 1: Public-data reconstruction and analysis workflow.
- Figure 2: Diagnosis-associated pathogen spectra.
- Figure 3: Wet-lab validation candidate prioritization.
- Figure 4: Robustness checks and interpretation boundaries.

## Data And Code Availability Draft

This manuscript is based on public sequencing records from PRJNA1056765 and public clinical-label information reported in the associated publications and supplementary materials. Public summary outputs, analysis job descriptions, and manuscript preparation files are maintained in the GitHub repository. Raw FASTQ files, local databases, private runner configuration, and intermediate workstation outputs are not committed to the repository.

## Ethics Statement Draft

This study re-analyzed publicly available sequencing and metadata resources. Any future local validation using BALF samples should be conducted under appropriate institutional ethics approval, biosafety requirements, and local sample-use permissions.

## Author-Decision Placeholders

- Target journal: to be selected.
- Abstract style: unstructured by default; revise if journal requires structured format.
- Wet-lab validation status: not included in the current public-data-only draft.
- TB wet-lab validation: biosafety-dependent; keep as bioinformatic endpoint unless approved workflow exists.
