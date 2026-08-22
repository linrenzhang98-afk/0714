# PRJNA1056765 anchor compatibility audit

Audit date: 2026-08-22

## Decision before independent review

The checked-in PRJNA1056765 summaries do **not yet directly constitute** the anchor side of the Kraken2-only common sensitivity layer. The original per-run Kraken reports are the correct reusable intermediate, but they and their command ledgers are not present in this checkout, and `/mnt/disk1` is not mounted after reboot.

No contradictory method evidence was found. The gap is provenance and artifact availability, not a failure of the selected native-read Kraken2 estimand.

## Verified provenance

- The production plan, job generator and runner consistently name `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`.
- The anchor production candidate set is 400 DNA WGS `SINGLE` runs. The runner supplied one native FASTQ positional input and did not enable `--paired`.
- The runner command generated standard Kraken2 reports without `--report-zero-counts`, `--confidence` or `--minimum-hit-groups` overrides. This corresponds to confidence 0.0 and minimum hit groups 2; the prospective command freezes both explicitly.
- The checked-in production QC proves 400 successful Kraken2/Bracken records and preserves total, classified and unclassified read counts, but it is not a substitute for rank-wise Kraken2 classifier counts.
- Host removal was not performed before the original anchor classifier run. PRJCA046985 depositions are already host-depleted; this upstream difference must be reported and must not be disguised as classifier comparability.
- The later live inventory verifies Kraken2 2.17.1 and database manifest identity `6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3` on 2026-08-21. Those facts freeze the prospective external-cohort environment but do not by themselves prove the July anchor execution environment or that database contents were unchanged.

## Missing method-defining evidence

- Kraken2 version at anchor production execution.
- Immutable database identity at anchor production execution.
- Original anchor `.kreport` availability in the current workspace.
- Per-batch `command_log.jsonl` availability to verify actual commands against the frozen runner.

The original reports should be recovered and inspected before considering any rerun. A rerun is necessary only if those reports or their method-defining provenance cannot be recovered. The frozen PRJNA1056765 Kraken2+Bracken v5 analysis remains unchanged either way.

## Compatibility rule

Direct reuse is executable only when every method-defining field is `VERIFIED_EXACT` or supported by adequate immutable `VERIFIED_PROVENANCE`, no field is `CONFLICTING`, and the raw Kraken2 report artifacts exist and pass membership/format checks. Later path agreement alone cannot upgrade execution-time software or database identity to exact verification.
