# Discussion, Limitations, And Abstract Draft

## One-Sentence Argument

In PRJNA1056765 BALF mNGS data, conservative public-data re-analysis can prioritize diagnosis-associated pathogen markers for targeted validation, but it should not be framed as a stand-alone diagnostic or antimicrobial-resistance study.

## Discussion Draft

This re-analysis positions PRJNA1056765 as a practical resource for pathogen-marker prioritization in bronchoalveolar lavage fluid (BALF) metagenomic next-generation sequencing (mNGS), rather than as an unrestricted microbiome discovery dataset. By reconstructing four clinically labelled groups and analyzing 400 DNA WGS/mNGS runs, the workflow identified diagnosis-associated pathogen spectra across bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer disease-control samples. The strongest findings converged on clinically coherent organisms, especially `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus`, each of which has a direct validation route using targeted molecular assays.

The main value of the analysis is its conservative link between public mNGS signals and short-project experimental feasibility. `P. aeruginosa` was the clearest bacterial infection-associated candidate and is therefore the most practical first validation target. `A. fumigatus` provides a defensible fungal target with group-level support, while `Cryptococcus neoformans` remains a secondary candidate because its signal was biologically plausible but did not reach the same statistical strength. `M. tuberculosis` showed a strong tuberculosis-associated signal, but its wet-lab validation should be treated as conditional because tuberculosis assays require established biosafety and clinical workflow approvals. This tiered interpretation is more defensible than treating all detected pathogens as equivalent discoveries.

The deep-review analysis strengthened selected pathogen calls by showing that all 30 selected samples retained the same top pathogen after QC re-analysis. This does not prove that every first-pass call in the 400-run cohort is robust, but it supports the reliability of the selected high-priority calls used for manuscript framing. The host-removal and AMRFinderPlus screen further clarified the boundary of the study. No AMRFinderPlus hit rows were detected in capped host-removed short-read subsets, which means the current workflow does not support antimicrobial-resistance claims. This negative result is still useful because it prevents overinterpretation and keeps the study focused on pathogen-marker prioritization.

Several alternative explanations need to be handled explicitly. First, low classified fractions across the cohort mean that weak low-abundance signals may reflect database composition, host background, reagent or environmental contamination, or nonspecific mapping rather than disease biology. Second, recurrent broad-detection taxa, including host, plant-associated, and low-specificity species, should be treated as analytical background unless supported by independent evidence. Third, the lung cancer group is a disease-control comparator and should not be described as a healthy reference. These constraints do not invalidate the prioritized pathogen signals, but they narrow the claim to clinically labelled diseased BALF samples.

This work should therefore be presented as a bioinformatics-led candidate prioritization study with a focused validation module. The most efficient validation route is to test `P. aeruginosa` and `A. fumigatus` first in independent or local BALF samples, with `C. neoformans` added only if fungal-positive sample numbers are sufficient. Tuberculosis validation can remain a bioinformatic endpoint unless the laboratory already has an approved assay and biosafety workflow. A positive validation result would support the public-data prioritization framework; a negative validation result would still be informative because it would define the limits of transferability from public BALF mNGS data to the local cohort.

## Limitations Draft

This study has several boundaries that should be stated directly. First, clinical labels were reconstructed from public and published metadata, and two expected WGS records were unavailable because their SRA RunInfo entries had `size_MB=0`. Second, the dataset contains diseased BALF samples and does not include a true healthy BALF control group. Lung cancer samples were therefore used as disease controls, not as healthy controls. Third, Kraken2/Bracken profiling is database-dependent, and the cohort showed low classified fractions, so biological interpretation was restricted to clinically coherent and statistically prioritized pathogen signals. Fourth, the deep-review analysis covered a selected 30-sample subset rather than the entire 400-run cohort. Fifth, host-removal and AMR screening used capped host-removed short-read subsets; the absence of AMRFinderPlus hits should not be interpreted as absence of antimicrobial resistance. Finally, targeted wet-lab validation is required before making translational or diagnostic claims.

## Unstructured Abstract Draft

Bronchoalveolar lavage fluid metagenomic next-generation sequencing can support broad pathogen detection in pulmonary disease, but public mNGS datasets require careful metadata reconstruction and conservative interpretation before they can inform experimental validation. We re-analyzed PRJNA1056765, a public BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. After excluding unavailable public WGS records, the final cohort contained 400 analyzable DNA WGS/mNGS runs. Kraken2/Bracken profiling and group-level species detection testing prioritized `Pseudomonas aeruginosa` in bacterial infection, `Mycobacterium tuberculosis` in pulmonary tuberculosis, and `Aspergillus fumigatus` in fungal infection as the strongest validation candidates. A 30-sample deep-review set retained the same top pathogen after QC re-analysis, supporting stability of selected calls. Host-removal and AMRFinderPlus screening completed for all deep-review samples and detected no AMR hit rows in capped host-removed short-read subsets. These findings support a focused bioinformatics-led short project in which public BALF mNGS data are used to prioritize pathogen markers for targeted qPCR or ddPCR validation, while antimicrobial-resistance and clinical diagnostic claims remain outside the supported scope.

## Structured Abstract Draft

### Background

BALF mNGS is increasingly used for pulmonary infection assessment, but public datasets can be overinterpreted when metadata, background taxa, and validation boundaries are not handled explicitly.

### Methods

We reconstructed clinical groups in PRJNA1056765 from public SRA records and published labels, then performed Kraken2/Bracken profiling of analyzable DNA WGS/mNGS runs. Species detection was compared by diagnosis group, selected pathogen-positive samples underwent QC deep-review, and host-removal plus AMRFinderPlus screening was used as an exploratory resistance guardrail.

### Results

The final cohort included 400 analyzable BALF mNGS runs: 114 bacterial infection, 78 fungal infection, 86 pulmonary tuberculosis, and 122 lung cancer disease-control runs. `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus` were the strongest diagnosis-associated pathogen candidates. All 30 selected deep-review samples retained the same top pathogen after QC re-analysis. AMRFinderPlus detected no AMR hit rows in capped host-removed short-read subsets.

### Conclusions

PRJNA1056765 supports a focused public-data re-analysis for pathogen-marker prioritization in BALF mNGS. The most defensible short-project validation targets are `P. aeruginosa` and `A. fumigatus`, with `M. tuberculosis` treated as biosafety-dependent. The current workflow supports candidate prioritization, not stand-alone diagnostic or antimicrobial-resistance inference.

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| PRJNA1056765 is suitable for pathogen-marker prioritization. | 400 analyzable labelled BALF mNGS runs across four disease groups. | Supported. |
| The strongest validation targets are `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus`. | Group-enrichment evidence from public summaries. | Supported. |
| Deep-review supports selected call stability. | 30/30 selected samples retained the same top pathogen after QC re-analysis. | Supported for selected subset. |
| AMR conclusions are supported. | No AMRFinderPlus hits in capped host-removed subsets. | Not supported; use as boundary. |

## Next Writing Step

Convert the Results, Discussion, limitations, and abstract drafts into a single manuscript skeleton with figure/table callouts and a concise Methods section.
