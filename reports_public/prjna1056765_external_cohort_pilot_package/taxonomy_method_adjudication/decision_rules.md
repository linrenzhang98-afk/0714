# Prospective decision rules

These rules are frozen before benchmark execution. They govern technical method selection, not biological validity.

## Universal stops

- Selected input absent, checksum mismatch or FASTQ failure.
- Any accession substitution.
- Database/version/parameter mismatch.
- Host processing, database modification or environment modification becomes necessary.
- More than 0 new raw bytes are needed for the frozen four-run design.
- Resource cap exceeded.
- Clinical grouping enters sample selection or technical interpretation.

## Method A: Kraken2-only common layer

Eligible for `GO` only if the fixed-50 identity control reproduces exactly; all four native and trimmed runs classify successfully; classified-fraction and rank-support changes are reported rather than hidden; and DeepSeek judges the observed Native–Trim50 sensitivity compatible with a bounded classifier-assignment estimand. No universal numeric equivalence threshold is asserted from literature.

At the project-governance level, any run with Native–Trim50 Bray–Curtis above 0.10, Spearman below 0.90, or a greater than 20% relative change in any major-taxon proportion triggers `CONDITIONAL` review rather than automatic failure. These are conservative decision flags, not validated biological standards. Before cross-cohort use, a matched PRJNA1056765 Kraken2-only sensitivity layer must be separately frozen and generated with identical parameters.

## Method B: fixed-length harmonization

Eligible for further pilot consideration only if every sample retains at least 80% of reads and bases, the identity control is exact, and retention/classifier distortion is not architecture-dependent. The 80% threshold is explicitly an internal governance floor. Failure by the strongly mixed sample establishes that one universal 50-nt pipeline would alter the sample population or information content and therefore makes cohort-wide harmonization `INVALID` under this rule.

## Method C: length-stratified Bracken

`INVALID` unless a peer-reviewed or official validated aggregation method is identified before execution. The benchmark cannot rescue an undefined aggregation estimand.

## Method D: switch cohort

`RECOMMENDED` only if Methods A and B are invalid or scientifically uninformative and an already screened cohort independently closes clinical labels, run–subject mapping, host provenance, read architecture and feasible classifier compatibility. No switch is permitted merely because another cohort is smaller.

## Gate outcomes

- `GO`: method and interpretation are executable without changing the scientific question.
- `CONDITIONAL_GO`: bounded benchmark/pilot is allowed under explicit unresolved conditions.
- `INSUFFICIENT_EVIDENCE`: state the single smallest experiment capable of changing the choice.
- `NO_GO`: stop the branch; do not weaken the rules.
