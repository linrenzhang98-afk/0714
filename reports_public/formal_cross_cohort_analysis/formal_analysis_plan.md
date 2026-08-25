# Formal cross-cohort analysis plan — method preflight stop

## Decision

The formal biological/statistical analysis is **not queued**. Execution stopped before reading outcome matrices because the authorized primary zero-handling method is not reproducibly available in the reviewed execution environment.

The frozen scientific gate requires exact count-zero multiplicative replacement (CZM), with a named and version-pinned implementation. The canonical reviewed implementation is `zCompositions::cmultRepl(..., method = "CZM")`. Repository-wide inspection found only the prospective CZM recommendation, not executable CZM code. The existing ETYY inventory verifies Python and classifier executables but does not establish an R runtime or an installed `zCompositions` version. Installing software is outside this authorization. A home-grown approximation and substitution of the authorized 0.5-pseudocount sensitivity would both violate the gate.

The exact unresolved dependency is an ETYY-accessible, version-pinned implementation equivalent to `zCompositions` 1.6.2 `cmultRepl` with `label=0`, `method="CZM"`, `output="prop"`, `frac=0.65`, `threshold=0.5`, and `adjust=TRUE`, together with its declared R dependencies. The implementation contract is documented by the [official `cmultRepl` reference](https://search.r-project.org/CRAN/refmans/zCompositions/html/cmultRepl.html) and [CRAN package record](https://cran.r-project.org/package=zCompositions).

No production definition, queue envelope, formal-analysis job ID, or biological result was created.

## Frozen inputs and populations

The only permitted analytical source remains the successful ETYY handoff for job `20260825T080123Z-prjna1056765-prjca046985-common-kraken2-layer-codefix-rerun` at:

`/mnt/disk1/0714_control/state/20260825T080123Z-prjna1056765-prjca046985-common-kraken2-layer-codefix-rerun-handoff`

When the method dependency is separately resolved, the analysis must use species direct-assigned counts, never clade counts, from:

- `anchor_species_direct_counts.tsv` and `anchor_sample_qc.tsv`
- `external_species_direct_counts.tsv` and `external_sample_qc.tsv`

The frozen analytical populations are:

- PRJNA1056765, n=400: Bacterial infection 114; Fungal infection 78; Lung cancer 122; Pulmonary tuberculosis 86.
- PRJCA046985, n=130: Drug_Resistance 49; Drug_Sensitive 81.

They are separate cohorts with different clinical estimands. No pooled 530-sample model, common clinical coefficient, P-value combination, multicenter claim, or formal meta-analysis is permitted.

## Prospective primary analysis after dependency resolution

Within each cohort independently, retain species with positive direct counts in at least 10% of samples. Repeat at fixed 5% and 20% thresholds as sensitivity analyses without outcome-guided selection. Apply exact CZM within each retained sample vector, close to unit sum, transform by CLR, and compute Euclidean distance in CLR space.

The anchor primary model is the four-level published-diagnosis association. It requires 9,999 deterministic permutations restricted within the repository's frozen Training/Test strata and paired PERMDISP with 9,999 permutations on the identical sample set and distance matrix. Collection year is a marginal sensitivity term only if run-level mapping is complete and the design matrix is full rank.

The external primary model is Drug_Resistance versus Drug_Sensitive, with 9,999 deterministic permutations and matching PERMDISP. The frozen nominal 50/75-nt category is a technical sensitivity only after verifying that both resistance groups occur in both categories.

Every primary analysis is repeated using the fixed 0.5 direct-read pseudocount as a sensitivity, never as a replacement for CZM. The existing 999-permutation Bray-Curtis analysis remains frozen sensitivity evidence and is not overwritten.

## Secondary endpoint freeze

The five prespecified endpoints are richness, Shannon diversity, Gini-Simpson, dominance, and Kraken2 classified fraction. Classified fraction is a technical classifier-yield endpoint, not bacterial load.

For the anchor, the frozen omnibus test is Kruskal-Wallis with epsilon-squared and uncertainty. Only within the omnibus framework, the three prespecified lung-cancer contrasts use two-sided Wilcoxon rank-sum tests with rank-biserial correlations and uncertainty. Holm correction covers the complete 15-test family formed by three contrasts and five endpoints. Other pairwise comparisons remain exploratory and cannot drive the manuscript claim.

For the external cohort, the frozen test is two-sided Wilcoxon rank-sum with rank-biserial correlation and uncertainty. Holm correction covers the five endpoint tests. Tests cannot be changed after viewing significance.

## Interpretation and execution boundary

A PERMANOVA finding accompanied by material PERMDISP inequality must be described as location and/or dispersion structure, not a clean centroid shift. Permitted language includes “associated with,” “community structure differed,” “dispersion-qualified,” and “ecological organization.” Causal, biomarker, diagnostic-signature, validation, and replication claims are prohibited.

Differential abundance, new cohorts, raw acquisition, Kraken2, Bracken, host filtering, trimming, DeepSeek, and all biological computation remain unexecuted. Resumption requires a separate method-runtime gate that either verifies the exact pinned CZM implementation already present on ETYY or explicitly authorizes a controlled software provision and conformance test. The present authorization does not permit either assumption.
