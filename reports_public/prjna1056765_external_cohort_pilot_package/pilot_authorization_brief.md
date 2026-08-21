# Bounded pilot authorization brief

**Current independent gate verdict: DO_NOT_RUN.** This is a frozen candidate package, not an execution authorization.

1. **First-pilot cohort:** PRJCA039020 / PRJDB36521, technical-only candidate.
2. **Frozen run:** `DRR770839`.
3. **Role/group:** technical compatibility only; subject and CAP/severe group unresolved.
4. **Exact download:** 47,008,516 bytes (0.047009 GB decimal).
5. **Working-space floor:** 5,000,000,000 bytes (5.000 GB decimal), checked again immediately before execution.
6. **Runtime:** bounded at 24 h; expected under 2 h for this sub-GB file if network and classifier are healthy, but no live benchmark is claimed.
7. **Compatibility:** **STOP / adaptation required** because 40-nt Bracken compatibility is unverified; only 100-mer use is evidenced.
8. **Host depletion:** qualified RAW. Paper Data Availability calls the deposit raw sequence data, with Benzonase before library construction and SNAP hg38 in downstream analysis.
9. **Negative controls:** none publicly identified; the frozen technical pilot contains no negative control.
10. **Stop conditions:** checksum mismatch; accession outside allowlist; size above manifest/cap; layout/read-length mismatch; unresolved host state at filtering stage; missing matching Bracken redistribution; insufficient disk/RAM; repeated download/tool failure; any request for biological inference.
11. **Can establish:** download integrity, FASTQ structure, observed read length, existing-host-state compatibility, Kraken2/Bracken executable compatibility if all STOPs clear, runtime/disk use, classified fraction and output layout.
12. **Cannot establish:** CAP/severe differences, diagnosis effect, taxa, biomarkers, PERMANOVA, biological replication, or cohort validity.

This package is not executable. Raw-read authorization must not be requested unless an independent gate review records `APPROVE_BOUNDED_PILOT` after the host-state and 40-mer compatibility blockers close.
