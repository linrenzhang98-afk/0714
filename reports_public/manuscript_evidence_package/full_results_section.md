# Full Results Section Draft

## One-Sentence Argument

In public BALF mNGS data from PRJNA1056765, four clinically labelled pulmonary disease groups showed diagnosis-associated pathogen spectra, supported by a 400-run Kraken2/Bracken re-analysis, group-level enrichment testing, selected-call QC stability, and a conservative host-removal/AMR screen.

## Terminology Ledger

| Canonical term | Definition | Writing decision |
|---|---|---|
| BALF | Bronchoalveolar lavage fluid | Spell out once, then use BALF. |
| mNGS | Metagenomic next-generation sequencing | Spell out once, then use mNGS. |
| PRJNA1056765 | Public BioProject used for re-analysis | Use accession consistently. |
| Disease control | Lung cancer BALF group | Do not call this a healthy control. |
| First-pass profiling | Kraken2/Bracken profiling of 400 DNA WGS/mNGS runs | Use for whole-cohort taxonomic profiling. |
| Deep-review | QC re-analysis of 30 selected pathogen-positive samples | Use only for the selected subset. |
| Host-AMR screen | Host-removal plus AMRFinderPlus screen on capped host-removed subsets | Frame as exploratory. |

## Results

### Public-data reconstruction defined a four-group BALF mNGS cohort

We reconstructed the PRJNA1056765 analysis cohort by integrating the public SRA RunInfo table with published clinical labels for bronchoalveolar lavage fluid (BALF) metagenomic next-generation sequencing (mNGS) samples. The analyzable DNA WGS/mNGS cohort contained 400 runs, including 114 bacterial infection runs, 78 fungal infection runs, 86 pulmonary tuberculosis runs, and 122 lung cancer runs. Two expected WGS records, SRR27343810 from the fungal infection group and SRR27343463 from the lung cancer group, had `size_MB=0` in SRA RunInfo and were therefore treated as unavailable public records rather than pipeline failures.

This cohort definition set the main comparison framework for the analysis. Lung cancer BALF samples were used as a disease-control group because the public dataset did not include true healthy BALF controls. All downstream interpretation therefore focused on diagnosis-associated pathogen spectra within diseased BALF samples, not on healthy-versus-disease microbiome differences.

### First-pass profiling showed low classified fractions but recoverable pathogen signals

First-pass Kraken2/Bracken profiling completed for all 400 analyzable DNA WGS/mNGS runs. The median classified fraction was 1.797%, with a range from 0.418% to 10.427%. Median classified fractions by clinical group were 1.9034% for bacterial infection, 1.5793% for fungal infection, 1.6587% for pulmonary tuberculosis, and 2.0530% for lung cancer. These values indicate that the dataset is suitable for conservative pathogen prioritization, but not for overinterpreting weak low-abundance signals.

Several recurrent taxa were detected broadly across the cohort, including `Homo sapiens`, `Toxoplasma gondii`, `Arabidopsis thaliana`, and plant-associated taxa. Because these taxa were frequent across diagnosis groups and included likely host, background, or low-specificity signals, they were excluded from biological claim-building. The main analysis instead focused on clinically coherent taxa with group-associated detection patterns and plausible wet-lab validation markers.

### Group-level testing prioritized clinically coherent pathogen candidates

Species-level detection testing identified several diagnosis-associated pathogen candidates. `Pseudomonas aeruginosa` was the strongest bacterial infection-associated candidate, detected in 23 of 114 bacterial infection runs compared with a 0.02448 detection rate in the remaining groups (two-sided Fisher exact test with Benjamini-Hochberg correction, FDR 2.48792e-05). This signal supports `P. aeruginosa` as the highest-priority bacterial target for follow-up qPCR or ddPCR validation using markers such as `oprL` or `ecfX`.

`Mycobacterium tuberculosis` was enriched in pulmonary tuberculosis, detected in 9 of 86 tuberculosis runs and absent from the comparison groups (FDR 0.000533876). This finding is clinically coherent and supports `M. tuberculosis` as a strong bioinformatic endpoint. However, wet-lab validation using `IS6110` should be included only if the laboratory already has approved tuberculosis sample-handling and biosafety workflows.

In the fungal infection group, `Aspergillus fumigatus` was detected in 8 of 78 fungal infection runs compared with a 0.00932 detection rate in the remaining groups (FDR 0.0332815). This supports `A. fumigatus` as the most defensible fungal validation target, using ITS or 28S assays. `Cryptococcus neoformans` showed a weaker but biologically plausible fungal-enrichment pattern, detected in 6 of 78 fungal infection runs compared with a 0.00621 detection rate in other groups (FDR 0.110067). Because this signal did not meet the same statistical threshold as the tier-1 targets, it should be treated as an optional secondary validation candidate.

Other clinically relevant organisms, including `Haemophilus influenzae`, `Staphylococcus aureus`, `Streptococcus pneumoniae`, `Klebsiella pneumoniae`, `Acinetobacter baumannii`, and `Candida albicans`, were retained as case-confirmation or secondary targets rather than core group-enriched findings. This tiered interpretation prevents the manuscript from presenting every detected pathogen as a statistically supported diagnostic marker.

### Deep-review re-analysis supported stability of selected top-pathogen calls

To evaluate the stability of selected pathogen-positive calls, we performed a 30-sample deep-review analysis spanning Acinetobacter, Candida, Enterobacterales, Haemophilus, Mycobacteria, Pseudomonas, Staphylococcus, Stenotrophomonas, and Streptococcus groups. All 30 selected samples retained the same top pathogen after QC re-analysis. Diagnosis coverage in this subset included 14 bacterial infection samples, 1 fungal infection sample, 5 pulmonary tuberculosis samples, and 10 lung cancer samples, all of which showed stable same-top calls.

This result supports the robustness of selected high-priority pathogen calls under an additional QC pass. The evidence is deliberately bounded: it supports the selected deep-review subset and should not be written as proof that every first-pass call across the 400-run cohort is stable.

### Host-removal and AMR screening defined a conservative resistance boundary

Host-removal and AMRFinderPlus screening completed for all 30 deep-review samples. The screen generated 30 final run summaries, all with `done_short_read_subset` AMR status, and AMRFinderPlus detected no AMR hit rows in the capped host-removed short-read subsets.

This negative result is useful primarily as an interpretation boundary. It indicates that the current capped subset workflow did not provide support for genotypic antimicrobial resistance claims. It does not demonstrate absence of resistance, does not replace culture or antimicrobial susceptibility testing, and should not be used to infer phenotypic resistance. The manuscript should therefore present AMR as an exploratory endpoint that was checked but not supported by the available data.

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| PRJNA1056765 supports a four-group BALF mNGS re-analysis. | 400 analyzable DNA WGS/mNGS runs mapped to bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer labels. | Supported. |
| The cohort has low but usable classified fractions. | 400/400 runs completed; median classified fraction 1.797%. | Supported with conservative interpretation. |
| `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus` are top validation candidates. | Group-enrichment signals with FDR values below 0.05. | Supported. |
| `C. neoformans` is a secondary fungal candidate. | Fungal-group enrichment trend with FDR 0.110067. | Suggestive; needs validation. |
| Selected pathogen calls are stable after QC re-analysis. | 30/30 deep-review samples retained same top pathogen. | Supported for selected subset only. |
| Current data support AMR/resistance conclusions. | AMRFinderPlus produced 0 hits in capped host-removed subsets. | Not supported; use as boundary only. |

## Assumptions Or Missing Inputs

- This draft assumes published supplemental labels are the correct clinical grouping source.
- No healthy BALF control group is available in the current public-data reconstruction.
- Wet-lab validation sample availability, ethics approval, assay primers, and local clinical metadata remain external to the public-data workflow.
- Antimicrobial resistance interpretation requires orthogonal culture, AST, or deeper targeted genotypic evidence.
