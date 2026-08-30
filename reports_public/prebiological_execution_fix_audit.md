# Pre-biological execution fix audit

## Scope and disposition

This audit closes the two critical and twelve major pre-execution defects identified in the review of commit `6af4aee44ad61fbbfd075f80889160a7aab143d2`. All implementation checks used synthetic identifiers and synthetic count matrices. No biological abundance matrix, ETYY session, differential-abundance analysis or DeepSeek call was used.

The package is statistically and programmatically prepared for the frozen analyses. Biological execution remains stopped pending the already-defined workstation recovery evidence: the old installation state must be preserved and classified, and R 4.5.3 plus the exact isolated zCompositions 1.6.2 runtime must pass the synthetic CZM gate. This is an operational evidence requirement, not an unresolved analysis-design defect.

## Critical defects

| Defect | Resolution | Verification |
|---|---|---|
| Invalid PERMDISP label/centroid permutation | Replaced with an observed centroid-distance ANOVA followed by fixed-model least-squares residual permutations. Labels and centroids are not recomputed in the null iterations. | Locked explicit-map reference fixture, deterministic tests, pathological/degenerate tests and an optional vegan reference driver. |
| Ambiguous 0.5 sensitivity | Frozen as addition of exactly 0.5 to every retained feature count, including nonzero counts, before closure and CLR. | Code, manifest, plan, Methods, registry, schema metadata and synthetic cell-level test agree on `zero_method=additive_pseudocount`, `pseudocount=0.5`, `applied_to=all_retained_features`. |

## PERMDISP algorithm and reference boundary

For each distance representation, the implementation first calculates the observed distance from each sample to its observed group centroid and computes the ordinary one-way ANOVA F statistic and eta-squared for those distances. It then fits the fixed one-way group model, obtains least-squares residuals, streams each deterministic permutation within the applicable exchangeability blocks, refits the unchanged design to the permuted residual vector, and recomputes F. The Monte Carlo P value uses the plus-one correction. The production count is 9,999.

This matches the residual-permutation structure documented by the [vegan `permutest.betadisper` source](https://github.com/vegandevs/vegan/blob/master/R/permutest.betadisper.R) and its [betadisper documentation](https://vegandevs.github.io/vegan/reference/betadisper.html). The locked fixture supplies independently evaluated expected distances, observed F/eta-squared and F values for explicit permutation maps. `shotgun_analysis/reference_permdisp_vegan.R` can run the same explicit maps against vegan when that package is available. The package does not claim blanket numerical equivalence to vegan without the same distance and permutation matrices.

The primary Aitchison geometry is Euclidean and fails on a materially negative squared centroid distance. For the single non-Euclidean Bray-Curtis sensitivity, signed squared distances follow the Anderson/vegan handling: negative values are changed to zero and the count is serialized.

## Major defects

| # | Defect | Resolution |
|---:|---|---|
| 1 | Silent duplicate collapse | Duplicate sample/run IDs, count rows, QC rows and TSV headers fail before dictionary/index construction; conflicting duplicate metadata is named. |
| 2 | Ordering-dependent contrast signs | External effects are Drug_Resistance minus Drug_Sensitive. Anchor pairwise effects are Lung cancer minus each named infection group. Reordering tests cover the rank statistic and complete binary pipeline. |
| 3 | Flexible production settings | Production accepts only the two frozen accessions, exact sample/group counts, the seven fixed method cells, 9,999/9,999 permutations, Aitchison primary geometry and cell-specific deterministic seeds. Invalid method combinations fail before inputs are opened. |
| 4 | Weak result invariants | JSON Schema 2.0.0 plus cross-field validation checks n/group/sample consistency, unique IDs, feature and diagnostic dimensions, read denominators, method/ordination compatibility, exact orientations, exact algorithms/seeds and required provenance. Negative fixtures are included. |
| 5 | Incomplete CZM path provenance | The production path is exactly `/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3`. R must be 4.5.3; zCompositions must be 1.6.2; zCompositions, NADA and truncnorm versions/paths and effective `.libPaths()` are serialized; the isolated path must be first; other-library resolution fails. No installation was attempted. |
| 6 | Undefined post-omnibus behavior | All 15 fixed anchor contrasts are calculated and Holm-adjusted. Confirmatory interpretation is gated endpoint by endpoint by that endpoint's Holm-adjusted five-endpoint omnibus test; otherwise the contrast remains descriptive. |
| 7 | Contradictory Bray scope | Frozen to one cohort-specific 10%-prevalence comparator on sample-wise proportions, with no zero replacement, using PERMANOVA plus residual-permutation PERMDISP. It is not crossed with the filter/zero grid. |
| 8 | Undefined technical sensitivities | Anchor: marginal diagnosis in `Aitchison ~ collection_year + diagnosis`, reduced-model residual permutations within Training/Test. External: marginal resistance status in `Aitchison ~ nominal_read_length + resistance_status`. Missing, inadequate or singular designs serialize `NOT_RUN_DESIGN_GATE`; neither is primary adjustment. |
| 9 | Unchecked exchangeability | Anchor analysis serializes the diagnosis-by-Training/Test table and requires every diagnosis at least twice in every block. Blocking is explicitly not batch/split adjustment. Pathological designs fail. |
| 10 | Promised but absent uncertainty/figure outputs | Point PERMANOVA R², PERMDISP eta-squared, centroid-distance summaries and deterministic CLR-PCA/Aitchison-PCoA-equivalent coordinates are produced. Unsupported effect-size CIs were removed from manuscript and table/figure promises. |
| 11 | Alpha-diversity interpretation risk | Alpha metrics remain secondary and use complete direct-species vectors. Richness effort sensitivity is explicit. Total input, all classified and direct-species assigned reads are serialized with denominator invariants; classified fraction is not depth correction or biomass. |
| 12 | Vague ecological generalizability | Frozen as a two-resolution study: between-diagnosis anchor ecology and within-TB resistance ecology, connected only by reusable classifier-defined measurement and a common robustness framework. It requires interpretable contrast-specific magnitude/dispersion, transparent representation stability and comparable observability/limits; it implies no common direction, coefficient, taxon, signature or mechanism. |

## Additional review items

- The 402-to-400 anchor transition is resolved from repository provenance. `reports_public/metagenome_400_formal/audit/data_availability.json` and `publication_package/consistency_audit.tsv` identify SRR27343810/patient 20210709MCX011 (Fungal infection) and SRR27343463/patient 20211125MCX012 (Lung cancer) as `size_MB=0` with no reads available. The frozen 400 population is unchanged.
- Zero burden is serialized per sample and per taxon, together with retained taxa, zero-cell burden and sample-wise total-variation perturbation. These are descriptive and never exclusion or method-selection rules.
- Permutation maps are streamed rather than materialized as a 9,999-element collection.
- Manuscript language was consolidated around the two-resolution question. Prohibitions on pooling, replication, causality, biomarkers and biomass interpretation remain explicit.

## Verification

- `python3 -m py_compile shotgun_analysis/*.py scripts/run_formal_cross_cohort_analysis.py scripts/run_formal_cross_cohort_grid.py tests/test_shotgun_formal_analysis.py`: PASS.
- Shotgun formal-analysis suite: 49 synthetic tests, PASS.
- Full repository discovery suite: 157 tests, PASS. The pre-escalation run's sole failure was the sandbox prohibition on opening a localhost socket in an unrelated lifecycle test; the complete suite passed when local loopback was permitted.
- JSON parsing and schema-backed positive/negative fixtures: PASS.
- `git diff --check`: PASS at audit time.

## Remaining execution gate

`READY_FOR_REAL_BIOLOGICAL_ANALYSIS=false` until workstation recovery supplies runtime evidence. Required evidence is the preserved old job state, exact R/package/path resolution, deterministic synthetic CZM conformance and an immutable execution commit. No new scientific design or shotgun-analysis coding blocker remains.
