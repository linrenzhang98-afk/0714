# PRJCA046985 deposited read-length discrepancy

## Observed pilot facts

`CRR2423962` is the sole validated fixed-length run. Its 175,080 reads were all exactly 50 nt, and the existing 50-nt Kraken2/Bracken path completed successfully. This validates only that run and workflow pairing; it does not establish fixed length for the other nominally 50-nt records.

`CRR2423909` is reclassified from expected fixed 75 nt to **`OBSERVED_VARIABLE_LENGTH_15_75_NT`**:

- total reads: 107,300
- distinct lengths: 57
- minimum: 15 nt
- maximum: 75 nt
- modal length: 75 nt
- reads exactly 75 nt: 34,865
- fraction exactly 75 nt: 0.324930, or 32.493%
- deposited-file processing: subject-linked supplementary output is labelled `unhost_reads`; exact host-removal tool/reference remains unrecovered
- host status: `HOST_DEPLETED`, unchanged

Supplementary Table S3 supplied a nominal or average pre-host-filter read length of 75 nt. Repository metadata exposed one deposited `.fq.gz` file but did not establish that every deposited read was fixed at 75 nt. Direct FASTQ inspection therefore contradicts the fixed-length interpretation, not the host-depleted classification.

## Cohort implication

The pilot establishes one fixed 50-nt run and one variable 15–75-nt run. It does not estimate the prevalence of variable-length files across the cohort. The remaining 128 records have only nominal 50/75-nt metadata, so they remain `UNVERIFIED`; classifying them as fixed would repeat the assumption disproven for `CRR2423909`.

Accordingly, `CRR2423909` cannot yet be called either an isolated exception or representative of a known fraction. It is cohort-relevant evidence that the metadata field does not establish deposited-file Bracken compatibility.
