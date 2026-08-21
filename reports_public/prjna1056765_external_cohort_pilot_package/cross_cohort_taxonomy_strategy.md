# Cross-cohort taxonomy strategy under variable read lengths

## Current recommendation

Do not run Bracken on mixed-length files and do not adopt fixed-length harmonization yet. The leading contingency is a **Kraken2-only common taxonomy layer**, but it is not authorized as the primary scientific workflow with current evidence.

## Proposed bounded estimand

If later approved, each cohort would be processed independently with the same frozen Kraken2 database and reporting grammar. Outputs would retain classified and unclassified counts, taxonomic rank and sample-level technical metrics. Community analyses would remain within cohort. Cross-cohort synthesis would compare cohort-level effect sizes and robustness behavior, not pool raw abundance matrices.

Kraken2 counts or proportions would be named explicitly as classifier assignments. They would not be called Bracken abundance and would not be assumed unbiased across read-length distributions.

## Anchor consequence

Cross-cohort interpretation requires a matched Kraken2-only layer for PRJNA1056765. Existing frozen v5 Bracken-derived conclusions remain the anchor's primary record; a Kraken2-only analysis would be a separately frozen sensitivity layer. Without it, differences between the anchor and PRJCA046985 could reflect abundance-estimator choice rather than cohort behavior.

## Why alternatives are not currently superior

- Fixed-length trimming would discard most reads in the one observed variable-length file at 50 or 75 nt and has unknown cohort-wide retention bias.
- Length-stratified Bracken lacks validated aggregation mathematics.
- PRJCA039020 has unresolved individual CAP/severe mapping and lacks 40-nt Bracken redistribution. PRJNA977832 has unresolved mapping/provenance and a 917-GB footprint. PRJCA027972 remains a reserve with clinical-label validation pending. None is presently a clean primary replacement.

## Evidence still required

A small metadata-stratified raw-read length audit is necessary to learn whether `CRR2423909` is exceptional or reflects deposited preprocessing across PRJCA046985. This audit would inspect length distributions only and would not run taxonomy.

### Separate minimal read-length audit proposal

Eight runs, selected solely by nominal metadata stratum, clinical group and smallest file size within each stratum:

| Nominal length | Clinical group | Runs | Bytes |
|---|---|---|---:|
| 50 nt | Drug Sensitive | CRR2423961, CRR2424000 | 3,531,641 |
| 50 nt | Drug Resistance | CRR2423957, CRR2423986 | 5,083,396 |
| 75 nt | Drug Sensitive | CRR2423912, CRR2423921 | 1,797,711 |
| 75 nt | Drug Resistance | CRR2423991, CRR2424010 | 2,454,057 |

Exact maximum cumulative download: **12,866,805 bytes**.

Permitted future operations would be download identity/size checks, gzip/FASTQ integrity and complete read-length histograms. No trimming, host filtering, Kraken2, Bracken, taxonomy or biological inference would be permitted. The audit requires explicit new raw-read authorization before execution.
