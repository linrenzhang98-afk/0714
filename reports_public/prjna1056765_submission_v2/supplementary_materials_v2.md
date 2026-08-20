# Supplementary materials

## Supplementary Methods

### Reproducibility record

The analysis plan, 18-cell design, executable, anchor-species order, input hashes, random seeds, and interpretation rules were version-locked before statistical computation. The first locked record was commit `cb2e971`. A pre-statistics safeguard detected nondeterministic ordering among equal-prevalence species; the executable stopped before calculating any cell. Commit `7a1190d` imposed deterministic ordering without changing feature membership, thresholds, pseudocounts, distances, permutation counts, seeds, endpoints, or interpretation. The frozen results were recorded in commit `a4db55d`. The post-computation manuscript framing record is commit `dbb4862`. Exact SHA-256 values are retained in `manifest.json`, the complete v5 table, and repository history.

### Frozen grid interpretation

The grid has three non-poolable layers. P1 versus P2 within a fixed feature set evaluates zero-replacement sensitivity. The 5%, 10%, and 20% prevalence spaces evaluate feature-space dependence. Bray–Curtis is a metric and dispersion comparator. Repeating these cells in the n=119 pipeline-dependent sensitivity population changes the population and estimand; it is not validation or replication. No majority vote or result-based cell selection was used.

### Original-to-current pipeline provenance

The published and current workflows share broad preprocessing and Kraken2/Bracken tool families. Exact database builds, operational negative-control handling, some sample filters, and feature definitions remain unresolved. The complete itemized audit is Supplementary Table S3. Taxon overlap or mismatch is consequently described as pipeline/statistical concordance or discrepancy.

## Supplementary Figure legend

### Supplementary Figure S1. Bray–Curtis and dispersion comparator

PERMANOVA R² for the three prevalence-defined Bray–Curtis cells in the primary n=400 population and the pipeline-dependent sensitivity n=119 population. Daggers denote PERMDISP P<0.05. All full-cohort cells are dispersion-qualified; the 5% n=119 cell is unqualified, whereas its 10% and 20% cells are qualified. The panels use a common scale but represent different estimands.

## Supplementary tables

- **Table S1. Complete frozen v5 sensitivity grid.** All 18 prespecified cells, including population, feature space, metric, pseudocount, PERMANOVA, PERMDISP, seeds, and hashes.
- **Table S2. QC population and fields.** Sample-level frozen QC fields, flags, and membership in the pipeline-dependent sensitivity population.
- **Table S3. Original-versus-current pipeline difference matrix.** Itemized upstream, statistical, robustness, and unresolved differences.
- **Table S4. Frozen primary PERMANOVA and PERMDISP outputs.** Earlier checked-in community tests retained for provenance.
- **Table S5. Frozen species associations.** Earlier species-level results retained for audit transparency; no new taxon analysis was performed.
- **Table S6. Clustering diagnostics.** Silhouette and adjusted Rand index for k=2–10 in the frozen Bray–Curtis and Aitchison representations.

## Figure source data

Each figure has a tab-separated source-data file. Figure 1 records cohort and diagnosis counts. Figure 2 and Supplementary Figure S1 retain the complete relevant rows from the frozen v5 grid rather than plotted-value extracts. Figure 3 contains the complete frozen clustering diagnostics. `figure_source_manifest.tsv` records SHA-256 hashes and file sizes.

## Claim boundaries

The primary result is a very small conditional diagnosis-associated variance component in the 30-species full-cohort Aitchison analysis. The exact replay applies only to that frozen anchor. Feature-space, metric, dispersion, and population dependence are integral results. The analysis does not establish a diagnostic signature, biomarker, causal mechanism, disease-specific taxon discovery, or cross-cohort replication.
