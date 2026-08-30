# Reviewer risk notes

1. **CZM on microbiome zeros.** Reviewers may question treating zeros as rounded/sampling values. Show the 0.5 sensitivity, feature thresholds and exact package call; acknowledge that structural and sampling zeros cannot be distinguished.
2. **Subcomposition choice.** Direct Kraken2 species assignments exclude unclassified, higher-rank-only and nonretained components. State this prominently and keep classified fraction separate.
3. **PERMANOVA interpretation.** Always display R² and paired PERMDISP. With dispersion inequality, use location-and/or-dispersion wording.
4. **Restricted exchangeability.** Document the anchor Training/Test restriction and exact seeds. Do not imply restriction adjusts clinical confounding.
5. **Different clinical estimands.** The likely central objection is that diagnosis and TB resistance are not exchangeable. Make this a design feature: common measurement plus independent associations, with no pooled test.
6. **DA instability.** ANCOM-BC2/ALDEx2 can disagree; complete reporting and no favorable-method selection are essential. DA can be omitted if the primary result does not justify localization.
7. **Low-biomass contamination.** External negative controls are absent. This is especially limiting for rare or reagent-associated taxa and is a reason to lead with community results.
8. **Technical confounding.** Classifier fraction, upstream host processing and read architecture may correlate with groups. Sensitivity can diagnose but not fully correct missing batch variables.
9. **Original-study claims.** Source papers support cohort provenance, not equivalence of pipelines, replication of current effects, or adoption of their biomarker language.
10. **Novelty.** Do not oversell a new ecological method. The contribution is a prospectively frozen, common-measurement application with unusually explicit estimand and interpretation boundaries.
