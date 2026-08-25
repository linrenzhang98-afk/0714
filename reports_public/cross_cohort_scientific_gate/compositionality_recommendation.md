# Compositionality recommendation

## Decision

For a final manuscript, the recommended primary beta-diversity analysis is **cohort-specific Aitchison distance on CLR-transformed species direct-count compositions**. The verified Bray-Curtis layer remains an important, prespecified sensitivity analysis and must not be overwritten or retrospectively relabeled.

The reason is scientific rather than cosmetic. Direct species assignments form a sparse subcomposition whose total varies sharply with classifier yield. Bray-Curtis on direct/all-input-read fractions is affected both by relative taxonomic structure and by the total fraction assigned to species. Aitchison geometry asks the narrower biological question about log-ratios among observed taxa and separates that question from the classified-fraction technical endpoint. Neither representation estimates absolute microbial burden.

This recommendation defines a new analysis. It requires explicit formal-analysis authorization before execution.

## Prospective Aitchison specification

1. **Population.** Analyze PRJNA1056765 (n=400) and PRJCA046985 (n=130) independently. Never concatenate matrices or estimate one cohort-adjusted 530-sample model.
2. **Feature definition.** Start from Kraken2 species direct-assigned counts. Within each cohort, retain taxids detected with a positive direct count in at least 10% of that cohort. Report 5% and 20% prevalence-filter sensitivity analyses without outcome-guided threshold selection.
3. **Zero handling.** Principal analysis: count-zero multiplicative replacement (`CZM`) using a named, version-pinned implementation, applied within sample after the prevalence filter and before closure. Freeze software/version and all replacement parameters in the formal plan. Sensitivity analysis: add a fixed 0.5 direct-read pseudocount to each retained taxon. Structural absence cannot be distinguished from sampling zeros, so conclusions must be robust to both choices.
4. **Transformation.** Close the zero-replaced retained species vector to unit sum and apply the centered log-ratio transformation within sample.
5. **Distance.** Use Euclidean distance in CLR space, i.e. Aitchison distance.
6. **Anchor PERMANOVA.** Primary model: community distance by four-level published diagnosis. Use 9,999 permutations with a deterministic seed and restrict permutations within the published Training/Test cohort. Report pseudo-F, marginal R², permutation P and group sizes. Sensitivity models add collection year as a prespecified temporal term only if the design matrix remains full rank; use marginal tests rather than order-dependent sequential claims.
7. **External PERMANOVA.** Primary model: community distance by `Drug_Resistance` versus `Drug_Sensitive`. Use 9,999 permutations and a deterministic seed. Sensitivity model adds the frozen nominal 50/75-nt category as a marginal technical term; a stratified analysis may be reported because both resistance groups occur in both categories. Do not treat nominal length as a complete description of deposited variable-length reads.
8. **Dispersion.** Run PERMDISP on the identical Aitchison distance matrix and sample set for every PERMANOVA. Report distance-to-centroid effect summaries and permutation P. A significant PERMANOVA with material dispersion inequality must be described as location and/or dispersion structure, not a clean centroid shift.
9. **Sample QC.** Report total input reads, classified fraction and summed direct species assignments alongside the compositional analysis. Do not adjust away classified fraction automatically; it is partly a feature-generation property and requires a separate sensitivity rationale.

## Existing Bray-Curtis sensitivity layer

Retain the verified cohort-specific Bray-Curtis analysis on direct/all-input-read fractions after the 10% within-cohort prevalence filter. Its PERMANOVA must remain paired with PERMDISP. The current verified artifact used 999 permutations; it is valid as frozen sensitivity evidence. If a new formal analysis is authorized, a prospectively specified 9,999-permutation replay may be added without replacing the original artifact.

Concordance between Aitchison and Bray-Curtis should be judged by whether the bounded clinical association, effect-size scale and dispersion qualification are robust across representations. Discordance is scientifically informative because the distances answer different questions.

## Interpretation boundary

The Aitchison layer estimates relative community organization among directly assigned taxa. The Bray-Curtis all-read layer combines community structure with classifier-yield differences. Classified fraction remains a technical endpoint. None is an assay of total bacterial biomass.
