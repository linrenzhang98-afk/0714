# Prospective post-primary decision rules

Decisions use the whole prespecified evidence pattern, never `P < 0.05` alone and never a favorable threshold chosen after inspection.

## GO_TO_EXPLORATORY_DA

This branch requires all of the following: inputs and method provenance pass; the 10% CZM primary shows a nontrivial, reportable cohort-specific association or a coherent ecological pattern worth localizing; PERMDISP is absent or the location/dispersion limitation is explicitly acceptable; direction/magnitude is not an isolated 10% artifact across 5% and 20%; Aitchison versus Bray-Curtis behavior is scientifically interpretable; and classified fraction does not provide a compelling technical explanation for the entire pattern. DA remains separately authorized, cohort-specific and exploratory with ANCOM-BC2 plus ALDEx2 sensitivity.

## NO_DA_NEEDED

Use when primary effects are null/trivial or too imprecise, secondary ecology adds no coherent localization question, feature retention is unstable, or DA would only be a significance search. A complete null community analysis is a valid endpoint and does not need taxon mining.

## RESULTS_REQUIRE_REFRAMING

Use when a valid result is dominated by dispersion, strongly representation-dependent, materially linked to classified fraction or read provenance, stable only under a sensitivity filter, or heterogeneous in a way that defeats the intended biological wording. Preserve the analysis and reframe toward technical/ecological heterogeneity; do not switch thresholds, outcomes or contrasts.

## ANALYSIS_QC_FAILURE

Use for count/manifest mismatch, duplicate or missing sample, wrong frozen group counts, invalid reports, nonfinite/negative values, all-zero sample after filtering, no retained features, degenerate permutation design, failed CZM version/conformance, schema failure, non-reproducible seed behavior, or incomplete provenance. No biological interpretation or DA is permitted until the same frozen method passes bounded recovery.

The two cohorts may reach different branches. Their decisions are not combined, and a GO in one does not rescue or validate the other.
