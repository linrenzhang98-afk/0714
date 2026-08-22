# PRJNA1056765 anchor compatibility audit

Audit date: 2026-08-22

## Recovered ETYY provenance reconciliation

The authoritative repository record `anchor_reconciliation_v2.json` closes the artifact and actual-command blockers exactly. It was generated with corrected `SRR\d+` extraction and command classification based only on `args[0]`/actual executable identity.

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

## Exact report-class reconciliation

The V2 inventory keeps the file classes separate:

- Native Kraken2 class: exactly 400 files representing exactly 400 frozen runs, with no missing, extra or duplicate run membership.
- Bracken-derived `*_bracken_species.kreport` class: exactly 400 files representing exactly 400 runs; these are not native classifier reports and are excluded from the common layer.

The earlier combined scan count of 1124 is retired for anchor admission and is never treated as a native-report count.

## Exact historical command reconciliation

Twenty original production `command_log.jsonl` files contain exactly 400 actual Kraken2 command records. All 400 succeeded and reconcile one-to-one to the frozen 400-run anchor membership. Command identity is determined from `args[0]`, preventing Bracken paths containing `/kraken2/` from being misclassified.

The single historical Kraken2 method signature is:

- executable: `kraken2`
- database: `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`
- threads: `4`
- `--report`, `--output` and one input FASTQ
- `--confidence`: not explicitly passed; historical default behavior
- `--minimum-hit-groups`: not explicitly passed; historical default behavior

Kraken2 2.17.1 remains `VERIFIED_PROVENANCE`, not `VERIFIED_EXACT`. Database identity remains sufficient `VERIFIED_PROVENANCE`; `hash.k2d` is not newly hashed.

No taxonomy rerun is justified. The frozen PRJNA1056765 Kraken2+Bracken v5 analysis remains unchanged.

## Compatibility rule

Every method-defining field is now `VERIFIED_EXACT` or supported by adequate immutable `VERIFIED_PROVENANCE`, and no field is `CONFLICTING`. The corrected package is ready for DeepSeek to decide anchor admission and pilot authorization. No anchor rerun occurred or is methodologically indicated by this audit.

## Cross-environment handoff rule

ETYY is compute-only. WSL/Codex is the sole Git writer. Future ETYY evidence crossing environments must be written to `/mnt/disk1/0714_handoff/` and retrieved by WSL; ETYY must not create Git commits or rely on `/tmp` as the only evidence location.
