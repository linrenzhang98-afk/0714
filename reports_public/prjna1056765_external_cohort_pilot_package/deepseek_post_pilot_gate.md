# Live DeepSeek post-pilot gate

**Verdict: REQUIRE_VARIABLE_LENGTH_METHOD_REVIEW**

Model: `deepseek-v4-pro`

Review date: 2026-08-21

## Blocking issues

- `CRR2423909` cannot be dismissed as isolated. Its 57 observed lengths show that nominal/average 75-nt metadata does not establish deposited-file fixed length. The prevalence of variable-length files remains unknown because 128 runs are unverified.
- No replacement fixed-length run is defensible from nominal/average 50/75-nt metadata alone.
- Any exclusion, trimming, length stratification, Kraken2-only or alternative-estimator strategy requires a separate prospective methodological review.

## Evidence assessment

The classification of one directly verified fixed 50-nt run, one directly observed variable-length run and 128 unverified runs is supported. The successful `CRR2423962` result validates that run and workflow pairing only. The mixed-length stop for `CRR2423909` was correct. `HOST_DEPLETED` remains supported, and no biological inference was made.

## Cohort decision

Current evidence blocks a replacement pilot but does not justify abandoning PRJCA046985 as the primary external cohort before variable-length method review.

## Low-risk edits applied

- Preserved `pilot_manifest_v3.tsv` unchanged and added a companion status record identifying it as the superseded pre-pilot expectation.
- Replaced a named-reviewer dependency with a role-based independent-review requirement.
- Clarified that the 50-nt validation does not transfer to other nominally 50-nt runs.

Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T13-51-52-382Z-71981.jsonl`
