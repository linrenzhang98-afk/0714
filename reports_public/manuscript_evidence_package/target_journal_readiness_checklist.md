# Target-Journal Readiness Checklist

## Current Manuscript Readiness State

The project has moved from workstation computation to manuscript preparation. The current evidence package supports a bioinformatics-led brief report or short communication based on public BALF mNGS re-analysis, with optional targeted validation if local samples are available.

## Completed Components

| Component | Status | File |
|---|---|---|
| Public-data cohort reconstruction | Ready | `reports_public/prjna1056765_clinical_groups/summary.md` |
| First-pass 400-run profiling summary | Ready | `reports_public/metagenome_production/summary.md` |
| Group-level candidate prioritization | Ready | `reports_public/prjna1056765_group_differentials/summary.md` |
| Deep-review selected-call stability | Ready | `reports_public/metagenome_deep_review_summary/summary.md` |
| Host-removal/AMR guardrail | Ready | `reports_public/metagenome_host_amr_screen/summary.md` |
| Short-project evidence package | Ready | `reports_public/manuscript_evidence_package/short_project_plan.md` |
| Results draft | Ready | `reports_public/manuscript_evidence_package/full_results_section.md` |
| Discussion/limitations/abstract draft | Ready | `reports_public/manuscript_evidence_package/discussion_limitations_and_abstract.md` |
| Manuscript skeleton | Ready | `reports_public/manuscript_evidence_package/manuscript_skeleton.md` |
| Reproducible Methods detail | Ready | `reports_public/manuscript_evidence_package/reproducible_methods_detail.md` |
| Table and figure captions | Ready | `reports_public/manuscript_evidence_package/tables_and_figure_captions.md` |

## Recommended Manuscript Positioning

Best fit:

- Short communication
- Brief report
- Bioinformatics resource re-analysis
- Translational bioinformatics note with targeted validation plan

Avoid positioning as:

- Stand-alone clinical diagnostic model
- Antimicrobial-resistance study
- Full respiratory microbiome discovery study
- Healthy-versus-disease microbiome comparison

## Core Claim That Is Supported

PRJNA1056765 BALF mNGS re-analysis identifies diagnosis-associated pathogen signals and prioritizes practical validation candidates, especially `Pseudomonas aeruginosa` and `Aspergillus fumigatus`, with `Mycobacterium tuberculosis` retained as a biosafety-dependent bioinformatic endpoint.

## Claims That Should Not Be Made

- Do not claim clinical diagnostic accuracy.
- Do not claim absence of antimicrobial resistance.
- Do not claim healthy-control specificity.
- Do not claim all first-pass pathogen calls are stable.
- Do not claim wet-lab validation has been completed unless independent validation data are later added.

## Remaining Author Decisions

These decisions require author input before final journal-specific formatting:

| Decision | Why it matters | Recommended default |
|---|---|---|
| Target journal | Determines abstract format, word count, figure count, reporting style | Choose a brief-report-friendly infectious disease, microbiology, or translational bioinformatics journal |
| Validation status | Determines whether the manuscript is public-data-only or public-data-plus-validation | If no validation yet, submit as candidate-prioritization/re-analysis |
| TB assay inclusion | Requires biosafety and approved workflow | Keep TB as bioinformatic endpoint unless existing approval is already in place |
| Local BALF sample availability | Determines whether qPCR/ddPCR validation can be included | Prioritize `P. aeruginosa` and `A. fumigatus` |
| Figure count | Short communications often limit figures | Use 3 main figures plus supplementary tables if limits are tight |
| Abstract style | Structured vs unstructured varies by journal | Use unstructured by default unless journal requires headings |

## Minimal Submission Package

If submitting without wet-lab validation:

1. Manuscript skeleton refined into full draft.
2. Three main figures:
   - cohort/workflow
   - pathogen candidate spectrum
   - robustness and guardrails
3. Three main tables:
   - cohort reconstruction
   - validation candidate ranking
   - deep-review/AMR guardrail summary
4. Supplementary run-level and differential result tables.
5. Strong limitations paragraph stating that this is candidate prioritization, not clinical validation.

If submitting with wet-lab validation:

1. Add independent/local BALF validation cohort description.
2. Add targeted validation results for `P. aeruginosa` and `A. fumigatus`.
3. Add validation concordance table.
4. Keep `M. tuberculosis` conditional unless biosafety workflow is already approved.

## Suggested Journal Categories

Short-project compatible categories:

- clinical microbiology brief report
- infectious disease diagnostics note
- translational bioinformatics short communication
- respiratory infection data re-analysis
- public-data resource re-analysis

The manuscript is likely weaker for broad microbiome journals unless additional ecological analyses or independent validation are added.

## Immediate Next Action

The next technical writing step is to convert the current manuscript skeleton into a journal-neutral full draft with numbered figures/tables and a concise Methods section. The next author decision is target journal selection.
