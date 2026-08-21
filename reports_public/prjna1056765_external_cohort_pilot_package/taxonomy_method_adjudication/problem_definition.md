# Taxonomy method adjudication

## Decision to be made

PRJCA046985 cannot be processed prospectively with one nominal Bracken read length: seven of eight audited files contained multiple lengths, across nominal 50-nt and 75-nt strata. The immediate decision is whether a scientifically bounded common taxonomy estimand can be defined without modifying the frozen PRJNA1056765 v5 anchor or inventing a mixed-length Bracken correction.

The cross-study objective is cohort-specific analysis followed by comparison of effect structures. Samples and abundance matrices will not be pooled. A common layer must use the same classifier version, database identity, classifier parameters, taxonomic rank, count normalization and reporting rules in both cohorts. It must be named according to what it measures.

## Fixed boundaries

- Frozen PRJNA1056765 Kraken2+Bracken v5 results remain the anchor's primary record.
- A possible Kraken2-only result is a separate sensitivity estimand, not Bracken abundance and not a replacement for v5.
- Native mixed-length reads cannot be passed to Bracken with their maximum, mean, median or mode as a surrogate length.
- Length-stratified Bracken is not admissible without an externally validated aggregation rule.
- Clinical labels and run–sample–subject mappings cannot be inferred from sequence output.
- No primary analysis will pool samples, abundance matrices or diagnosis-associated R² across studies.

## Evidence available before adjudication

- Eight-run length audit: 12,866,805 exact downloaded bytes; 1 strictly fixed and 7 variable files; modal fractions 22.911–100%.
- Earlier technical pilot: CRR2423962 was strictly 50 nt and completed Kraken2 plus matching 50-nt Bracken; CRR2423909 ranged 15–75 nt and stopped before classification.
- Hospital classifier: Kraken2 2.17.1, Bracken 3.0.1, database `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`; installed Bracken lengths 50, 75, 100, 150, 200, 250 and 300 nt.
- Deposited PRJCA046985 files are treated as host-depleted on direct supplementary/repository provenance; no second host filtering is planned.

## Question for the gate

Can native-read Kraken2 classifier assignments be frozen as a legitimate cross-cohort sensitivity estimand, provided both cohorts are processed identically and interpreted only within cohort before cross-study synthesis? If current evidence cannot establish this, the gate must specify the smallest technical benchmark capable of separating that option from fixed-length harmonization or cohort replacement.
