# Live DeepSeek variable-length method gate

**Verdict: INSUFFICIENT_EVIDENCE**

Model: `deepseek-v4-pro`

Review date: 2026-08-21

## Rationale

Official Bracken documentation creates one redistribution for one specified read length and accepts one `-r` value per abundance-estimation run. It provides no endorsed method for reducing a broad 15–75-nt mixture to its mean, mode or maximum. Software acceptance of a mixed-length Kraken report would not validate the abundance estimate.

## Methods not adopted

- **Fixed-length harmonization:** insufficient cohort-wide retention, pairing, bias, benchmark and matched-anchor evidence. The proposed 80% read/base floor is a project governance rule, not external validation; `CRR2423909` fails it at 50 and 75 nt.
- **Length-stratified Bracken:** no validated weighting, aggregation, sparse-bin or missing-redistribution method was found.
- **Kraken2-only common layer:** avoids Bracken's single-length mismatch but yields length-dependent classifier assignments, not Bracken-equivalent abundance. It requires a separately frozen common estimand and matched anchor sensitivity layer.
- **Switch primary cohort:** no screened alternative currently clears clinical mapping, provenance, size and read-length gates.
- **Mean/mode/maximum substitution:** unsupported; only 32.493% of `CRR2423909` reads equal its 75-nt mode and maximum.

## Consequences

PRJCA046985 remains a candidate, but `CRR2423909` is blocked from Bracken and 128 runs remain read-length unverified. `CRR2423962` validates only its own 50-nt workflow. The frozen PRJNA1056765 v5 anchor remains unchanged. Any harmonized or Kraken2-only anchor layer would be separately authorized new analysis.

## Required evidence

Further raw-read characterization is necessary to distinguish an isolated variable-length file from a cohort-relevant deposition pattern. The proposed audit is limited to eight metadata-stratified files and 12,866,805 cumulative bytes. It may produce only transfer-integrity and complete read-length outputs. It cannot validate trimming, stratified aggregation, Kraken2-only comparability or any biological claim.

Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T14-43-27-237Z-74856.jsonl`
