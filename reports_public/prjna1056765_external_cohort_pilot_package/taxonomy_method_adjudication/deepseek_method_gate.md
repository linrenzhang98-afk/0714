# Stage 1 DeepSeek taxonomy-method gate

**CONDITIONAL_GO:** proceed only with the frozen four-sample, zero-new-download technical benchmark in `benchmark_design.md`.

Model: `deepseek-v4-pro`

Mode: thinking

Review date: 2026-08-22

## Method adjudication

- **A — Kraken2-only common sensitivity estimand: CONDITIONAL_GO.** Native Kraken2 classifier assignments are a plausible, explicitly distinct sensitivity estimand, but they are not yet legitimate for cross-cohort inference. The benchmark must establish their sensitivity to the proposed 50-nt transformation. Any later cross-cohort use also requires a separately frozen, parameter-identical PRJNA1056765 Kraken2-only layer.
- **B — Fixed-length harmonization: INSUFFICIENT_EVIDENCE.** It is not adoptable without direct retention and taxonomy-distortion evidence. The 80% read/base threshold remains an internal governance floor.
- **C — Length-stratified Bracken: NO_GO / NOT VALIDATED.** No externally validated aggregation rule exists in the reviewed evidence. This branch must not be implemented.
- **D — Switch external cohort: NO_GO at this stage.** The screened alternatives retain material mapping, provenance, compatibility or compute blockers. Switching remains a reserve action, not the default response to PRJCA046985 complexity.

## Smallest discriminating benchmark

Use exactly `CRR2423957`, `CRR2424000`, `CRR2423921` and `CRR2424010`, already present in the hospital audit workspace. Compare Native Kraken2 with deterministic Trim50 Kraken2, and compare Trim50 Kraken2 with matching 50-nt Bracken only as an estimator contrast. `CRR2423957` is the fixed-50 identity control. Use the exact frozen classifier/database parameters and all universal stop rules. New raw download is prohibited for this benchmark.

## Supervisor record

DeepSeek returned `STEER` because the package lacked a persisted final gate statement, while explicitly determining that the scientific gate should be `CONDITIONAL_GO`. This file implements that exact steering instruction without broadening the design.

Supervisor response was recovered from `/tmp/stage1_deepseek_gate.json`. Usage: 4,057 prompt tokens, 3,856 completion tokens; thinking mode; no retry.
