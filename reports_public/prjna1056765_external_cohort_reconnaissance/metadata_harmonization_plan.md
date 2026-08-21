# Conservative metadata harmonization plan

The raw source fields remain immutable snapshots. Harmonized values are new fields with a versioned mapping table and a reason code.

## Canonical dictionary

| Field | Rule |
|---|---|
| `study_id` | Stable local cohort identifier; never implies centre |
| `sample_id` | Repository BioSample/sample identifier |
| `subject_id` | Paper/repository patient identifier; unresolved if no defensible mapping |
| `center` / `country` | Preserve source text; `unknown` is preferable to inference |
| `specimen` | Controlled values: BAL, BALF, protected brush, bronchial lavage, other |
| `diagnosis_raw` | Exact source label, never overwritten |
| `diagnosis_harmonized` | Study-specific analysis label from a frozen mapping |
| `disease_family` | Broad contextual family only; not automatically an analysis group |
| `case_control_status` | Used only when the paper prospectively defined it |
| `age`, `sex`, `smoking` | Retain units/categories and separate missing/unknown/not collected |
| `antibiotic_exposure`, `treatment_status` | Include time window when supplied; do not equate heterogeneous definitions |
| `sequencing_platform`, `library_layout`, `read_length` | Run-level technical fields |
| `negative_control` | `true`, `false`, or `unresolved`; controls never enter disease groups |
| `technical_batch` | Source batch/lane/date/laboratory; missingness explicitly recorded |
| `host_depletion_tool` | Exact tool or `unknown`; never inferred from filename alone |
| `host_reference` | Reference build/version or `unknown` |
| `depletion_parameters` | Preserved source parameters or `not reported` |
| `depletion_provenance` | `raw`, `laboratory-depleted`, `in-silico-depleted`, or `unresolved` |
| `download_accession` | Run/file accession, not sample ID |

## Cohort-specific grouping

- PRJCA046985: `DR_TB` versus `DS_TB`; no reclassification from microbial profiles.
- PRJCA039020: `CAP` versus `severe_pneumonia` exactly as published. The contrast is severity-associated and covariate-imbalanced.
- PRJNA977832: `pulmonary_infection_HIV_positive` versus `pulmonary_infection_HIV_negative`; require public-run linkage to the paper labels.
- PRJCA027972: freeze the clinical adjudication hierarchy from the patient supplement before pilot; do not use sequencing positivity to define groups.

Ambiguous labels stay ambiguous and are excluded from formal contrasts. Disease labels are never merged merely to increase n. If longitudinal/repeated data are later included, use one prespecified baseline/pre-treatment BALF per subject; if no unambiguous baseline exists, exclude the subject from primary analysis and retain all samples for a separately approved longitudinal sensitivity analysis. Duplicate accessions and paired modalities are linked, never counted as independent patients.
