# Known blockers and limitations

| Item | Classification | Status | Required closure |
|---|---|---|---|
| Four excess public BioSamples/runs | Repairable blocker | UNRESOLVED | Direct, auditable accession/BioSample-to-subject-to-paper-group and inclusion/exclusion key. |
| Individual CAP/severe labels | Fatal for biological manifest/pilot at present | UNRESOLVED | Same direct key; do not infer from accession order. |
| Age/sex/comorbidity linkage and timing | Repairable blocker | UNRESOLVED | Row-level clinical dictionary and linkage, with missingness. |
| PSI/qSOFA/ventilation/treatment causal position | Interpretation and model-design blocker | SUPPORTED but incomplete | Exact severity definition and timing relative to BALF collection/group assignment. |
| Pre-sampling antibiotic exposure | Repairable blocker | UNCERTAIN | Patient-level exposure definition and timing. |
| Sequencing batch and controls | Sensitivity/interpretation limitation | UNRESOLVED | Public technical metadata or an explicit statement of unavailable data. |
| n=25 severe group | Inherent precision limitation | VERIFIED | Pre-specify effect sizes, permutation scheme, dispersion checks, and conservative inference. |
| 40-nt Bracken derivative | Technical blocker for a future Bracken path, not this gate | VERIFIED | Separate compatibility decision; no execution in this task. |

`PUBLIC_233_TO_PAPER_229_STATUS=UNRESOLVED`.

No item above authorizes raw-read download, microbiome processing, or a substitute cohort/label definition.
