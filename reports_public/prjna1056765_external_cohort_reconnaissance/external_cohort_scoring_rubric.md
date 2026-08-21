# External cohort scoring rubric

Status: metadata-only specification, frozen 2026-08-20. A score never overrides a scientific veto.

Seven positive domains are scored 0–5: scientific fit, metadata completeness, technical compatibility, independence, QC interpretability, compute feasibility, and publication value. `confounding_risk_score` and `compute_cost_score` in the table instead use 1 = low and 5 = extreme so that risk remains visually explicit.

| Score | Scientific fit | Metadata | Technical compatibility | Independence | QC interpretability | Compute feasibility | Publication value |
|---:|---|---|---|---|---|---|---|
| 5 | Confirmed human BAL/BALF and an a priori within-study clinical contrast | Run–sample–subject map plus diagnosis and core covariates | Public shotgun DNA, ordinary FASTQ, compatible reads | Independent people, site and BioProject; diagnosis estimable within study | Public controls and well-described low-biomass workflow | <50 GB and routine processing | Adds a distinct, defensible generalizability test |
| 4 | BAL/BALF with narrower relevant contrast | Mapping and most core fields recoverable | Shotgun DNA with a manageable platform caveat | Independent with minor provenance uncertainty | Controls or detailed technical metadata, not both | 50–250 GB | Strong partial replication |
| 3 | Tests methods more than diagnosis | Diagnosis/mapping present but covariates incomplete | Reprocessing feasible after a bounded adaptation | Independence likely but linkage incomplete | Low-biomass workflow documented, controls unclear | 250–500 GB | Useful methodological replication |
| 2 | Lower airway but weakly comparable | Paper-level metadata only or public subset incomplete | Modality/specimen architecture substantially differs | Possible related publication or design dependence | Sparse QC provenance | 0.5–1 TB | Mainly contextual |
| 1 | Wrong specimen or no valid contrast | Key labels unavailable | 16S/RNA/targeted/virome only for this question | Strong overlap/confounding | QC cannot be interpreted | >1 TB or extraordinary burden | Little incremental value |
| 0 | Nonhuman/not lower airway | No usable metadata | No usable sequence | Duplicate dataset | No QC evidence | Not executable | No value |

Categories are assigned by judgment, not a sum alone. **A** requires confirmed BAL/BALF shotgun DNA, an a priori estimable within-study contrast, and no fatal independence/confounding problem. **B** is usable but narrower or operationally conditional. **C** is reserve or methods/context. **D** is excluded from quantitative replication. DeepSeek may veto any A/B candidate for invalid labels, specimen, duplicate data, or irreparable study–diagnosis confounding.
