# Figure blueprint

No fake biological plot should be drawn. Layout-only assets, if made, must carry a visible `MOCKUP — SYNTHETIC LAYOUT` watermark.

## Figure 1 — Study architecture and common measurement layer

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 1A | Frozen manifests; exclusion/validity audit; flow diagram | no quantitative axes; parallel cohort lanes | published 402 → frozen 400, naming the two zero-size excluded runs; external 130 | “Two zero-size anchor runs were excluded by the documented availability rule, leaving 400 anchor and 130 external reports for separate analyses.” | transparent frozen analytical populations | unexplained attrition or one pooled diagnosis cohort |
| 1B | Clinical group counts | x=group; y=subjects; cohort facets | n above bars | “Published diagnosis and TB resistance status define distinct cohort-specific contrasts.” | exact grouping | equivalent outcomes |
| 1C | provenance matrix: database/parser shared; upstream state/read architecture distinct | columns=measurement stages; rows=cohorts | verified/shared/different/unknown icons | “Common classifier definitions align assignment semantics but not all upstream processing.” | technical comparability within stated limits | identical pipelines or multicenter design |
| 1D | species/genus inventories and ≥10% intersections; descriptive classified-fraction inset | overlap sets; inset x=cohort, y=classified fraction | intersection/union/Jaccard; median/IQR only across cohorts | “Common observability comprised 166 species and 45 genera at ≥10% prevalence.” | shared observability | equal biology or bacterial biomass |

## Figure 2 — Anchor ecological analysis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 2A | 10%/CZM/CLR Aitchison ordination by deterministic PCA of sample-centred CLR coordinates | x=PCoA1 [%]; y=PCoA2 [%]; diagnosis color; split shape | n per group; no confidence ellipse or visual significance stars | “Ordination displays within-anchor Aitchison structure by published diagnosis.” | visualization of structure | diagnostic clusters |
| 2B | primary PERMANOVA and paired PERMDISP | x=test; y=point effect size; diagnosis omnibus | R², eta-squared, permutation P, 9,999 permutations; no CI | “Diagnosis-associated variance is reported together with dispersion.” | cohort-specific association | unqualified centroid shift if dispersion differs |
| 2C | richness, Shannon, Gini-Simpson, dominance, classified fraction | x=diagnosis; y=metric; small multiples | group summaries, epsilon-squared and omnibus Holm P; no CI | “Secondary endpoints describe complementary ecological and technical patterns.” | secondary ecology with sequencing/classification QC | classified fraction as biomass |
| 2D | three fixed lung-cancer contrasts | x=rank-biserial point effect; y=contrast×endpoint | Holm-adjusted P across all 15; endpoint-specific omnibus gate visibly marked; no CI | “All prespecified contrasts are shown; confirmatory interpretation is gated by the corresponding adjusted omnibus test.” | signed secondary contrasts | outcome-guided pairwise discovery |

## Figure 3 — External TB ecological analysis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 3A | external 10%/CZM/CLR Aitchison ordination by deterministic PCA | x=PCoA1 [%]; y=PCoA2 [%]; resistance color; length shape | group n; no confidence ellipse | “Ordination displays external-cohort structure by resistance status.” | cohort-specific visualization | anchor replication |
| 3B | external PERMANOVA and PERMDISP | x=test; y=point effect | R², eta-squared and permutation P, 9,999 permutations; no CI | “Resistance-status variance is reported together with dispersion.” | within-TB cohort association | resistance-caused dysbiosis |
| 3C | five secondary endpoints | x=resistance group; y=metric | rank-biserial point effect (Drug_Resistance minus Drug_Sensitive) and Holm-adjusted P; no CI | “Secondary ecological and classifier-yield effects are reported as one five-endpoint family.” | secondary effects with fixed direction | biomarkers or bacterial load |
| 3D | nominal 50/75-nt sensitivity and classified fraction | x=technical stratum; y=effect/classified fraction; resistance grouping | marginal/stratified effect and representation counts | “Technical provenance is evaluated without claiming complete batch adjustment.” | technical sensitivity | all confounding removed |

## Figure 4 — Qualified cross-cohort ecological synthesis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 4A | six Aitchison cells (5/10/20% × CZM/additive 0.5) plus one 10% Bray-Curtis comparator, separately by cohort | x=R²; y=explicit cohort/contrast; shape=representation; facet=threshold | point effects and PERMDISP status; no CI | “Every prespecified representation is displayed without selecting cells by outcome.” | stability or transparent representation dependence | a full prevalence-by-zero-method Bray grid or favorable-cell selection |
| 4B | primary cohort estimates | x=R²; y=explicit, non-equivalent estimand | point estimate, permutation P secondary, dispersion badge; no CI | “Between-diagnosis and within-TB estimates are juxtaposed but not pooled.” | two-resolution comparison | shared coefficient or meta-analysis |
| 4C | secondary endpoint point effects | x=effect; y=endpoint; facet=cohort/contrast | point effect and adjusted P; no CI; explicit sign convention | “Secondary effects retain their clinical contrast labels.” | separate cohort-specific patterns | clinical replication |
| 4D | prevalence overlap at 5/10/20% | x=threshold; y=intersection/union/Jaccard | descriptive estimates only | “Taxonomic overlap quantifies common observability.” | common measurement behavior | replicated disease taxa |

## Supplementary figures

- S1: complete sample-level QC distributions and missingness/provenance.
- S2: full Aitchison ordinations across 5/10/20% and both zero methods.
- S3: the single 10%-prevalence Bray-Curtis comparator per cohort with paired PERMDISP.
- S4: group distances to centroid for every primary/sensitivity cell.
- S5: feature-retention stability and overlap across thresholds.
- S6: anchor Training/Test and collection-year sensitivity, only if design gates pass.
- S7: external nominal-length sensitivity, only if representation/rank gates pass.
