# Figure blueprint

No fake biological plot should be drawn. Layout-only assets, if made, must carry a visible `MOCKUP — SYNTHETIC LAYOUT` watermark.

## Figure 1 — Study architecture and common measurement layer

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 1A | Frozen manifests; exclusion/validity audit; flow diagram | no quantitative axes; parallel cohort lanes | counts only | “Two independently assembled BALF cohorts contributed 400 and 130 valid reports to separate analyses.” | complete frozen analytical populations | one pooled diagnosis cohort |
| 1B | Clinical group counts | x=group; y=subjects; cohort facets | n above bars | “Published diagnosis and TB resistance status define distinct cohort-specific contrasts.” | exact grouping | equivalent outcomes |
| 1C | provenance matrix: database/parser shared; upstream state/read architecture distinct | columns=measurement stages; rows=cohorts | verified/shared/different/unknown icons | “The common classifier grammar aligns assignment semantics but not all upstream processing.” | bounded technical comparability | identical pipelines or multicenter design |
| 1D | species/genus inventories and ≥10% intersections; descriptive classified-fraction inset | overlap sets; inset x=cohort, y=classified fraction | intersection/union/Jaccard; median/IQR only across cohorts | “Common observability comprised 166 species and 45 genera at ≥10% prevalence.” | shared observability | equal biology or bacterial biomass |

## Figure 2 — Anchor ecological analysis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 2A | 10%/CZM/CLR Aitchison ordination | x=PCoA1 [%]; y=PCoA2 [%]; diagnosis color; split shape | n per group; no visual significance stars | “Ordination shows within-anchor Aitchison organization by published diagnosis.” | visualization of structure | diagnostic clusters |
| 2B | primary PERMANOVA and paired PERMDISP | x=test; y=effect size; diagnosis omnibus | R²/CI, P, PERMDISP P, 9,999 permutations | “Diagnosis-associated variance is reported with its dispersion qualification.” | bounded association | unqualified centroid shift if dispersion differs |
| 2C | richness, Shannon, Gini-Simpson, dominance, classified fraction | x=diagnosis; y=metric; small multiples | epsilon-squared/CI, omnibus adjusted P | “Secondary endpoints describe complementary ecological and technical organization.” | secondary ecology | classified fraction as biomass |
| 2D | three frozen lung-cancer contrasts | x=rank-biserial effect; y=contrast×endpoint | CI and Holm-adjusted P; show all 15 | “Only prespecified post-omnibus contrasts are displayed.” | secondary contrasts | outcome-guided pairwise discovery |

## Figure 3 — External TB ecological analysis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 3A | external 10%/CZM/CLR Aitchison ordination | x=PCoA1 [%]; y=PCoA2 [%]; resistance color; length shape | group n | “Ordination shows external-cohort organization by resistance status.” | cohort-specific visualization | anchor replication |
| 3B | external PERMANOVA and PERMDISP | x=test; y=effect | R²/CI, P, PERMDISP P, 9,999 permutations | “Resistance-status variance is paired with dispersion assessment.” | TB cohort association | resistance-caused dysbiosis |
| 3C | five secondary endpoints | x=resistance group; y=metric | rank-biserial/CI and Holm-adjusted P | “Secondary ecological and classifier-yield effects are reported as one five-endpoint family.” | bounded secondary effects | biomarkers or bacterial load |
| 3D | nominal 50/75-nt sensitivity and classified fraction | x=technical stratum; y=effect/classified fraction; resistance grouping | marginal/stratified effect and representation counts | “Technical provenance is evaluated without claiming complete batch adjustment.” | technical sensitivity | all confounding removed |

## Figure 4 — Qualified cross-cohort ecological synthesis

| Panel | Input and analysis | Axes/grouping | Statistical annotation/effect | Caption sentence | Permitted claim | Prohibited claim |
|---|---|---|---|---|---|---|
| 4A | all 5/10/20%, CZM/0.5, Aitchison/Bray cells | x=R²; y=explicit cohort/contrast; shape=representation; facet=threshold | CI/robustness, PERMDISP qualification | “The full prespecified grid displays effect stability and dispersion without cell selection.” | robustness/representation dependence | choose favorable cell |
| 4B | primary cohort estimates | x=R²; y=cohort-specific estimand | CI, P secondary, dispersion badge | “Different estimands are juxtaposed but not pooled.” | cohort-level comparison | shared coefficient or meta-analysis |
| 4C | standardized alpha/dominance effects | x=effect; y=endpoint; facet=cohort/contrast | CI and adjusted P | “Ecological effects retain their contrast labels.” | qualified ecological patterns | clinical replication |
| 4D | prevalence overlap at 5/10/20% | x=threshold; y=intersection/union/Jaccard | descriptive estimates only | “Taxonomic overlap quantifies common observability.” | common measurement behavior | replicated disease taxa |

## Supplementary figures

- S1: complete sample-level QC distributions and missingness/provenance.
- S2: full Aitchison ordinations across 5/10/20% and both zero methods.
- S3: full Bray-Curtis comparator with paired PERMDISP.
- S4: group distances to centroid for every primary/sensitivity cell.
- S5: feature-retention stability and overlap across thresholds.
- S6: anchor Training/Test and collection-year sensitivity, only if design gates pass.
- S7: external nominal-length sensitivity, only if representation/rank gates pass.
