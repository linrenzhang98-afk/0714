# Interpretation rules

| Observed pattern | Permitted language | Prohibited language |
|---|---|---|
| Material PERMANOVA effect; no material dispersion inequality | “Clinical grouping was associated with cohort-specific Aitchison community location” with point R², permutation P and full sensitivity context | causal effect, diagnostic separation, biomarker |
| PERMANOVA with material PERMDISP evidence | “Community structure differed in location and/or dispersion”; `DISPERSION_QUALIFIED` | clean centroid shift or disease-specific composition |
| Small but statistically precise effect | “A small bounded association” | strong biological separation |
| Null or imprecise primary result | “No clear association was resolved under the prespecified representation” | equivalence, absence of biology, pipeline failure |
| Aitchison/Bray agreement | representation robustness for the cohort-specific ecological conclusion | validation of a shared disease signature |
| Aitchison/Bray disagreement | representation dependence requiring explanation | selecting the favorable metric |
| Shared prevalent features | common taxonomic observability under the classifier definition | replicated differential taxa |
| Similar cohort-level ecology | qualified ecological generalizability | formal meta-analysis, independent confirmation |

Here, ecological generalizability is operational rather than a shared biological effect: the same classifier-defined measurement is applied without cohort-specific redesign; each cohort yields contrast-labelled effect and dispersion estimates; representation dependence is shown rather than selected away; observability and technical limits are compared; and no common direction, coefficient, taxa, signature or mechanism is inferred. The design has two resolutions—between-diagnosis ecology in the anchor and within-TB resistance ecology in the external cohort.

Anchor pairwise contrasts are always calculated as one fixed 15-test family, but confirmatory interpretation is endpoint-specific and requires the corresponding five-endpoint-Holm-adjusted omnibus P to be at most 0.05. Otherwise they are descriptive. Rank-biserial signs are fixed as Lung cancer minus the named infection group; the external sign is Drug_Resistance minus Drug_Sensitive.

Richness is sequencing-effort sensitive. Classified fraction neither corrects direct-species depth nor measures biomass, so alpha-diversity is secondary and must be read with sequencing/classification QC.

Classified fraction is a classifier-yield technical endpoint and is not bacterial biomass. Direct-species composition is a classifier-defined subcomposition. The cohorts stay analytically separate; PRJCA046985 is neither replication nor validation of the anchor diagnosis effect. All conclusions are observational associations.
