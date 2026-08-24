# DeepSeek pre-analysis gate: PRJCA039020 / CRA024916 / PRJDB36521

This is a rendering of the genuine DeepSeek supervisor response. Model: `deepseek-v4-pro`; actual provider response received `2026-08-24T02:43:53.094Z`; provider usage: 4,184 prompt tokens and 6,014 completion tokens. The model-provided `review_timestamp` is retained verbatim in the companion JSON.

## Overall verdict

**SAFE_STOP at current evidence.** The cohort-specific CAP/severe community question is conditionally valid as a future ecological analysis, but neither manifest freeze nor a bounded pilot can proceed until mapping and protocol are fully resolved and separately authorized.

| Decision | Verdict |
|---|---|
| Cohort identity | PARTIALLY_RESOLVED: the three accessions are one cohort; accession-to-subject-to-group identity is unresolved. |
| Public 233 to paper 229 | UNRESOLVED |
| Manifest freeze | SAFE_STOP |
| Bounded raw-read pilot | SAFE_STOP |
| Differential abundance | EXPLORATORY |

## DeepSeek’s primary assessment

The paper-level CAP versus severe-pneumonia question is conditionally valid, but it is not operationally estimable from public accessions: no direct key links public runs/BioSamples to paper participants or CAP/severe labels. The severe group has n=25 and further limits inferential claims.

DeepSeek’s future primary-model recommendation is unadjusted Aitchison beta-diversity PERMANOVA with finite-sample-appropriate permutations, pseudo-F, R², effect size and uncertainty, plus mandatory PERMDISP. After verified pre-exposure linkage, age/sex may enter a separate minimal sensitivity model. PSI, qSOFA, ventilation, treatment, and laboratory variables must not be blindly adjusted for.

## Fatal flaws at this gate

1. No public run-to-subject-to-group key; every public accession has unresolved group assignment.
2. The roles of the four records beyond paper n=229 are unknown, so the paper’s analyzed population cannot be reconstructed without a traceable key.

## Required conditions before any pilot

- Obtain a direct, auditable run/BioSample-to-participant, inclusion/exclusion, and CAP/severe mapping.
- Resolve the four excess records without accession-order or group-count inference.
- Obtain a row-level covariate dictionary with timing and missingness, including pre-BALF antibiotics.
- Pre-register distance/zero handling, permutation, effect-size, multiplicity and rare-taxon rules; retain differential abundance as exploratory.
- Resolve, or explicitly document absence of, batch and negative-control metadata.
- Obtain separate user authorization before any raw-read download or pilot.

## Cross-cohort adjudication

| Statement | DeepSeek adjudication |
|---|---|
| A: replicates the PRJNA1056765 disease signature | False / not supported. |
| B: independently tests a prespecified clinical grouping | Conditional on direct mapping and a frozen plan; currently blocked. |
| C: contributes comparable ecological estimands while preserving its own contrast | Valid within-cohort role. |
| D: may be pooled with DR/DS-TB and four-level diagnosis as one disease effect | False / not supported. |

The structured response, including all reviewer attack points, is retained in [deepseek_preanalysis_gate.json](deepseek_preanalysis_gate.json).
