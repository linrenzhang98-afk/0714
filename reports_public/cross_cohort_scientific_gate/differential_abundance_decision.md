# Differential-abundance decision

## Role: EXPLORATORY

Differential abundance is not the primary manuscript result. The primary evidence should be bounded community-level association and dispersion, followed by prespecified alpha-diversity and dominance summaries. Species-level testing faces sparse direct assignments, thousands of features, zero handling, low classifier yield, no identical cross-cohort contrast and incomplete clinical/batch covariates. PRJCA046985 also has no identified public negative-control run.

## Principal and sensitivity methods

- **Principal method: ANCOM-BC2**, run independently within each cohort on species direct counts after the prospectively frozen at-least-10% within-cohort prevalence filter. In the anchor, use the global four-group test first; perform pairwise contrasts only for a taxon passing the global family and label all pairwise results. In the external cohort, estimate the `Drug_Resistance` versus `Drug_Sensitive` coefficient. Include nominal read-length category only in a prespecified external sensitivity model.
- **Sensitivity method: ALDEx2**, using its Monte Carlo CLR framework on the same samples and prevalence-filtered feature set. Use a four-group global test for the anchor and the binary contrast for the external cohort.

Report signed effect sizes, uncertainty and Benjamini-Hochberg adjusted P values. Control false discovery separately by cohort, taxonomic rank and prespecified test family. Do not screen thresholds or methods based on significance. Taxa with unstable sign, large method dependence, very low counts, or plausible reagent/environmental provenance remain unconfirmed observations.

## Cross-cohort boundary

No taxon can be called replicated merely because it is significant in both cohorts: the clinical contrasts differ. For the 166 species prevalent in both cohorts, side-by-side signs or ranks are exploratory ecological concordance only. No pooled count table, combined P value or meta-analytic species effect is valid without a genuinely shared estimand.

If formal-analysis authorization does not include an adequately frozen DA plan, omit DA rather than promote an under-specified result.
