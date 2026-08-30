# Results skeleton — placeholders only

No paragraph below contains a formal biological result. Bracketed tokens must be populated only from schema-valid outputs.

## 1. Cohort construction and common classifier layer

**Narrative:** The frozen anchor comprised 400 unique patients (114 Bacterial infection, 78 Fungal infection, 122 Lung cancer and 86 Pulmonary tuberculosis), while the external cohort comprised 130 unique TB subjects (49 Drug_Resistance and 81 Drug_Sensitive). All [ANCHOR_VALID_REPORTS]/400 and [EXTERNAL_VALID_REPORTS]/130 reports met the common-layer validity contract. The cohorts remained separate analytical populations.

- Required statistic: exact patient/run/group counts, missingness and valid-report counts.
- Required display: Figure 1A–C; Table 1.
- Permitted interpretation: complete common classifier-assignment coverage for two distinct cohorts.
- Prohibited interpretation: one diagnosis cohort of 530, pooled clinical analysis, multicenter sampling.

## 2. Feature observability and taxonomic overlap

**Narrative:** The anchor and external report inventories contained 5,198 and 4,888 observed species and 1,633 and 1,496 genera. At the frozen 10% criterion, 166 species and 45 genera were observable in both cohorts. After cohort-specific primary filtering, [ANCHOR_RETAINED_SPECIES_10] and [EXTERNAL_RETAINED_SPECIES_10] species entered the separate compositional analyses; 5% and 20% counts were [ANCHOR_FEATURE_COUNTS_SENS] and [EXTERNAL_FEATURE_COUNTS_SENS].

- Required statistic: inventory, intersection/union/Jaccard, retained count at each threshold.
- Required display: Figure 1D; Supplementary Table feature-filter counts/common inventory.
- Permitted interpretation: shared observability under a common classifier grammar.
- Prohibited interpretation: equal biology, equal abundance or replicated differential taxa.

## 3. Anchor four-diagnosis community structure

**Narrative:** Under the prespecified 10%/CZM/CLR representation, published diagnosis accounted for [ANCHOR_AITCHISON_R2] of community variation (pseudo-F=[ANCHOR_PERMANOVA_F], permutation P=[ANCHOR_PERMANOVA_P]). Group dispersion was [ANCHOR_DISPERSION_DESCRIPTION] (PERMDISP F=[ANCHOR_PERMDISP_F], P=[ANCHOR_PERMDISP_P]), requiring the interpretation [ANCHOR_PRIMARY_BRANCH].

- Required statistic: R² with uncertainty/robustness, pseudo-F, P, seed, group n, PERMDISP statistic/P and centroid distances.
- Required display: Figure 2A–B; Table 2.
- Permitted interpretation: bounded cohort-specific diagnosis association, dispersion-qualified when applicable.
- Prohibited interpretation: causal diagnosis effect, diagnostic clusters, external confirmation.

## 4. Anchor secondary ecological organization

**Narrative:** Diagnosis-associated patterns in richness, Shannon diversity, Gini-Simpson diversity, dominance and classified fraction were [ANCHOR_SECONDARY_SUMMARY]. The three prespecified lung-cancer contrasts yielded [ANCHOR_CONTRAST_EFFECT_SUMMARY] after Holm control across 15 tests. Classified-fraction findings were treated as classifier-yield behavior.

- Required statistic: medians/IQR, omnibus H/P/epsilon-squared, pairwise U/rank-biserial/CI, raw and adjusted P.
- Required display: Figure 2C–D; Table 3.
- Permitted interpretation: complementary ecological or technical organization within the anchor.
- Prohibited interpretation: bacterial biomass, post hoc contrast discovery, biomarkers.

## 5. External DR/DS TB community structure

**Narrative:** In PRJCA046985, resistance status accounted for [EXTERNAL_AITCHISON_R2] of community variation (pseudo-F=[EXTERNAL_PERMANOVA_F], permutation P=[EXTERNAL_PERMANOVA_P]). Dispersion was [EXTERNAL_DISPERSION_DESCRIPTION] (PERMDISP F=[EXTERNAL_PERMDISP_F], P=[EXTERNAL_PERMDISP_P]), yielding [EXTERNAL_PRIMARY_BRANCH].

- Required statistic: binary R²/uncertainty, pseudo-F/P, seed, group n, PERMDISP and centroid distances.
- Required display: Figure 3A–B; Table 2.
- Permitted interpretation: resistance-status association within this TB cohort, if supported.
- Prohibited interpretation: replication or validation of the four-diagnosis anchor effect; resistance-caused dysbiosis.

## 6. External secondary ecological organization

**Narrative:** Drug_Resistance versus Drug_Sensitive differences in the five secondary endpoints were [EXTERNAL_SECONDARY_SUMMARY], with Holm-adjusted values [EXTERNAL_SECONDARY_ADJUSTED_SUMMARY]. Nominal read-length and classified-fraction checks indicated [EXTERNAL_TECHNICAL_SENSITIVITY_SUMMARY].

- Required statistic: endpoint medians/IQR, U, rank-biserial/CI, P/adjusted P; length-stratum representation/QC.
- Required display: Figure 3C–D; Table 3.
- Permitted interpretation: cohort-specific ecological and classifier-yield associations.
- Prohibited interpretation: absolute bacterial load or removal of all technical confounding.

## 7. Aitchison versus Bray-Curtis robustness

**Narrative:** Across the fixed representation grid, Aitchison and Bray-Curtis results were [ROBUSTNESS_CONCORDANCE], while 5%/10%/20% and CZM/0.5-pseudocount effects were [FILTER_ZERO_STABILITY]. Discordant cells were retained and interpreted as [REPRESENTATION_DEPENDENCE].

- Required statistic: all cell R², P, PERMDISP, feature counts and seeds.
- Required display: Figure 4A; Supplementary sensitivity and PERMDISP tables.
- Permitted interpretation: robustness or representation dependence of each cohort-specific ecological conclusion.
- Prohibited interpretation: choosing the favorable method or threshold.

## 8. Cross-cohort ecological synthesis

**Narrative:** Side-by-side cohort-specific effects showed [CROSS_COHORT_EFFECT_PATTERN], and secondary ecological summaries showed [CROSS_COHORT_ECOLOGICAL_PATTERN]. These findings indicate [QUALIFIED_GENERALIZABILITY_SENTENCE] under a common measurement grammar, while the distinct clinical contrasts prevented a shared coefficient or formal effect synthesis.

- Required statistic: contrast-labelled cohort estimates, dispersion status, standardized endpoint effects and descriptive overlap.
- Required display: Figure 4B–D; Tables 1–3.
- Permitted interpretation: qualified ecological generalizability and common observability.
- Prohibited interpretation: formal meta-analysis, clinical replication, universal disease signature.
