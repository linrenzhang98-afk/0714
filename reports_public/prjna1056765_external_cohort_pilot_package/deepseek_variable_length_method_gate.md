# Live DeepSeek variable-length method gate

**Verdict: INSUFFICIENT_EVIDENCE**

Model: `deepseek-v4-pro`

Review date: 2026-08-22

## Rationale

The completed metadata-stratified audit found one strictly fixed-length file and seven variable-length files among eight runs. Variable-length deposition occurred in both nominal 50-nt and nominal 75-nt strata. Several files were strongly dominated by the nominal maximum, but modal dominance is not fixed length. Together with the earlier mixed-length `CRR2423909` result, this makes variable-length deposition cohort-relevant rather than an isolated run anomaly.

Official Bracken documentation creates one redistribution for one specified read length and accepts one `-r` value per abundance-estimation run. It provides no endorsed method for reducing these within-file mixtures to their mean, mode or maximum. Software acceptance of a mixed-length Kraken report would not validate the abundance estimate.

## Methods not adopted

- **Fixed-length harmonization:** still lacks cohort-wide retention, pairing, bias, benchmark and matched-anchor evidence. The audit shows that retention would vary materially: the modal fraction ranged from 22.911% to 100%. The proposed 80% read/base floor is a project governance rule, not external validation.
- **Length-stratified Bracken:** no validated weighting, aggregation, sparse-bin or missing-redistribution method was found.
- **Kraken2-only common layer:** avoids Bracken's single-length mismatch but yields length-dependent classifier assignments, not Bracken-equivalent abundance. It requires a separately frozen common estimand and matched anchor sensitivity layer.
- **Switch primary cohort:** no screened alternative currently clears clinical mapping, provenance, size and read-length gates.
- **Mean/mode/maximum substitution:** unsupported. Exact modal fractions were 22.911–100% in the audit and 32.493% for the earlier `CRR2423909` pilot.

## Consequences

PRJCA046985 remains scientifically attractive but is not ready for a common Bracken workflow. `CRR2423962` and audited `CRR2423957` validate only their own strictly 50-nt files; near-modal files cannot use a nominal redistribution without a validated method. The frozen PRJNA1056765 v5 anchor remains unchanged. Any harmonized or Kraken2-only anchor layer would be separately authorized new analysis.

## Required evidence

The bounded audit answered the immediate anomaly question, so no additional raw-read characterization is required merely to establish that variable-length deposition is cohort-relevant. It did not validate trimming, stratified aggregation, Kraken2-only comparability or any biological claim. A new prospective method plan, including an anchor-comparability strategy, would be required before any taxonomy or cohort-scale processing.

Live post-audit gate: `APPROVE` with scientific verdict `INSUFFICIENT_EVIDENCE`.

Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T17-05-12-818Z-84273.jsonl` (executor transport failure), `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T17-06-19-573Z-85020.jsonl` (read-only evidence inspection), followed by a direct `deepseek-v4-pro` thinking-mode completion gate (1,526 prompt tokens; 1,169 completion tokens).
