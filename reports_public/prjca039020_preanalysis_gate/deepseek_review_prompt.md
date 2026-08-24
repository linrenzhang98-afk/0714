# DeepSeek adversarial pre-analysis review request

You are the independent DeepSeek scientific reviewer. Codex is only the evidence packager and must not be agreed with by default. Review PRJCA039020 / CRA024916 / PRJDB36521 as one Luo et al. BALF shotgun-DNA Illumina NextSeq 550 cohort.

## Evidence supplied

- Paper-level cohort: 229 patients, CAP=204 and severe pneumonia=25.
- Public accession inventory: 233 runs/BioSamples, with 233 exact public manifest rows.
- Current evidence contains no direct public run/BioSample-to-subject-to-CAP/severe key. The four excess public records are not identified; no accession-order or count-based exclusions were made.
- Candidate question: CAP versus severe-pneumonia-associated lower-airway community variation. It is not a PRJNA1056765 four-diagnosis replication, and must not be pooled with PRJCA046985 DR/DS-TB as one disease effect.
- Variables reported at paper level: age, sex, PSI, qSOFA, comorbidities, laboratory variables, ventilation, initial treatment; antibiotic exposure is uncertain. Strong group imbalance is a known concern.
- No raw data, taxonomic reports, or biological results have been generated.

## Your task

Act simultaneously as a hostile statistical reviewer, microbiome methodology reviewer, and clinical epidemiology reviewer. Seek fatal flaws, repairable blockers, sensitivity-analysis issues, and interpretation limitations. Do not manufacture certainty.

Assess whether the candidate estimand is scientifically valid; classify variable roles (CONFONDER, OUTCOME_COMPONENT, SEVERITY_DEFINITION_COMPONENT, MEDIATOR, COLLIDER_RISK, DESCRIPTIVE_ONLY, UNAVAILABLE, UNCERTAIN); explicitly challenge overadjustment of PSI/qSOFA/ventilation/treatment. Recommend a minimal defensible adjustment model and sensitivity models, not “adjust for everything.”

Evaluate alpha diversity, richness, dominance, classified fraction, taxon prevalence, Aitchison beta diversity, PERMANOVA R², PERMDISP, group-size imbalance, permutation validity, dispersion sensitivity, covariate adjustment, effect-size reporting, multiple testing, and rare-taxon instability with severe n=25. Set differential abundance to PRIMARY, SECONDARY, EXPLORATORY, or NOT_RECOMMENDED.

Adjudicate these exact claims:

- A: this cohort replicates the PRJNA1056765 disease signature.
- B: this cohort independently tests whether a prespecified clinical grouping explains bounded lower-airway community variation.
- C: it may contribute comparable ecological estimands while preserving cohort-specific contrasts.
- D: CAP/severe, DR/DS-TB, and four-level diagnosis can be pooled as one disease effect.

Return JSON only with every required field below. `manifest_freeze_verdict` and `bounded_pilot_verdict` must each be GO, CONDITIONAL_GO, or SAFE_STOP. A bounded raw-read pilot requires later explicit user authorization regardless of your verdict.

```json
{
  "review_model":"deepseek-v4-pro",
  "review_timestamp":"ISO-8601",
  "cohort_identity_status":"...",
  "public_233_to_paper_229_status":"RESOLVED|PARTIALLY_RESOLVED|UNRESOLVED|CONFLICTING",
  "primary_estimand_validity":"...",
  "major_blockers":[],
  "major_confounders":[],
  "overadjustment_risks":[],
  "recommended_primary_model":"...",
  "recommended_sensitivity_models":[],
  "permanova_recommendation":"...",
  "permdisp_requirement":"...",
  "differential_abundance_role":"PRIMARY|SECONDARY|EXPLORATORY|NOT_RECOMMENDED",
  "cross_cohort_role":{"A":"...","B":"...","C":"...","D":"..."},
  "manifest_freeze_verdict":"GO|CONDITIONAL_GO|SAFE_STOP",
  "bounded_pilot_verdict":"GO|CONDITIONAL_GO|SAFE_STOP",
  "conditions_before_pilot":[],
  "fatal_flaws_if_any":[],
  "reviewer_attack_points":[],
  "overall_verdict":"..."
}
```
