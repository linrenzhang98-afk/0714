# Pilot manifest v3 status

`pilot_manifest_v3.tsv` is preserved unchanged as the frozen pre-pilot execution manifest. Its expected fixed 75-nt classification for `CRR2423909` was an execution-time stop condition, not a post-pilot observation.

Post-pilot status:

- `CRR2423962`: directly validated `FIXED_50` for this run and workflow pairing only.
- `CRR2423909`: superseded by `OBSERVED_VARIABLE_LENGTH_15_75_NT`.
- No inference transfers fixed-length status to other nominally 50- or 75-nt records.

The current compatibility record is `prjca046985_read_length_audit.tsv`.
