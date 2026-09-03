# Real 530-sample CZM sparsity compatibility audit

No CZM replacement, CLR, distance, permutation test, differential abundance, or biological inference was executed.

## Anchor

Input artifact: species rows × sample columns = [5198, 400].
Transformation view: sample rows × retained-species columns.

- prevalence 5%: retained=343; features >80% zero=267; samples >80% zero=305; compatible=False
- prevalence 10%: retained=186; features >80% zero=110; samples >80% zero=249; compatible=False
- prevalence 20%: retained=76; features >80% zero=0; samples >80% zero=169; compatible=False

## External

Input artifact: species rows × sample columns = [4888, 130].
Transformation view: sample rows × retained-species columns.

- prevalence 5%: retained=771; features >80% zero=635; samples >80% zero=106; compatible=False
- prevalence 10%: retained=353; features >80% zero=217; samples >80% zero=82; compatible=False
- prevalence 20%: retained=136; features >80% zero=0; samples >80% zero=53; compatible=False

## Options for method review (not selected or implemented)

- A — Keep 10% prevalence and raise `z.warning` enough to avoid deletion with `z.delete=TRUE`. Changes the frozen CZM parameterization; retains the prespecified feature/sample set and estimand, but weakens a diagnostic guard and requires an explicit justified bound recorded for reproducibility.
- B — Use a prevalence threshold intrinsically compatible with the 80% rule. Changes the frozen primary prevalence and feature set; the cohort-specific compositional estimand remains related but not identical, with reduced sparse-feature burden and a threshold-selection/reproducibility concern.
- C — Promote additive 0.5 CLR and demote CZM. Changes the frozen primary method while retaining samples/features and broad estimand; results can depend on arbitrary additive scale, though implementation is already authorized as sensitivity and reproducible.
- D — No additional reviewed solution is currently implemented; any alternative requires separate method review and authorization.

Classified/direct-assigned totals are technical count summaries, not biomass.
