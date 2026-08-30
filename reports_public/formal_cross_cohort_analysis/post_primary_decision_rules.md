# Prospective post-primary decision rules

Decisions use the whole prespecified evidence pattern, never `P < 0.05` alone and never a favorable threshold chosen after inspection.

## GO_TO_EXPLORATORY_DA

This branch requires all of the following: inputs and method provenance pass; the 10% CZM primary yields an effect magnitude that is reported as scientifically meaningful with an explicit rationale rather than a P-value threshold alone; there is no material dispersion qualification or that limitation is explicitly accepted; the effect is not confined to one prevalence/zero cell; the single 10% Bray-Curtis comparator is interpretable; and sequencing/classification QC does not provide a compelling technical account of the pattern. Terms such as “meaningful” and “material” must be justified from effect magnitude, centroid-distance distributions and complete sensitivity output, never used to choose a favorable cell. DA remains separately authorized, cohort-specific and exploratory.

## NO_DA_NEEDED

Use when primary effects are null/trivial or too imprecise, secondary ecology adds no coherent localization question, feature retention is unstable, or DA would only be a significance search. A complete null community analysis is a valid endpoint and does not need taxon mining.

## RESULTS_REQUIRE_REFRAMING

Use when a valid result is dominated by dispersion, strongly representation-dependent, materially linked to classified fraction or read provenance, stable only under a sensitivity filter, or heterogeneous in a way that defeats the intended biological wording. Preserve the analysis and reframe toward technical/ecological heterogeneity; do not switch thresholds, outcomes or contrasts.

## ANALYSIS_QC_FAILURE

Use for count/manifest mismatch, duplicate or missing sample, wrong frozen group counts, invalid reports, nonfinite/negative values, all-zero sample after filtering, no retained features, degenerate permutation design, failed CZM version/conformance, schema failure, non-reproducible seed behavior, or incomplete provenance. No biological interpretation or DA is permitted until the same frozen method passes bounded recovery.

The two cohorts may reach different branches. Their decisions are not combined, and a GO in one does not rescue or validate the other.
