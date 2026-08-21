# Stage 1 figure legends

## Figure 1. Cohort provenance and analytical populations

The published PRJNA1056765 cohort comprised 402 patients and used 284 training records for the reported ecological analyses and an internal 284/118 split for diagnostic modelling. The current secondary compositional robustness reanalysis includes the 400 DNA runs with downloadable reads. Two mapped records lacked downloadable sequence data. The n=119 set is labelled only as a pipeline-dependent sensitivity population. Counts and arrows distinguish data availability, published analytical populations, and current analytical populations; they do not represent independent cohorts. Source: Han et al. (2025), Tang et al. (2025), and the frozen cohort audit.

## Figure 2. Published and current pipelines define non-equivalent analyses

Side-by-side audit of the Han et al. workflow and the frozen current workflow. Shared high-level steps include read preprocessing, human-read removal, Kraken2 classification, and Bracken abundance estimation. Unresolved items include exact database builds and versions, operational negative-control handling, parts of sample filtering, and feature definitions. The published n=284 cancer-versus-infection and pairwise tests differ from the current n=400 four-level omnibus. Differences are classified as upstream processing, statistical method, robustness finding, or unresolved pipeline discrepancy. No pipeline mismatch is interpreted as biological disagreement. Source: Han et al. (2025), Tang et al. (2025), released code, `original_pipeline_reconstruction.md`, and `pipeline_difference_matrix.tsv`.

## Figure 3. Prespecified Aitchison robustness audit in the full cohort

All six full-cohort Aitchison cells from the frozen v5 grid. The exact 10% prevalence, half-minimum-pseudocount anchor retained 30 species and gave R²=0.0194095 with PERMDISP P=0.487. The alternative pseudocount gave R²=0.0190746 with PERMDISP P=0.4677. The 5% feature space retained 90 species; both pseudocount cells were dispersion-qualified. The 20% feature space retained two species; neither cell was dispersion-qualified. Panels separate exact replay, pseudocount sensitivity, and feature-space dependence. Cells are not ranked by P value, R², or dispersion behavior. Source: frozen v5 grid and manifest.

## Figure 4. Results in the pipeline-dependent sensitivity population

All six Aitchison cells in the n=119 pipeline-dependent sensitivity population. The population comprised 42 bacterial infection, 19 fungal infection, 36 lung cancer, and 22 pulmonary tuberculosis cases under the frozen QC definition. Effect-size estimates and paired PERMDISP results are shown separately for each prevalence threshold and pseudocount. No arrow or label treats numerical differences from n=400 as a same-estimand change, independent replication, or biological improvement. Source: frozen v5 grid, cohort QC table, and manifest.

## Figure 5. Supported conclusions and claim limits

Synthesis of the analytical robustness audit. The frozen 30-species Aitchison anchor replayed exactly and was stable to the two prespecified pseudocounts. Estimated magnitude and dispersion qualification depended on feature space, metric, and QC population. Taxon overlap or mismatch with Han et al. is classified only as pipeline/statistical concordance or discrepancy. The figure marks unsupported extensions, including a stable disease fingerprint, biomarker, diagnostic signal, disease-specific taxon discovery, and mechanism. Source: frozen v5 grid, original-paper overlap audit, frozen taxon table, and clustering diagnostics.

## Supplementary Figure S1. Bray–Curtis metric and dispersion comparator

All six Bray–Curtis cells from the frozen v5 grid. Full-cohort R² values were 0.0263302, 0.0153390, and 0.0096564 at 5%, 10%, and 20% prevalence; all paired PERMDISP tests were qualified. In the n=119 pipeline-dependent sensitivity population, R² values were 0.0638835, 0.0607394, and 0.0796114. The 5% cell was not dispersion-qualified, whereas the 10% and 20% cells were. Each result is described as a metric- and population-conditional location and/or dispersion result where applicable.

## Supplementary Table S1. Complete frozen v5 sensitivity grid

All 18 prespecified cells with population, prevalence threshold, retained-feature count, metric, pseudocount, sample count, PERMANOVA F and R², permutation P, PERMDISP F and R², permutation P, seeds, and input, plan, and executable hashes. The exact anchor replay is flagged. No cell was selected or omitted according to its statistical result.
