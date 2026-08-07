# Minimal Wet-Lab Validation Plan

## Objective

Validate a small set of pathogen signals prioritized from PRJNA1056765 BALF mNGS re-analysis using independent or local BALF samples.

## Recommended Minimal Panel

### Core assays

1. `Pseudomonas aeruginosa`
   - Marker: `oprL` or `ecfX`
   - Rationale: strongest bacterial infection enrichment in the public analysis.
   - Priority: highest.

2. `Aspergillus fumigatus`
   - Marker: ITS or 28S
   - Rationale: fungal infection enrichment with BH-FDR below 0.05.
   - Priority: highest fungal target.

3. `Cryptococcus neoformans`
   - Marker: ITS
   - Rationale: weaker but biologically coherent fungal signal.
   - Priority: optional if fungal-positive BALF samples are available.

### Conditional assay

4. `Mycobacterium tuberculosis`
   - Marker: `IS6110`
   - Rationale: strong tuberculosis enrichment in public data.
   - Condition: include only if the laboratory already has approved TB workflow, biosafety conditions, and sample handling route.

## Suggested Sample Design

- Preferred sample type: residual BALF DNA or BALF-derived nucleic acid already processed under approved ethics.
- Minimum short-project design:
  - bacterial infection BALF group
  - fungal infection BALF group
  - tuberculosis BALF group if TB assay is feasible
  - lung cancer BALF disease-control group
- Avoid claiming healthy-control specificity unless true healthy BALF controls are available.

## Primary Validation Readouts

- Presence/absence by qPCR or ddPCR.
- Ct/Cq or copies per input DNA when quantitative data are available.
- Group-level detection rate by clinical category.
- Concordance with mNGS-prioritized pathogen group.

## Minimal Statistical Plan

- Compare detection frequency between target diagnosis group and all other available groups by Fisher exact test.
- Report effect size as detection rate difference or odds ratio with confidence interval if sample size permits.
- For quantitative assays, compare pathogen load distributions using a non-parametric test only when sample size is adequate.
- Treat this as validation of prioritized markers, not discovery of diagnostic thresholds.

## Interpretation Rules

- A positive validation result supports pathogen-marker prioritization from public BALF mNGS data.
- A negative validation result does not necessarily refute the public-data signal; it may reflect local cohort composition, sample handling, or assay sensitivity.
- Do not infer antimicrobial resistance from the current AMRFinderPlus-negative subset screen.
- If AST/culture data are available locally, analyze them as a separate exploratory correlation.

## Practical Recommendation

For the shortest feasible project, run `P. aeruginosa` and `A. fumigatus` first. Add `C. neoformans` only if fungal sample numbers are sufficient. Add `M. tuberculosis` only under existing biosafety approval.
