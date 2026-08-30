# Prospective multiplicity plan

The two primary PERMANOVA tests answer different cohort-specific clinical questions. They are reported side by side, not combined and not treated as a two-study replication family. Point R², the complete robustness set and paired PERMDISP lead interpretation; neither analysis is declared successful solely from `P < 0.05`.

For the anchor, the five secondary endpoints first receive four-level omnibus tests, with Holm adjustment across those five tests. All 15 prespecified pairwise tests (three Lung-cancer contrasts by five endpoints) are calculated and Holm-adjusted together so the output is complete and reproducible. Their confirmatory interpretation gate is endpoint-specific: a pairwise result may be promoted as confirmatory only when the corresponding omnibus Holm-adjusted P value is at most 0.05. Otherwise it is labelled descriptive regardless of its pairwise P value. This rule is frozen before biological results and prevents selective execution or promotion.

For the external cohort, Holm controls the five Drug_Resistance versus Drug_Sensitive secondary endpoint tests. No anchor and external P values are combined.

The Aitchison grid contains CZM and additive-0.5-to-all-features representations at 5%, 10% and 20%. Bray-Curtis is a single 10% sensitivity on sample-wise proportions with no zero replacement. Cells are never selected by P value. Concordance is judged from effect magnitude, sign where meaningful, dispersion status and feature stability.

If exploratory differential abundance is later authorized, Benjamini-Hochberg controls false discovery separately for every cohort, taxonomic rank and prespecified global/contrast family. ANCOM-BC2 is primary and ALDEx2 is a method sensitivity; taxa are not selected by the more favorable method. Holm remains the familywise method for the three anchor clinical contrasts.
