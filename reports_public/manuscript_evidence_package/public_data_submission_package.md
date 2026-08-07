# Public-Data-Only Submission Package

## Route Decision

Use the public-data-only manuscript route now. qPCR or culture validation can be added later as a revision, follow-up study, or local validation note, but it is not treated as a prerequisite for initial submission.

## One-Sentence Argument

In public BALF mNGS data from PRJNA1056765, we show that diagnosis-associated pathogen signals can prioritize clinically coherent validation targets using reproducible Kraken2/Bracken profiling, group-level detection testing, selected-sample QC re-analysis, and host-removal/AMR guardrails, while limiting claims to candidate prioritization rather than diagnostic performance or antimicrobial-resistance inference.

## Terminology Ledger

| Canonical term | First-use definition | Use decision |
|---|---|---|
| BALF | bronchoalveolar lavage fluid (BALF) | Spell out once, then use BALF. |
| mNGS | metagenomic next-generation sequencing (mNGS) | Use mNGS for sequencing modality; avoid mixing with "shotgun metagenomics" unless discussing method. |
| PRJNA1056765 | public BioProject PRJNA1056765 | Use as the dataset identifier. |
| Disease-control comparator | lung cancer BALF samples used as a diseased comparator group | Do not call this a healthy control. |
| Candidate prioritization | ranking pathogen targets from public-data evidence | Do not call it clinical validation or diagnostic confirmation. |
| Deep-review set | 30 selected pathogen-positive samples re-analyzed after QC | Use for stability only; do not generalize to all first-pass calls. |
| Host-removal/AMR screen | host-removed capped short-read AMRFinderPlus screen | Use as a guardrail; do not infer phenotypic resistance. |

## Recommended Submission Position

Recommended manuscript type:

- Short Communication
- Brief Report
- Public-data re-analysis
- Translational bioinformatics note

Best first target:

- Frontiers in Medicine, if a suitable clinical infectious disease, pulmonary medicine, or translational medicine section is available.

Practical fallback:

- Journal of Clinical Medicine, only if the clinical framing is strengthened and the public-data limitation is explicit.
- Infectious-disease or clinical microbiology brief-report journals if speed is prioritized over journal breadth.

Do not prioritize an environmental-health journal for the current version unless the manuscript is reframed around surveillance or One Health. The strongest story is clinical BALF pathogen-marker prioritization.

## Current Evidence Package

Supported:

- 400 analyzable DNA WGS/mNGS BALF runs from PRJNA1056765.
- Four reconstructed disease groups: bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer disease-control comparator.
- Two unavailable WGS records handled as public-data unavailability, not pipeline failure.
- First-pass Kraken2/Bracken profiling completed for all analyzable runs.
- Group-level species detection testing with multiple-testing correction.
- Strong candidate signals for `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus`.
- 30-sample deep-review set with stable same-top pathogen calls.
- Host-removal/AMRFinderPlus guardrail completed in 30 samples with zero AMRFinderPlus hit rows in capped subsets.

Not supported:

- Clinical diagnostic sensitivity or specificity.
- Healthy-control comparisons.
- Phenotypic antimicrobial-resistance conclusions.
- Wet-lab-confirmed pathogen detection.
- Causal inference about infection pathogenesis.

## Submission Manuscript To Use

Primary draft:

- `reports_public/manuscript_evidence_package/journal_neutral_full_manuscript_draft.md`

Route-specific draft:

- `reports_public/manuscript_evidence_package/manuscript_variant_public_data_only.md`

Supporting files:

- `reports_public/manuscript_evidence_package/reproducible_methods_detail.md`
- `reports_public/manuscript_evidence_package/tables_and_figure_captions.md`
- `reports_public/manuscript_evidence_package/discussion_limitations_and_abstract.md`
- `reports_public/manuscript_evidence_package/target_journal_readiness_checklist.md`

## Required Pre-Submission Edits

1. Remove language that implies validation, diagnosis, or resistance confirmation.
2. Keep `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus` as prioritized candidates rather than confirmed biomarkers.
3. Explicitly state that lung cancer samples are disease-control comparators, not healthy controls.
4. Add direct citations for the PRJNA1056765 source papers and for Kraken2, Bracken, AMRFinderPlus, SRA Toolkit, and multiple-testing methods.
5. Convert backtick species names to journal-compliant italic formatting in the final manuscript.
6. Prepare figures from public summary tables only; do not include raw FASTQ, private logs, or local runner configuration.
7. Keep AMR as a negative/exploratory guardrail and avoid resistance claims.

## Suggested Figure Set

Figure 1: Public cohort reconstruction and analysis workflow.

- SRA/published-label integration.
- Four disease groups and unavailable WGS records.
- Analysis modules: Kraken2/Bracken, group testing, deep-review QC, host-removal/AMR guardrail.

Figure 2: Diagnosis-associated pathogen candidates.

- Detection rates by clinical group.
- FDR-ranked candidates.
- Highlight `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus`.

Figure 3: Robustness and boundary checks.

- 30/30 stable same-top calls in the deep-review set.
- 30/30 host-removal/AMR screen completion.
- Zero AMRFinderPlus hit rows in capped subsets.
- Explicit interpretation boundary.

## Suggested Tables

Table 1: Reconstructed cohort and analyzable run counts.

Table 2: Candidate pathogen ranking by disease group, detection counts, comparison rate, FDR, and validation feasibility.

Table 3: Deep-review and host-removal/AMR guardrail summary.

Supplementary Table 1: Run-level metadata reconstruction.

Supplementary Table 2: Full group-level differential detection results.

Supplementary Table 3: Deep-review run status and top-call comparison.

## Abstract Positioning

Use a conservative abstract ending:

> These results support the use of public BALF mNGS datasets for pathogen-marker prioritization and study design. They do not establish diagnostic performance or antimicrobial-resistance status, both of which require independent validation.

Avoid:

- "validated biomarker"
- "diagnostic marker"
- "clinical assay"
- "resistance profile"
- "confirmed pathogen"

## Cover-Letter Message

The cover letter should frame the manuscript as a reproducible public-data re-analysis that converts a large BALF mNGS resource into a conservative, clinically interpretable candidate-prioritization framework. It should emphasize transparency, metadata reconstruction, robustness checks, and explicit limits, not novelty by overstatement.

## Decision Status

Current decision: proceed with public-data-only submission preparation.

Current blocker: none inside the repository. The remaining work is manuscript polishing, citation verification, figure generation from public summary tables, and target-journal formatting.
