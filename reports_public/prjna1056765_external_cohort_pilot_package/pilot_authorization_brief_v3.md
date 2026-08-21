# Pilot authorization brief v3

The bounded option submitted to DeepSeek is **Option C: PRJCA046985 technical smoke test**.

- Runs: `CRR2423962` and `CRR2423909`
- Expected read lengths: 50 and 75 nt
- Exact total: 10,526,255 bytes, or 0.010526 GB decimal
- Host status: already host-depleted; no second host-removal stage
- Installed matching Bracken lengths: 50 and 75 nt, conditional on FASTQ confirmation
- Caps: two runs, 8 threads, 64 GiB RAM, 5 GB workspace, 8 h and two retries; 10,526,255 bytes is the cumulative transfer ceiling across all attempts
- Integrity: exact file identifiers/bytes plus ETag and gzip/FASTQ checks; GSA cryptographic checksums were not published
- Stop conditions: accession/size/transport mismatch, invalid gzip/FASTQ, unexpected layout, any mixed or nonconforming read length, missing expected Bracken file, resource cap, repeated failure or any biological comparison

The pilot may validate the end-to-end technical path through Bracken. It cannot estimate DR/DS differences or provide scientific evidence from two samples. Direct clinical mapping makes the full cohort eligible for later prespecified design review, but this pilot does not establish scientific validity.

The database and redistribution files are read-only inputs. Before classification, record their hashes or, if hashes are unavailable, file sizes and modification times.

Option B is not authorized or executed. A dedicated 40-nt derivative requires a separate future approval.
