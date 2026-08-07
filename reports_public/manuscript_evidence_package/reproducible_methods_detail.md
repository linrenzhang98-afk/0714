# Reproducible Methods Detail

## Purpose

This document expands the manuscript Methods section into a reproducible, publication-ready description. It is written for a bioinformatics-led short communication and avoids operational wet-lab protocol detail.

## Study Design

This study was a retrospective public-data re-analysis of BALF mNGS data from PRJNA1056765. The analysis objective was to reconstruct clinically labelled pulmonary disease groups, profile species-level pathogen signals, prioritize validation candidates, and define interpretation guardrails through selected-sample QC re-analysis and exploratory host-removal/AMR screening.

The study did not use healthy BALF controls. Lung cancer BALF samples were used as disease controls because they represented a non-infection pulmonary disease group within the same public BioProject.

## Public Data And Metadata Reconstruction

SRA RunInfo records were obtained for PRJNA1056765 and integrated with published clinical labels from the associated main article and data descriptor supplementary materials. Runs were retained when they represented analyzable DNA WGS/mNGS records with available public data. RNA-seq or metatranscriptomic records were not used for the DNA WGS/mNGS analysis set.

The final analyzable cohort contained 400 DNA WGS/mNGS runs:

- Bacterial infection: 114 runs
- Fungal infection: 78 runs
- Pulmonary tuberculosis: 86 runs
- Lung cancer disease controls: 122 runs

Two expected WGS records were not analyzed because their SRA RunInfo entries had `size_MB=0`:

- SRR27343810, fungal infection group
- SRR27343463, lung cancer group

These records were treated as unavailable public records rather than analysis failures.

## First-Pass Taxonomic Profiling

All analyzable DNA WGS/mNGS runs were processed through a first-pass taxonomic profiling workflow using Kraken2 followed by Bracken species-level abundance estimation. The local Kraken2 database used for this project was the PlusPF 16 GB database unpacked under the local workstation database directory. Outputs were summarized at run level and species level.

For each run, the workflow recorded:

- run accession
- diagnosis group
- classified fraction
- top detected species
- top-pathogen fraction
- species-level Bracken fractions

The analysis retained full output tables for transparency but separated broad recurrent taxa from biological interpretation. Host, plant-associated, or low-specificity recurrent taxa were not used as disease-associated pathogen findings unless supported by clinical coherence and group-level enrichment.

## Group-Level Differential Detection

Species-level detection was compared between each diagnosis group and all remaining groups. For each species and target diagnosis group, detection frequency was evaluated using a two-sided Fisher exact test. Benjamini-Hochberg false-discovery-rate correction was applied to account for multiple testing.

Candidate prioritization used three criteria:

1. Statistical support from group-level detection testing.
2. Clinical coherence with the diagnosis group.
3. Practical feasibility for targeted validation.

The strongest tier-1 candidates were:

- `Pseudomonas aeruginosa` for bacterial infection
- `Mycobacterium tuberculosis` for pulmonary tuberculosis
- `Aspergillus fumigatus` for fungal infection

`Cryptococcus neoformans` was retained as a secondary fungal candidate because the signal was biologically plausible but statistically weaker.

## Deep-Review QC Re-Analysis

A selected set of 30 pathogen-positive samples underwent deep-review QC re-analysis. The selection covered the following pathogen groups:

- Acinetobacter
- Candida
- Enterobacterales
- Haemophilus
- Mycobacteria
- Pseudomonas
- Staphylococcus
- Stenotrophomonas
- Streptococcus

The primary deep-review endpoint was whether the top pathogen call remained unchanged after QC re-analysis. A same-top result was interpreted as support for selected-call stability. This endpoint was restricted to the selected subset and was not generalized to every first-pass call in the 400-run cohort.

## Host-Removal And Exploratory AMR Screen

The 30 deep-review samples were evaluated with host-removal and AMRFinderPlus screening on capped host-removed short-read subsets. This step was used to define whether the current workflow produced exploratory genotypic AMR signals.

The interpretation rules were:

- AMRFinderPlus hit rows, if present, would be treated as exploratory genotypic signals.
- Absence of AMRFinderPlus hits would not be interpreted as absence of antimicrobial resistance.
- Phenotypic resistance claims would require independent culture, antimicrobial susceptibility testing, or deeper targeted genotypic evidence.

In the current analysis, all 30 host-AMR screens completed and no AMRFinderPlus hit rows were detected.

## Statistical Reporting

Detection counts were reported as detected runs over total runs in the target diagnosis group and as comparator detection rate in the remaining groups. Multiple-testing-adjusted values were reported as BH-FDR. Classified fraction summaries were reported as group medians and overall range.

The manuscript should avoid unsupported diagnostic-performance metrics unless a later analysis explicitly defines prediction models, cross-validation, held-out testing, and clinically meaningful endpoints.

## Reproducibility Outputs

The following public summary outputs should be cited as analysis artifacts:

- `reports_public/prjna1056765_clinical_groups/summary.md`
- `reports_public/prjna1056765_group_differentials/summary.md`
- `reports_public/metagenome_production/summary.md`
- `reports_public/metagenome_deep_review_summary/summary.md`
- `reports_public/metagenome_host_amr_screen/summary.md`
- `reports_public/manuscript_evidence_package/manuscript_skeleton.md`

Raw FASTQ files, local databases, full intermediate outputs, runner state, and private local configuration are intentionally not committed to GitHub.

## Methods Boundaries

This Methods description supports public-data bioinformatics re-analysis and validation planning. It does not provide a pathogen culture protocol, clinical diagnostic protocol, or wet-lab operating procedure. Any future experimental validation must follow local ethics approval, biosafety requirements, and laboratory standard operating procedures.
