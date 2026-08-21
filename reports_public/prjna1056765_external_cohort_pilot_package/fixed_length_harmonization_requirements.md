# Requirements before fixed-length harmonization could be adopted

This is a prospective evidence gate, not an implementation plan. No target length is selected.

## Target-length rule

The target must be justified by all of the following before taxonomic outcomes are viewed:

1. cohort-wide or prospectively sampled deposited-read length distributions;
2. retained-read fractions and retained bases at each candidate target;
3. technical evidence that truncation does not introduce unacceptable classification or compositional distortion;
4. compatibility with a verified redistribution derived from the exact frozen database;
5. applicability to the scientific estimand and anchor comparison.

Installed lengths are only feasibility constraints, not selection criteria. For the observed `CRR2423909` file, targets of 100–300 nt retain zero reads; 50 nt could retain at most 46,982/107,300 reads (43.786%), and 75 nt only 34,865/107,300 (32.493%). These observations make neither target acceptable without broader evidence.

## Minimum retained-read fraction

A conservative governance floor of **80% of input reads per sample and 80% of input bases per sample** is proposed for method evaluation. This is a project stop rule, not a literature-derived biological threshold. The distribution must also be inspected by clinical group and technical batch before outcomes; a material group- or batch-dependent retention imbalance is a stop even if every sample exceeds 80%.

`CRR2423909` fails the read-retention floor for both currently plausible installed targets.

## Read handling

- Reads shorter than the frozen target would be discarded.
- Reads longer than the target would be truncated deterministically to exactly the target length.
- Sequence and quality strings must remain synchronized.
- If inputs are paired, mates must remain synchronized. A pair-level rule must be frozen, normally discarding the pair if either mate fails the target, unless a separately validated orphan-read estimand is adopted.
- The PRJCA046985 deposit exposes one file per subject and pairing is undeclared; this must not be treated as proof of single-end library architecture.

## Cross-cohort application

Applying trimming only to PRJCA046985 creates a cohort-specific feature-generation difference. Before adoption, either:

1. all cohorts, including the anchor, receive the identical harmonization workflow; or
2. PRJCA046985 is analyzed with harmonization and the anchor receives a matched, prespecified sensitivity analysis demonstrating how the taxonomic/community estimand changes.

The frozen PRJNA1056765 v5 results remain unchanged. Any matched anchor processing is new analysis requiring separate approval.

## Required QC

Before and after trimming, record per sample:

- total reads and bases;
- complete length histogram;
- retained reads/bases and fractions;
- quality-score distribution;
- adapter/low-complexity status if available;
- paired synchronization and orphan counts where applicable;
- Kraken2 classified/unclassified fractions in a separately authorized technical validation;
- taxonomic resolution distribution;
- output checksum, tool version, command and manifest identity.

## Stop criteria

- any sample retains less than 80% of reads or bases;
- retained fraction is materially associated with clinical group or technical batch;
- pairing cannot be preserved or library layout is unresolved where it affects processing;
- the exact target redistribution is absent or mismatched to the database;
- trimming changes the cohort, primary contrast or QC population without prospective approval;
- benchmark or matched sensitivity evidence shows material taxonomy/community distortion;
- the target was selected because it produced favorable biological results.
