# Candidate taxonomy methods

## Method A: Kraken2-only common sensitivity estimand

This option retains all native reads and avoids applying an unsupported Bracken redistribution to variable-length files. The estimand is explicitly the distribution of Kraken2 classifier assignments, including the unclassified fraction. It is not an unbiased abundance estimate and is not interchangeable with Bracken output.

Scientific admissibility requires an exactly matched layer for PRJNA1056765 and PRJCA046985: Kraken2 2.17.1, database manifest identity `6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3`, the same confidence and minimum-hit-group settings, species/genus reporting rules and sample-level normalization. Existing intermediate Kraken reports may be reused only if their parameter and database identities are proven identical. Otherwise, any anchor recalculation is a new, separately frozen sensitivity layer and does not alter v5.

Permitted future cohort-specific outputs would include classified fraction, rank-specific assignment counts, Bray–Curtis, PERMANOVA R², PERMDISP and prespecified prevalence/rank summaries. Richness is conditional because read depth, read length and classified fraction can change the observed support. Cross-study synthesis would compare effect structures and robustness behavior, never pool assignments.

Current status: **plausible but not validated as a common sensitivity layer**. A technical benchmark must quantify length/preprocessing sensitivity before scientific use.

## Method B: fixed-length harmonization

A candidate target cannot be chosen merely because an installed redistribution exists. Candidate 50 nt is the only target with nonzero theoretical retention across all observed 15–50 and 15–75 distributions, but strongly mixed 75-nt files may retain fewer than half their reads at or above 50 nt. Target 75 nt would exclude every nominal 50-nt file and is therefore not a cohort-wide rule.

A prospective rule would discard reads shorter than the target and trim longer reads from a declared end to exactly the target. Pair synchronization and orphan handling must be explicit if pairing is established. The current public files expose one FASTQ per subject and pairing remains undeclared; this is not proof of native single-end architecture.

Required benchmark measures are read and base retention, classification-rate change, richness change, major-taxon count and proportion change, rank correlation and Bray–Curtis distance between native Kraken2 and trimmed Kraken2. Matching Bracken is permitted only on exact target-length trimmed reads with an installed redistribution. The proposed 80% read/base retention gate is an internal conservative governance rule, not a literature-validated biological threshold.

Current status: **not adoptable without benchmark evidence**.

## Method C: length-stratified Bracken

Bracken redistributes reads using a database file generated for one chosen length. The reviewed official documentation and methods literature do not provide a validated rule for dividing one sample by exact length, running separate redistributions and aggregating estimates by input reads, classified reads, bases or another weight. Small bins and missing redistribution lengths further change the estimand.

Current status: **NOT VALIDATED**. No aggregation formula will be implemented or benchmarked unless external validation is identified.

## Method D: switch the primary external cohort

Existing metadata do not identify a clearly superior immediate replacement:

- PRJCA039020/PRJDB36521 is operationally small and ordinary Illumina BALF, but CAP/severe-pneumonia individual mapping remains unresolved, reads are raw, and installed 40-nt Bracken redistribution is absent.
- PRJNA977832 has a large 917-GB footprint plus unresolved run/subject count and provenance discrepancies; it remains metadata-only.
- PRJCA027972 remains reserve because clinical-label validation and technical closure are incomplete.

Switching is justified only if an alternative independently closes clinical grouping, subject mapping, host provenance, read architecture and classifier compatibility. Technical difficulty alone is not a scientific selection rule.

Current status: **reserve; not presently superior**.
