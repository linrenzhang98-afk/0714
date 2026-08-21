# Minimal PRJCA046985 deposited-read length audit proposal

**Status: AWAITING EXPLICIT RAW-READ AUTHORIZATION.**

## Frozen scope

- Runs: exactly eight, listed in `prjca046985_read_length_audit_manifest.tsv`.
- Exact cumulative download ceiling: **12,866,805 bytes** across all runs and attempts.
- Sampling: two smallest previously unobserved files in each nominal-length × clinical-group metadata stratum. Selection uses file architecture and size only, never taxonomy or biological outcome.
- Inputs remain classified `HOST_DEPLETED`; no host filtering is allowed.

## Allowed outputs

- accession, URL/file identity and exact byte verification;
- available repository checksum or a locally computed SHA-256;
- gzip and FASTQ structural integrity;
- total reads;
- exact complete read-length histogram, distinct-length count, minimum, maximum and mode.

## Prohibited operations

- trimming, filtering or rewriting reads;
- Kraken2, Bracken or any taxonomy tool;
- new database or redistribution generation;
- biological, clinical-group or taxonomic inference;
- accession substitution, additional runs or cohort expansion.

## Stop conditions

- any accession or byte mismatch;
- cumulative transferred bytes would exceed 12,866,805;
- FASTQ integrity failure;
- host-depletion provenance becomes uncertain;
- any operation beyond integrity and read-length characterization becomes necessary.

This audit can estimate whether variable-length deposition occurs across the prespecified technical strata. It cannot validate a downstream abundance method.
