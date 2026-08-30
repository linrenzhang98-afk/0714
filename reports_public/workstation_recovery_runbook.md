# ETYY workstation recovery runbook

This is a manual checklist. It does not authorize or queue any job.

1. **Verify network externally.** Confirm hospital network and the normal GitHub transport path; do not initiate WSL-to-ETYY SSH.
2. **Verify runner observability.** Check the established ETYY timer/service and its last event through the authorized control channel. Preserve timestamps and logs.
3. **Inspect the old installation job.** Locate job `20260825T140844Z-0714-zcompositions-1-6-2-isolated-install` and its state/handoff only. Do not create a duplicate.
4. **Preserve old state.** Record job envelope SHA, execution commit, state file, logs, handoff presence and target-library directory metadata before recovery. Do not delete, overwrite or reuse a nonempty partial library.
5. **Classify exactly one state.** `READY` requires a complete valid handoff, exact package/version/path, unchanged system library and passing synthetic CZM. `SAFE_STOP` means the old job recorded a bounded failure. `NOT_SEEN` means no reliable execution evidence exists. Unknown remains unknown.
6. **Bounded recovery only if needed.** Follow the existing isolated-install contract and frozen tarball hashes. Preserve scientific scope, installation target and system library. A technical SAFE_STOP does not justify a new method.
7. **Verify zCompositions 1.6.2.** Resolve it from `/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3`; verify NADA/truncnorm dependencies and ensure the system package set/versions are unchanged.
8. **Run synthetic CZM conformance.** Execute the frozen small zero-containing matrix twice with the exact `cmultRepl` parameters. Require finite positive output, unit-sum proportions, stable dimensions and deterministic equality. No biological matrix is read here.
9. **Freeze the actual method environment.** Record R 4.5.3, package versions/paths, adapter hash, input/job hashes, locale and synthetic conformance output in an immutable execution commit.
10. **Obtain/confirm the visible formal-analysis authorization.** Verify the accepted plan, source handoff, sample universe, counts definition, seeds and output contract. Do not infer authorization from installation success alone.
11. **Execute primary Aitchison analysis.** Run anchor and external cohorts separately at 10% with exact CZM, 9,999 PERMANOVA and 9,999 paired PERMDISP; preserve the Training/Test restriction for the anchor.
12. **Validate before interpretation.** Require exact group/sample counts, hashes, no all-zero samples, closure/CLR/distance invariants, deterministic replay, schema-valid JSON and complete compact tables. A failure is `ANALYSIS_QC_FAILURE`.
13. **Review primary results before DA.** Apply `post_primary_decision_rules.md`, inspect dispersion, Aitchison/Bray behavior, secondary ecology, classified-fraction technical confounding and 5/10/20% stability. DA remains off unless a separate decision is recorded.

At every step: no force push, raw-data commit, legacy checkout modification, secret exposure or automatic new job.
