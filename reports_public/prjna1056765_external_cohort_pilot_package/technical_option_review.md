# Bounded technical decision review

## Decision summary

**Preferred: Option C, a two-run PRJCA046985 technical pilot with prespecified stop-on-length-mismatch rules.** It uses a scientifically stronger cohort with direct clinical mapping and expected 50/75-nt read architectures that match installed Bracken files. The pilot remains technical until the deposited FASTQ confirms those lengths. No biological comparison is permitted at pilot scale.

**Fallback: Option A, Kraken2-only DRR770839.** This is the lowest-risk way to test the PRJCA039020 transport and Kraken2 path but cannot validate the end-to-end Kraken2/Bracken workflow.

**Deferred: Option B, isolated 40-nt derivative generation.** It is reproducible in principle but unnecessary before testing an already compatible candidate cohort and would create a new database derivative.

| Criterion | A: DRR770839 Kraken2-only | B: isolated 40-nt derivative | C: PRJCA046985 matching-length pilot |
|---|---|---|---|
| Scientific usefulness | Low; CAP/SP labels unresolved | Indirect; enables later PRJCA039020 processing but not labels | Highest; direct 49 DR-TB/81 DS-TB mapping exists |
| Technical risk | Low; explicit stop before Bracken | Moderate; derivative build can fail and needs source database assets | Low–moderate; deposited lengths must be confirmed before Bracken |
| Time to execution | Short after raw-read approval | Estimated 4–24 h build plus validation, before any pilot | Short after raw-read approval; two public files total ~10.5 MB |
| Database modification | None | New isolated derivative only; never write to shared DB | None |
| Reproducibility | High but incomplete workflow | High if isolated manifest, commands and hashes are frozen | High if exact files, ETags/bytes, observed lengths and installed derivatives are recorded |
| Resolves external pipeline question | Partially: download/FASTQ/host/Kraken2 only | Enables full PRJCA039020 technical path later | Best near-term end-to-end test of download through Bracken |
| Supports later scientific design | No, without CAP/SP map | No, without CAP/SP map | Potentially; direct clinical mapping permits later full-cohort prespecification, but the pilot itself has no inferential value |

## Option A

Allowlist only `DRR770839` (47,008,516 bytes). Verify MD5, FASTQ structure and the observed 40-nt length, preserve the downloaded RAW file, perform at most one documented computational host-removal stage, then run Kraken2. Stop before Bracken. Classified fraction is a technical metric, not biological evidence.

## Option B

The official Bracken 3.0.1 interface is conceptually:

```text
bracken-build -d <isolated_db_path> -t 16 -k <verified_kraken_kmer_length> -l 40 -x /home/suma/anaconda3/envs/mgshotgun/bin -y kraken2
```

Before execution, obtain the Kraken2 k-mer length from the frozen database metadata rather than assuming 35. The build writes intermediate `database40mers.kraken` and final `database40mers.kmer_distrib` inside the target database directory. It must never target the shared production path.

Isolation plan:

1. Create a versioned derivative directory outside the shared DB.
2. Copy or snapshot the complete frozen database with reflink/copy-on-write where supported; do not use writable symlinks back to shared files.
3. Freeze the source database identity, Bracken/Kraken versions, command, environment, file manifest and pre-build hashes.
4. Run with at most 16 threads and a conservative 24-h stop.
5. Retain only the isolated derivative after checks; rollback means deleting/quarantining that new derivative directory, never modifying the source.

Estimated runtime is 4–24 h with 16 threads; official documentation warns that single-threaded builds may take hours to days. Reserve at least 100 GB working space until actual source/intermediate sizes are inventoried. A prebuilt database may lack source library assets required by `bracken-build`; failure must stop without downloading replacements. These are planning estimates, not measured values.

## Option C

PRJCA046985 has 130 direct DNA run-to-subject-to-group mappings. Supplementary Table S3 reports average pre-host-filter read architectures of exactly 50 nt for 81 records and 75 nt for 49 records. Both clinical groups occur in both length strata, so read length is not perfectly confounded with DR/DS status. Public files map to the Table S3 `unhost_reads` records.

Freeze two metadata-representative files selected near the within-cell median compressed size:

- `CRR2423962`, Drug_Sensitive, expected 50 nt, 6,450,611 bytes.
- `CRR2423909`, Drug_Resistance, expected 75 nt, 4,075,644 bytes.

Their roles are technical architecture checks, not a two-sample biological contrast. GSA did not publish a cryptographic checksum in the verified pages; integrity uses exact Content-Length, file identifier, ETag where available and post-download gzip/FASTQ checks. Each run stops before Bracken if observed deposited length does not exactly match 50 or 75 nt. Already host-depleted files must not undergo a second host-removal stage.
