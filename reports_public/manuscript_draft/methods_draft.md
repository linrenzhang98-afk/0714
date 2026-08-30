# Methods draft

## Study design

We performed a retrospective, two-resolution analysis of two public bronchoalveolar lavage fluid (BALF) shotgun metagenomic cohorts. The anchor addressed between-diagnosis community structure, whereas the external cohort addressed within-TB drug-resistance structure. Each remained an independent analytical population; no pooled 530-sample clinical matrix or common coefficient was constructed.

## Cohort selection

PRJNA1056765 served as the anchor. The published source contained 402 mapped patients; repository availability records showed that SRR27343810 (Fungal infection) and SRR27343463 (Lung cancer) had `size_MB=0` and no available reads. The analytical population therefore comprised the 400 available DNA runs, each deterministically linked to one unique patient and published diagnostic and Training/Test labels. PRJCA046985 contributed one DNA run for each of 130 subjects with independently documented tuberculosis drug-resistance status. Other candidates remained parked because they lacked an auditable accession-to-phenotype bridge, compatible specimen or an adequate independent contrast.

## BALF shotgun data provenance and clinical grouping

The anchor included Bacterial infection (n=114), Fungal infection (n=78), Lung cancer (n=122) and Pulmonary tuberculosis (n=86). Its primary estimand was the omnibus association of published diagnosis with BALF species composition. The external cohort included Drug_Resistance (n=49) and Drug_Sensitive (n=81) TB subjects; its primary estimand was the resistance-status association with BALF species composition. Labels were frozen independently of the microbiome outcome. Demographics, recent antibiotics, treatment, severity and comorbidity variables were not available as a complete common run-linked adjustment set and were not imputed.

## Common Kraken2 classifier-assignment layer

All 400 anchor and 130 external runs had a valid native Kraken2 report under the verified common database, classifier parameters, report grammar and parser. The layer was used to standardize classifier assignments, not to assert identical upstream processing or read architecture. The two cohorts were parsed separately and retained separate matrices.

## Direct versus clade assignment distinction

Primary species features were Kraken2 reads assigned directly to a species-rank taxon. Kraken2 clade counts, which include descendants, were not substituted. Bracken redistributions were excluded from the common primary layer. Accordingly, direct-species composition is a classifier-defined subcomposition: it represents log-ratio organization among retained direct assignments, not the complete biological community or an absolute abundance assay.

## Cohort-specific prevalence filtering

Detection was defined as a positive species direct count. Within each cohort independently, the primary feature set retained species detected in at least 10% of samples, inclusive at the boundary. Prespecified sensitivity sets used 5% and 20%. All-zero taxa were removed; an all-zero sample after filtering caused a fail-stop. Thresholds were not chosen after viewing group results.

## Compositional analysis and CZM zero handling

For the primary analysis, zeros were replaced with `zCompositions::cmultRepl` version 1.6.2 using `label=0`, `method="CZM"`, `output="prop"`, `frac=0.65`, `threshold=0.5`, and `adjust=TRUE`. R 4.5.3, package versions, effective library paths and the resolved paths of zCompositions, NADA and truncnorm had to pass before biological execution. All three packages had to resolve inside the frozen isolated library at `/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3`, which had to be first in `.libPaths()`. No approximation of CZM was permitted. As a fixed sensitivity, 0.5 was added to every retained feature count, including nonzero counts, before closure and CLR. This additive sensitivity could not replace a missing primary CZM analysis.

After zero replacement, every sample was closed to unit sum. We computed the centered log-ratio (CLR) as the natural logarithm of each component minus the within-sample mean log component. Euclidean distance between CLR vectors was the Aitchison distance.

## PERMANOVA and restricted permutations

For PRJNA1056765, the primary model tested four-level published diagnosis with 9,999 deterministic label permutations restricted within the published Training/Test blocks. Every diagnosis required at least two observations per block. Blocking defined exchangeable labels but did not adjust for split or batch effects. For PRJCA046985, the primary model tested Drug_Resistance versus Drug_Sensitive status with 9,999 unrestricted deterministic permutations. Pseudo-F, point R², permutation P, feature count, group sizes and seed were reported.

The anchor collection-year sensitivity was defined as the marginal diagnosis term in `Aitchison distance ~ collection_year + diagnosis`, evaluated by reduced-model residual permutation within Training/Test blocks. The external read-length sensitivity was the marginal resistance-status term in `Aitchison distance ~ nominal_read_length + resistance_status`, also evaluated by reduced-model residual permutation. Either sensitivity was recorded as not run if its technical labels were incomplete, group representation was inadequate or the design was singular. Neither replaced the primary model.

## PERMDISP

Every PERMANOVA was paired with PERMDISP on the identical samples and distances. Observed distances were calculated from each sample to its group centroid. Their one-way ANOVA supplied the observed F statistic and eta-squared. For the permutation test, least-squares residuals from this fixed one-way model were permuted 9,999 times under the cohort-specific exchangeability restriction, the same design was refitted and F was recomputed. Group labels and centroids were not recalculated during permutations. The implementation was checked against a locked synthetic explicit-permutation reference derived from the Anderson/vegan centroid residual procedure; equivalence to a particular vegan run was not asserted without matching its permutation matrix. Material dispersion differences required location-and/or-dispersion wording.

## Alpha-diversity metrics

Metrics were calculated from each sample's unfiltered direct-species counts. Richness was the number of species with a positive count. Shannon entropy was `-sum(p log p)`, Gini-Simpson diversity was `1-sum(p²)`, and dominance was the largest species proportion. These were secondary endpoints. Richness is sequencing-effort sensitive, and classified fraction does not correct its dependence on direct-species assigned depth; all alpha-diversity findings were therefore interpreted with sample-level sequencing and classification QC. The anchor used Kruskal-Wallis omnibus tests with epsilon-squared effects. All 15 fixed lung-cancer contrasts were calculated, but confirmatory interpretation was endpoint-specific and required the corresponding omnibus Holm-adjusted P value to be at most 0.05. Rank-biserial signs represented Lung cancer minus the named infection group. External signs represented Drug_Resistance minus Drug_Sensitive.

## Technical classified-fraction endpoint

Classified fraction was the number of reads classified by Kraken2 divided by total input reads in the valid report. It measured classifier yield under database and input provenance. **Classified fraction is not bacterial biomass** and was never presented as microbial load.

## Bray-Curtis sensitivity layer

Bray-Curtis was one prespecified technical sensitivity per cohort. It used the 10%-prevalence direct-species features converted to sample-wise proportions, with no zero replacement, followed by 9,999-permutation PERMANOVA and residual-permutation PERMDISP. For this non-Euclidean comparator, negative signed squared point-to-centroid distances were set to zero and counted in the output. It was not crossed with other prevalence thresholds or zero methods. The earlier 999-permutation artifact remained separate provenance.

## Cross-cohort synthesis

Synthesis used contrast-labelled cohort estimates: PERMANOVA R², dispersion, secondary ecological effects, representation stability and prevalence-set overlap. Ecological generalizability required use of the same measurement without cohort-specific redesign, interpretable cohort-specific effects, transparent representation dependence and comparable observability and technical limits. It did not imply a common direction, coefficient, taxon set, signature or mechanism. Raw matrices, coefficients and P values were not pooled.

## Multiplicity control

Holm adjustment controlled the five anchor omnibus endpoint tests, the complete 15-test anchor contrast family and the five external endpoint tests as separate families. Sensitivity cells were displayed in full rather than selected by significance. If separately authorized, exploratory taxon-level analyses would apply Benjamini-Hochberg correction separately by cohort, rank and test family.

## Differential-abundance exploratory status

Differential abundance was not part of the primary analysis. The prospectively preferred future method was cohort-specific ANCOM-BC2 with ALDEx2 sensitivity on the 10% species layer, with effect sizes, uncertainty and stability reporting. No DA computation was performed for this manuscript draft.

## Software and reproducibility

Production orchestration was implemented in the repository's `shotgun_analysis` package and `scripts/run_formal_cross_cohort_analysis.py`. Exact CZM was delegated to a fail-closed R adapter requiring zCompositions 1.6.2 from the isolated library. Deterministic seeds, strict manifests, cross-field result validation, compact TSVs, input hashes and method versions were recorded. Aitchison ordination used deterministic PCA of sample-centred CLR coordinates. Zero burden and total-variation perturbation were descriptive QC and never exclusion criteria. Point effect estimates were reported without confidence intervals; no unvalidated bootstrap procedure was added. Preparation used synthetic identifiers and matrices only.

## Statistical interpretation boundaries

Effect magnitude and robustness were interpreted before binary significance. All associations were observational. The study did not estimate causal effects, diagnostic accuracy, biomarkers, bacterial biomass or a universal disease signature. PRJCA046985 was not a replication or validation cohort for the PRJNA1056765 diagnosis estimand, and formal meta-analysis was not attempted.
