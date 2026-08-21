# Minimal discriminating benchmark design

## Purpose

The benchmark is technical. It asks whether native Kraken2 assignments are sufficiently stable to read-length harmonization to support a named Kraken2-only sensitivity estimand, and whether 50-nt harmonization causes unacceptable, sample-dependent information loss. It cannot establish disease effects or validate the external cohort scientifically.

## Frozen sample roles

Use four already downloaded hospital-side audit files, chosen before taxonomy from read architecture alone:

| Run | Architecture role | Observed lengths | Modal fraction |
|---|---|---|---:|
| CRR2423957 | strictly fixed 50 nt | 50 only | 100.000% |
| CRR2424000 | near-modal 50 nt | 15–50 | 98.663% |
| CRR2423921 | near-modal 75 nt | 15–75 | 98.105% |
| CRR2424010 | strongly mixed 75 nt | 15–75 | 22.911% |

No clinical outcome enters selection or interpretation. Zero new raw download is preferred. If any selected FASTQ is not retained on the hospital workstation with the published checksum, the benchmark stops rather than substituting another accession.

## Pipelines

1. **Native K2:** unmodified deposited host-depleted reads to the frozen Kraken2 classifier.
2. **Trim50 K2:** retain reads at least 50 nt, trim retained reads deterministically to 50 nt, then use the same Kraken2 settings.
3. **Trim50 K2+Bracken50:** use the exact Trim50 Kraken report and the installed `database50mers.kmer_distrib` at species rank.

Native mixed-length Bracken is prohibited. CRR2423957 acts as a transformation identity control: Trim50 must be sequence-identical to native input and its Kraken2 report must reproduce exactly apart from nondeterministic metadata. Trimming is performed only in a benchmark workspace; source FASTQs remain unchanged.

## Frozen classifier parameters

- Kraken2 executable/version: hospital inventory, expected 2.17.1.
- Database: `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209` with manifest identity `6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3`.
- Confidence: `0.0` unless the prior validated runner proves a different frozen value.
- Minimum hit groups: Kraken2 default unless the prior runner proves an explicit frozen value.
- Output: standard per-read assignments and Kraken report; genus and species tables derived deterministically.
- Bracken: 3.0.1, species rank, threshold 10, exact installed 50-nt redistribution.

Any mismatch between these expected settings and the validated pilot command causes a pre-execution STOP and a deviation report.

## Measurements

For every run and pipeline record total reads/bases, retained reads/bases and fractions, classified/unclassified fractions, genus/species observed support, top assigned taxa, and output hashes. Compare Native K2 with Trim50 K2 using Spearman correlation on a fixed union taxon universe, Bray–Curtis dissimilarity, and absolute/relative changes for prespecified major taxa defined as the union of taxa reaching at least 1% in either representation. Compare Trim50 Kraken2 with Trim50 Bracken only as an estimator contrast; do not label it a truth benchmark.

## Resource envelope

- New download: 0 bytes.
- Samples: exactly 4 allowlisted runs.
- Threads: at most 16.
- RAM target: at most 64 GiB with bounded monitoring.
- Temporary workspace: at most 100 GB; use a tighter 5-GB cap if observed input sizes and Kraken outputs permit.
- Total wall time: at most 8 hours.
- No database derivative, rebuild, update or environment change.

## Outputs

Machine-readable manifest, input checksums, command ledger, runtime/resource ledger, per-run retention table, classifier summary table, taxon-stability table, comparison table, database identity, software versions, stop/deviation record and a no-biological-inference statement.
