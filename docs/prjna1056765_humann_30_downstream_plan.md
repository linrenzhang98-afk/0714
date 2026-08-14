# Fixed-30 HUMAnN downstream analysis plan

## Scope and gate

The cohort authority is the exactly 30 unique `run` values and unchanged
`pathogen_group` labels in
`reports_public/metagenome_functional_profile/run_status.tsv`. Input HUMAnN files
are immutable. Downstream execution starts only if all 90 expected files exist,
have a tabular HUMAnN header, contain at least one data row, and contain only
finite non-negative numeric values with consistent columns and unique features.
Sub-kilobyte files are flagged for review. Thus a header-only pathway file is a
hard failure, not a valid zero-filled profile.

Run the read-only gate as follows (replace the root only; never copy results into
the repository merely to satisfy the gate):

```bash
python3 scripts/audit_humann_30_outputs.py \
  --input-root /REAL/PATH/20260809T000000Z-prjna1056765-functional-profile \
  --output-dir reports_public/metagenome_humann_30_downstream/audit
```

## Reproducible analysis after the gate passes

1. Record the 90 SHA-256 checksums, absolute input root, cohort table, software
   versions, command line, UTC timestamps, and parameters. Join each output type
   by exact feature identifier and exact 30-sample membership; fill feature
   absence with zero. Do not use recursively discovered merged outputs as input.
2. Split rows containing `|` (taxon-stratified) from rows without `|`
   (unstratified). Retain `UNMAPPED`/`UNINTEGRATED` in QC, but exclude them from
   biological feature testing and ordination.
3. Gene families: convert copies-per-million profiles to relative abundance
   within sample (or use HUMAnN `relab` equivalently), then analyse unstratified
   UniRef90 features. Path abundance: total-sum scale unstratified pathways.
   Path coverage is already bounded evidence of pathway completeness and must
   not be compositional-renormalized.
4. Filtering is declared before tests: retain features present (`>0`) in at
   least 20% (6/30) of samples for ordination/exploration. Report sensitivity at
   10% and 30%. Do not filter the archived joined tables.
5. Sample QC: totals, detected features, zero fraction, mapped/unmapped share,
   stratified/unstratified totals, pathway abundance/coverage counts, and
   outliers by robust median absolute deviation. Feature QC: prevalence, mean,
   median, maximum, variance, zero fraction, taxonomic contributor count.
6. Use Bray-Curtis on filtered unstratified relative abundance for PCoA and
   hierarchical clustering (average linkage). Use CLR only as a sensitivity
   analysis with a documented multiplicative pseudocount. Plot labels always
   retain run and pathogen group.
7. Group exploration is restricted to groups with at least three samples:
   descriptive group summaries, omnibus permutation test where exchangeability
   is defensible, and per-feature Kruskal-Wallis tests with Benjamini-Hochberg
   FDR. Report effect sizes and raw distributions; do not call discoveries from
   FDR alone in this selected cohort.
8. Pathogen-function association uses the existing fixed pathogen groups and
   checked-in species fractions. Analyse Spearman abundance correlations and
   group enrichment, with BH correction separately by feature family. Treat
   correlations as compositional and selection-sensitive; they are hypotheses,
   not evidence of mechanism.
9. Export joined/raw, stratified/unstratified, normalized, filtered, QC,
   statistics, coordinates, distances, cluster assignments, plot source tables,
   SVG figures, machine-readable JSON summary, Markdown narrative,
   environment versions, commands, and checksums under one timestamped output.

## Interpretation boundary

These 30 samples are selectively chosen deep-review cases, not a random or
representative sample of the approximately 400-run parent collection. All
functional distributions, pathogen-group contrasts, ordination structure,
clusters, p-values, FDR values, and pathogen-function associations are strictly
exploratory within these 30. They cannot estimate population prevalence,
generalize effect sizes, validate biomarkers/classifiers, or support claims
about the full cohort. Confirmation requires a prespecified analysis of the
full eligible cohort or an independent validation set and is outside this plan.
