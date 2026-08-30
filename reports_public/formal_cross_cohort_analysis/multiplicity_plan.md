# Prospective multiplicity plan

The two primary PERMANOVA tests answer different cohort-specific clinical questions. They are reported side by side, not combined and not treated as a two-study replication family. R², uncertainty/robustness and paired PERMDISP qualification lead interpretation; neither analysis is declared successful solely from `P < 0.05`.

For the anchor, the five secondary ecological endpoints first receive four-level omnibus tests. The only prespecified post-omnibus comparisons are Lung cancer versus each of Bacterial infection, Fungal infection and Pulmonary tuberculosis. Holm adjustment controls all 15 pairwise endpoint tests together. The omnibus tests are shown as a clearly labelled five-endpoint family; their unadjusted and Holm-adjusted values will both be retained in the compact table.

For the external cohort, Holm controls the five Drug_Resistance versus Drug_Sensitive secondary endpoint tests. No anchor and external P values are combined.

The 5%, 10% and 20% prevalence thresholds, CZM and 0.5-pseudocount representations, and Aitchison/Bray-Curtis representations are prespecified robustness cells. They are not searched and then filtered by P value. Concordance is judged from effect magnitude, sign where meaningful, dispersion status and feature stability.

If exploratory differential abundance is later authorized, Benjamini-Hochberg controls false discovery separately for every cohort, taxonomic rank and prespecified global/contrast family. ANCOM-BC2 is primary and ALDEx2 is a method sensitivity; taxa are not selected by the more favorable method. Holm remains the familywise method for the three anchor clinical contrasts.
