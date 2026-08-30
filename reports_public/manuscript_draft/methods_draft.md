# Methods draft

## Study design

We performed a retrospective analysis of two public bronchoalveolar lavage fluid (BALF) shotgun metagenomic cohorts. Each cohort was treated as an independent analytical population with its own clinical estimand. No pooled 530-sample clinical matrix or common coefficient was constructed.

## Cohort selection

PRJNA1056765 served as the anchor because a deterministic mapping connected one available DNA shotgun run to each of 400 unique patients with published diagnostic and Training/Test labels. PRJCA046985 served as an external ecological cohort because one DNA run per 130 unique subjects could be mapped to independently documented tuberculosis drug-resistance status. Other candidates remained parked because they lacked an auditable accession-to-phenotype bridge, compatible specimen/modality, adequate contrast, or bounded acquisition justification. A third cohort was not required for the prespecified two-cohort ecological question.

## BALF shotgun data provenance and clinical grouping

The anchor included Bacterial infection (n=114), Fungal infection (n=78), Lung cancer (n=122) and Pulmonary tuberculosis (n=86). Its primary estimand was the omnibus association of published diagnosis with BALF species composition. The external cohort included Drug_Resistance (n=49) and Drug_Sensitive (n=81) TB subjects; its primary estimand was the resistance-status association with BALF species composition. Labels were frozen independently of the microbiome outcome. Demographics, recent antibiotics, treatment, severity and comorbidity variables were not available as a complete common run-linked adjustment set and were not imputed.

## Common Kraken2 classifier-assignment layer

All 400 anchor and 130 external runs had a valid native Kraken2 report under the verified common database, classifier parameters, report grammar and parser. The layer was used to standardize classifier assignments, not to assert identical upstream processing or read architecture. The two cohorts were parsed separately and retained separate matrices.

## Direct versus clade assignment distinction

Primary species features were Kraken2 reads assigned directly to a species-rank taxon. Kraken2 clade counts, which include descendants, were not substituted. Bracken redistributions were excluded from the common primary layer. Accordingly, direct-species composition is a classifier-defined subcomposition: it represents log-ratio organization among retained direct assignments, not the complete biological community or an absolute abundance assay.

## Cohort-specific prevalence filtering

Detection was defined as a positive species direct count. Within each cohort independently, the primary feature set retained species detected in at least 10% of samples, inclusive at the boundary. Prespecified sensitivity sets used 5% and 20%. All-zero taxa were removed; an all-zero sample after filtering caused a fail-stop. Thresholds were not chosen after viewing group results.

## Compositional analysis and CZM zero handling

For the primary analysis, zeros were replaced with `zCompositions::cmultRepl` version 1.6.2 using `label=0`, `method="CZM"`, `output="prop"`, `frac=0.65`, `threshold=0.5`, and `adjust=TRUE`. Runtime version and a synthetic conformance vector had to pass before biological execution. No approximation of CZM was permitted. As a fixed sensitivity, 0.5 direct read was added to every retained feature; this sensitivity could not replace a missing primary CZM analysis.

After zero replacement, every sample was closed to unit sum. We computed the centered log-ratio (CLR) as the natural logarithm of each component minus the within-sample mean log component. Euclidean distance between CLR vectors was the Aitchison distance.

## PERMANOVA and restricted permutations

For PRJNA1056765, the primary model tested the four-level published diagnosis with 9,999 deterministic permutations restricted within the frozen published Training/Test strata. For PRJCA046985, the primary model tested Drug_Resistance versus Drug_Sensitive status with 9,999 deterministic permutations. Pseudo-F, R², permutation P, feature count, group sizes and seed were reported. A collection-year anchor sensitivity or nominal 50/75-nt external sensitivity was admissible only if mapping was complete, groups were represented and the model remained full-rank; marginal rather than order-dependent claims were required.

## PERMDISP

Every PERMANOVA was paired with a 9,999-permutation PERMDISP test on the identical sample set and distance matrix. Distance-to-centroid summaries, statistic, effect and P value were retained. When group dispersion differed materially, the corresponding community result was described as location and/or dispersion structure rather than an unqualified centroid shift.

## Alpha-diversity metrics

Metrics were calculated from each sample's unfiltered direct-species counts. Richness was the number of species with a positive count. Shannon entropy was `-sum(p log p)`, Gini-Simpson diversity was `1-sum(p²)`, and dominance was the largest species proportion. The anchor used Kruskal-Wallis omnibus tests with epsilon-squared effects; the three frozen post-omnibus lung-cancer contrasts used two-sided Wilcoxon rank-sum tests with rank-biserial effects. The external cohort used the corresponding two-group Wilcoxon tests.

## Technical classified-fraction endpoint

Classified fraction was the number of reads classified by Kraken2 divided by total input reads in the valid report. It measured classifier yield under database and input provenance. **Classified fraction is not bacterial biomass** and was never presented as microbial load.

## Bray-Curtis sensitivity layer

Bray-Curtis was retained as a prespecified sensitivity because it answers a related but distinct representation question. Replayed cohort-specific tests used the same feature threshold and paired PERMANOVA/PERMDISP logic. The previously verified 999-permutation artifact was preserved; a 9,999-permutation replay could supplement it without overwriting provenance.

## Cross-cohort synthesis

Synthesis used contrast-labelled cohort-level estimates: PERMANOVA R², dispersion qualification, ecological endpoint effects, filter stability and prevalence-set overlap. Raw matrices, coefficients and P values were not pooled. Similar behavior was interpreted as qualified ecological generalizability under a common measurement grammar, not replication of a shared clinical effect.

## Multiplicity control

Holm adjustment controlled the complete 15-test anchor family (three prespecified contrasts by five endpoints) and the five external endpoint tests. Sensitivity cells were displayed in full rather than selected by significance. If separately authorized, exploratory taxon-level analyses would apply Benjamini-Hochberg correction separately by cohort, rank and test family.

## Differential-abundance exploratory status

Differential abundance was not part of the primary analysis. The prospectively preferred future method was cohort-specific ANCOM-BC2 with ALDEx2 sensitivity on the 10% species layer, with effect sizes, uncertainty and stability reporting. No DA computation was performed for this manuscript draft.

## Software and reproducibility

Production orchestration was implemented in the repository's `shotgun_analysis` package and `scripts/run_formal_cross_cohort_analysis.py`. Exact CZM was delegated to a fail-closed R adapter requiring zCompositions 1.6.2. Deterministic seeds, strict manifests, machine-readable JSON, compact TSVs, input hashes and method versions were retained. During preparation, only synthetic fake sample identifiers and synthetic count matrices were used.

## Statistical interpretation boundaries

Effect magnitude and robustness were interpreted before binary significance. All associations were observational. The study did not estimate causal effects, diagnostic accuracy, biomarkers, bacterial biomass or a universal disease signature. PRJCA046985 was not a replication or validation cohort for the PRJNA1056765 diagnosis estimand, and formal meta-analysis was not attempted.
