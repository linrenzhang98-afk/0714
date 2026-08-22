# Taxonomy method selection

State: **METHOD_SELECTED**

Review date: 2026-08-22

## Selected method

The selected next method is a **Kraken2-only common sensitivity estimand** based on native reads. It is valid only as a separately named classifier-assignment layer, with identical frozen Kraken2 version, database identity, parameters, taxonomic reporting rules and normalization in both cohorts. Each cohort must be analyzed independently before cross-study synthesis. Outputs must not be pooled, represented as Bracken abundance or used to overwrite the frozen PRJNA1056765 v5 primary anchor.

## Post-benchmark gate

- Overall verdict: `GO`
- Kraken2-only: `VALID`
- Fixed-length harmonization: `INVALID`
- Length-stratified Bracken: `INVALID`
- Switch cohort: `NOT_RECOMMENDED`
- Preferred next method: `Kraken2-only common sensitivity estimand`

DeepSeek explicitly accepted native-read Kraken2 classifier assignments as the separate cross-cohort sensitivity estimand under the frozen comparability conditions. It also determined that no additional raw-read characterization is needed merely to establish variable-length cohort relevance.

## Benchmark closure

The frozen four-sample benchmark used `CRR2423957`, `CRR2424000`, `CRR2423921` and `CRR2424010` with zero new downloaded bytes.

- The strictly fixed-50 identity control reproduced exactly.
- The near-modal-50 sample was stable after Trim50.
- The near-modal-75 sample showed strong Trim50 distortion: species-level Spearman 0.448, Bray–Curtis 0.594 and classified fraction falling from 0.0974 to 0.0286.
- The strongly mixed sample retained only 27.17% of reads and 47.51% of input bases, failing the prospective 80% harmonization floor before its Trim50 Bracken command returned 1.
- All native and Trim50 Kraken2 commands completed. The final Bracken failure leaves that estimator contrast incomplete but cannot rescue fixed-length harmonization and does not invalidate the native Kraken2 estimand.

No biological interpretation was made. No pilot or bulk production was started from this gate.

## Rejected methods

Universal fixed-length harmonization is rejected because distortion depends on read architecture and the strongly mixed sample fails retention rules. Length-stratified Bracken remains not validated because no externally defensible aggregation method was identified. Native mixed-length reads must not be supplied to Bracken using a summary read length. Switching cohorts is not recommended because the screened alternatives do not close the existing mapping, provenance, compatibility and compute constraints.

## Exact next action

Prospectively freeze the parameter-identical PRJNA1056765 Kraken2-only sensitivity-layer specification and verify whether existing anchor Kraken2 reports prove the required database and parameter identity before any bounded 4–8 sample pilot is designed.
