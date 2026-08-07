# Minimal qPCR Validation Data Template

## Purpose

This template defines the smallest data structure needed to add a short qPCR validation module to the BALF mNGS manuscript. It is a data-capture and reporting template, not a laboratory protocol.

## Recommended Validation Scope

Default route:

- validate `Pseudomonas aeruginosa`
- validate `Aspergillus fumigatus`
- keep `Mycobacterium tuberculosis` as bioinformatic unless an approved local workflow already exists
- add `Cryptococcus neoformans` only if fungal-positive BALF sample numbers are adequate

## Sample Metadata Table

Use one row per local BALF sample.

| sample_id | diagnosis_group | specimen_type | collection_period | mngs_available | culture_available | notes |
|---|---|---|---|---|---|---|
| LOCAL_001 | bacterial_infection | BALF | YYYY-MM | yes/no | yes/no |  |
| LOCAL_002 | fungal_infection | BALF | YYYY-MM | yes/no | yes/no |  |
| LOCAL_003 | lung_cancer_control | BALF | YYYY-MM | yes/no | yes/no |  |

Required fields:

- `sample_id`: de-identified internal sample ID
- `diagnosis_group`: bacterial_infection, fungal_infection, pulmonary_tuberculosis, lung_cancer_control, other_control
- `specimen_type`: should be BALF for the main validation claim
- `mngs_available`: whether local mNGS or clinical pathogen call exists
- `culture_available`: whether routine clinical culture/plate-count result exists

## qPCR Result Table

Use one row per sample per target.

| sample_id | target_species | marker | result_binary | quantitative_readout | replicate_status | interpretation |
|---|---|---|---|---|---|---|
| LOCAL_001 | Pseudomonas aeruginosa | oprL/ecfX | positive/negative | Ct/Cq/copies if available | pass/fail | concordant/discordant |
| LOCAL_002 | Aspergillus fumigatus | ITS/28S | positive/negative | Ct/Cq/copies if available | pass/fail | concordant/discordant |

Required fields:

- `target_species`
- `marker`
- `result_binary`
- `replicate_status`
- `interpretation`

Do not report quantitative comparisons unless the measurement and normalization approach are consistent across samples.

## Optional Culture / Plate-Count Support Table

Use only for routine bacterial targets where local clinical workflow already permits culture or plate-count data.

| sample_id | target_species | culture_result | plate_count_readout | concordance_with_qpcr | notes |
|---|---|---|---|---|---|
| LOCAL_001 | Pseudomonas aeruginosa | positive/negative | available/not_available | concordant/discordant |  |

Interpretation:

- Use as supportive evidence only.
- Do not use for tuberculosis.
- Do not use as antimicrobial-resistance evidence.
- Do not use to claim diagnostic performance without a prespecified validation cohort.

## Minimal Summary Statistics

### Detection by group

| target_species | target_group | positive_in_target_group | total_target_group | positive_in_comparator | total_comparator | interpretation |
|---|---|---:|---:|---:|---:|---|
| Pseudomonas aeruginosa | bacterial_infection |  |  |  |  | directional_support/no_support |
| Aspergillus fumigatus | fungal_infection |  |  |  |  | directional_support/no_support |

### Concordance with public-data prioritization

| target_species | public_data_priority | local_validation_direction | manuscript_use |
|---|---|---|---|
| Pseudomonas aeruginosa | tier1 | supports/partial/no_support | core/secondary/remove |
| Aspergillus fumigatus | tier1 | supports/partial/no_support | core/secondary/remove |
| Cryptococcus neoformans | tier2 | supports/partial/no_support/not_tested | optional |

## Result Interpretation Rules

If validation supports the public-data signal:

- Claim: targeted qPCR validation was directionally consistent with public-data prioritization.
- Do not claim diagnostic accuracy unless a separate validation design supports it.

If validation is mixed:

- Claim: validation showed partial transferability of public-data-prioritized targets.
- Discuss local cohort composition, sample handling, and assay sensitivity as possible explanations.

If validation does not support the public-data signal:

- Claim: the public-data signal did not transfer to the local validation set.
- Reframe manuscript as public-data prioritization with an explicit validation boundary.

## Manuscript Insert Placeholder

Targeted qPCR validation was performed in [N] local BALF samples. `Pseudomonas aeruginosa` was detected in [x/y] bacterial infection samples and [x/y] comparator samples. `Aspergillus fumigatus` was detected in [x/y] fungal infection samples and [x/y] comparator samples. These results were [directionally consistent / partially consistent / not consistent] with the public BALF mNGS prioritization analysis.
