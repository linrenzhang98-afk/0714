# Hospital pilot compatibility report

**Historical package verdict: DO_NOT_RUN, superseded by the live inventory and pending v3 DeepSeek gate.** The cohort-specific rows below preserve the earlier compatibility assessment.

## Read-only evidence inventory

The established project pathway records Kraken2 and Bracken at `/home/suma/anaconda3/envs/mgshotgun/bin/` and the classifier database at `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`. Thirty completed anchor jobs explicitly used `database100mers.kmer_distrib`. This repository snapshot does not provide live executable versions, a database content hash, an exhaustive redistribution-file listing, current free disk, or current CPU/RAM availability. No hospital file or service was modified.

The required rule is conservative: absence of verified evidence for a matching Bracken redistribution is a STOP, not a reason to build one.

| Cohort | Verdict | Reason |
|---|---|---|
| PRJCA039020 | **STOP / adaptation required** | Kraken2 input is technically plausible, but 40-nt Bracken compatibility is unverified. The deposit is qualified RAW; clinical grouping remains unresolved. |
| PRJCA046985 | **CONDITIONAL** | Direct DR/DS mapping is complete and files are small. Public files correspond to `unhost_reads`, but layout, exact host-depletion implementation and compatible 50/75-mer Bracken redistribution require live confirmation. |
| PRJNA977832 | **STOP** | Metadata-only by design; HIV mapping and host state are unresolved, and 40/50-nt Bracken compatibility is not evidenced. |

Current pilot working-space floor from the frozen one-run manifest is 5,000,000,000 bytes. Compatibility cannot be upgraded on historic command-path evidence alone. A future read-only workstation inventory must record `kraken2 --version`, `bracken -v`, executable hashes, database file inventory/hash/date, `database*mers.kmer_distrib`, `df`, CPU count and memory before raw-read execution. Host-state closure requires documentary provenance, not additional host filtering. A newly generated 40-mer redistribution would require separate validation and authorization and is outside this package.
