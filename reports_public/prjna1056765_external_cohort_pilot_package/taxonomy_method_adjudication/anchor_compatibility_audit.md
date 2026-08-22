# PRJNA1056765 anchor compatibility audit

Audit date: 2026-08-22

## Recovered ETYY provenance reconciliation

The original per-run Kraken reports and multiple original `command_log.jsonl` files remain accessible on ETYY. This closes the prior artifact-existence and ledger-existence blockers at `VERIFIED_PROVENANCE`. It does not by itself prove the exact native-report membership or actual logged Kraken2 arguments because the recovery listing and representative JSONL records were not persisted into this checkout.

No contradictory method evidence was found. The gap is provenance and artifact availability, not a failure of the selected native-read Kraken2 estimand.

## Verified provenance

- The production plan, job generator and runner consistently name `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`.
- The anchor production candidate set is 400 DNA WGS `SINGLE` runs. The runner supplied one native FASTQ positional input and did not enable `--paired`.
- The runner command generated standard Kraken2 reports without `--report-zero-counts`, `--confidence` or `--minimum-hit-groups` overrides. This corresponds to confidence 0.0 and minimum hit groups 2; the prospective command freezes both explicitly.
- The checked-in production QC proves 400 successful Kraken2/Bracken records and preserves total, classified and unclassified read counts, but it is not a substitute for rank-wise Kraken2 classifier counts.
- Host removal was not performed before the original anchor classifier run. PRJCA046985 depositions are already host-depleted; this upstream difference must be reported and must not be disguised as classifier comparability.
- Recovered conda metadata records Kraken2 2.17.1 and Bracken 3.1 in both `mgshotgun` and `clinical_meta`. Historical execution scripts select `mgshotgun`. Kraken2 2.17.1 is therefore `VERIFIED_PROVENANCE`, not `VERIFIED_EXACT`, because no execution-time version record was recovered.
- Database identity is `VERIFIED_PROVENANCE`: historical job files and recovered command provenance consistently name `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`; core files retain 2022 timestamps; `opts.k2d` SHA-256 is `80279333ae8d2e88f7bab5946ac843692d1662577d4a5f69a742c252f3f1d28b`; `taxo.k2d` SHA-256 is `4cf75aa017ec1a78edeb4a058ba2b7ab3117c0b8fb03213859b39ac2cfbded85`; and the frozen manifest identity is `6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3`.
- `hash.k2d` is 16,000,000,032 bytes with 2022 mtime and was intentionally not newly hashed. No decision is conditioned on hashing it unless DeepSeek identifies that exact hash as the single decision-changing item.

## Report-class reconciliation

The recovery scan found **1124 total `*.kreport` files**. This is not a native Kraken2 report count.

- Native class: `*.kreport` excluding `*_bracken_species.kreport` and other derived-report directories.
- Bracken-derived class: `*_bracken_species.kreport`.
- Native count: `MISSING` from the persisted evidence.
- Bracken-derived count: `MISSING` from the persisted evidence.

The remaining method-defining gaps are a suffix/path-classified native inventory tied to the frozen 400-run anchor membership and representative actual Kraken2 `args` records from the original production command ledgers. Ledger and artifact accessibility are no longer missing.

No taxonomy rerun is justified. The frozen PRJNA1056765 Kraken2+Bracken v5 analysis remains unchanged.

## Compatibility rule

Direct reuse is executable only when every method-defining field is `VERIFIED_EXACT` or supported by adequate immutable `VERIFIED_PROVENANCE`, no field is `CONFLICTING`, and the native Kraken2 reports pass frozen membership/format checks. The combined count of 1124 must never be substituted for the native count, and runner-template provenance must not be substituted silently for the actual logged invocation.
