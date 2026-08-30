# Prospective formal cross-cohort analysis plan

## Status and immutable boundary

This plan is frozen during workstation downtime. It prepares, but does not execute, biological analysis. `BIOLOGICAL_ANALYSIS_EXECUTED=false`. The previously queued isolated installation of zCompositions 1.6.2 has unknown status and is neither assumed complete nor changed here. No ETYY connection or job was used.

The analytical universe contains two separate cohorts: PRJNA1056765 (400 unique BALF patients) and PRJCA046985 (130 unique BALF subjects). The former estimates a four-level published-diagnosis association; the latter estimates a Drug_Resistance versus Drug_Sensitive TB association. They are not one clinical estimand. Matrices will never be pooled, and coefficients or P values will not be combined.

## Frozen cohort contracts

The anchor must contain exactly 114 Bacterial infection, 78 Fungal infection, 122 Lung cancer and 86 Pulmonary tuberculosis patients. Runs and sample identifiers must be unique; all 400 sample IDs must align exactly across the clinical manifest, direct-species matrix and report QC. Permutations must remain within the frozen published Training/Test strata. Collection year is a prespecified technical sensitivity only when complete and full-rank.

The external cohort must contain exactly 49 Drug_Resistance and 81 Drug_Sensitive subjects, again with unique and exactly aligned identifiers. Nominal 50/75-nt category is a technical sensitivity only after verifying that both groups are represented in both categories.

Any mismatch, duplicate, nonfinite value, negative/noninteger count, all-zero sample, missing report, wrong group count or degenerate design is an `ANALYSIS_QC_FAILURE`. Partial outputs must not be promoted.

## Input definition

Only Kraken2 species-rank direct-assigned counts from the verified common classifier-assignment handoff are allowed. Clade counts and Bracken estimates are prohibited. Alpha metrics use the complete direct-species count vector before prevalence filtering. Classified fraction is `classified_reads / total_input_reads` from the paired Kraken2 report QC and is a technical endpoint, not bacterial biomass.

Direct-species composition is a classifier-defined subcomposition. It describes relative organization among classifier-assigned species and cannot estimate absolute microbial load.

## Primary compositional analysis

For each cohort independently:

1. Compute detection as direct count greater than zero.
2. Retain a feature when its within-cohort prevalence is at least 10%, inclusive at the boundary. Remove every all-zero taxon.
3. Apply the exact `zCompositions::cmultRepl` implementation from zCompositions 1.6.2 with `label=0`, `method="CZM"`, `output="prop"`, `frac=0.65`, `threshold=0.5`, and `adjust=TRUE`.
4. Fail closed if the exact version or dependencies cannot be verified. No local approximation is permitted.
5. Close every positive replaced vector to sum one, take its centered log-ratio, and calculate Euclidean distance in CLR space (Aitchison distance).
6. Run cohort-specific PERMANOVA with 9,999 permutations and paired PERMDISP with 9,999 permutations on the identical samples and distance matrix.

The deterministic primary seed registry is: anchor PERMANOVA `105676510`, anchor PERMDISP `105676511`, external PERMANOVA `46985010`, and external PERMDISP `46985011`. Non-primary CZM filter cells add prevalence multiplied by 10,000; pseudocount cells add `100000` plus prevalence multiplied by 10,000. Seeds are recorded in every result.

## Prespecified sensitivities

Repeat the complete cohort-specific analysis at prevalence thresholds 5% and 20%. Repeat the 5%, 10% and 20% grid after adding exactly 0.5 direct read to every retained feature instead of CZM. Pseudocount results are sensitivities and may never replace a missing CZM primary. Threshold or zero method will not be selected from observed results.

Retain Bray-Curtis as a sensitivity representation and pair every replayed PERMANOVA with PERMDISP. The existing verified 999-permutation Bray-Curtis artifact is preserved; a later 9,999-permutation replay may supplement but not overwrite it.

## Primary tests and secondary endpoints

The anchor primary test is the four-level diagnosis omnibus. The external primary test is the binary resistance-status association. Report pseudo-F, R², permutation P, group sizes, seed, feature count and dispersion result; effect magnitude and uncertainty/robustness take precedence over a binary significance label.

Secondary endpoints are richness, Shannon entropy, Gini-Simpson diversity, dominance and classified fraction. The anchor uses a Kruskal-Wallis omnibus with epsilon-squared. The three frozen secondary, post-omnibus contrasts are Lung cancer versus Bacterial infection, Fungal infection and Pulmonary tuberculosis, tested with two-sided Wilcoxon/Mann-Whitney tests and rank-biserial effects. No additional outcome-guided contrast is promoted. The external cohort uses two-sided Wilcoxon/Mann-Whitney tests with rank-biserial effects.

## Multiplicity and serialization

Primary PERMANOVA questions are reported as two distinct cohort-specific estimands, not a pooled family. Holm adjustment controls the 15 anchor secondary contrast tests (three contrasts by five endpoints) and the five external secondary endpoint tests. Benjamini-Hochberg is reserved for later, separately authorized taxon-level exploratory families, separately by cohort, rank and test family.

Each cohort/cell produces schema-validated JSON plus compact TSVs for sample metrics, feature-filter counts, beta statistics, secondary tests and figure inputs. JSON rejects NaN/Inf and records software, input hashes, seed, group counts, filter, zero method, distance and interpretation flags. The checked-in schema is `result_schema.json`.

## Interpretation and execution gate

A PERMANOVA signal with material PERMDISP evidence is described as location and/or dispersion structure (`DISPERSION_QUALIFIED`), not a clean centroid shift. Null or very small effects remain reportable. Formal analysis begins only after ETYY recovery confirms the old installation state, exact zCompositions 1.6.2 behavior on a synthetic vector, immutable inputs and a separately visible formal-analysis authorization. Differential abundance remains exploratory and is not automatically authorized by this plan.
