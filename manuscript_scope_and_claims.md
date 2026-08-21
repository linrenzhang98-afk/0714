# Manuscript scope and claims

## In scope

- Reconstruct the original PRJNA1056765 preprocessing, ecological analysis, and modeling boundaries.
- Quantify diagnosis-associated variance conditional on the frozen pipeline.
- Evaluate whether distance-based inference is affected by multivariate dispersion.
- Report dependence on QC population and analytical feature space without treating those as biological validation.
- Evaluate whether community-state solutions are stable across metrics.

## Permitted claims

- “Diagnosis accounted for approximately 1.9% of Aitchison community variation in the frozen full cohort.”
- “The frozen Bray–Curtis difference was accompanied by differential dispersion and does not establish an unqualified centroid shift.”
- “Taxon-level results were sparse, substantially overlapped the original publication, and were partly QC-dependent.”
- “No metric-stable ecotype solution was identified under the frozen clustering design.”
- “Results are conditional on the current Kraken2/Bracken pipeline and available public cohort.”

## Prohibited claims

- Distinct disease microbiome fingerprints or natural diagnostic classes.
- New discovery of P. micra, P. gingivalis, F. nucleatum, or other highlighted taxa.
- Biomarker, diagnostic-performance, causal, aspiration, inflammatory, active-microbiome, or mechanistic claims.
- Independent validation by the same 402-patient source cohort.
- Biological explanation of discrepancies before upstream equivalence is established.
- Pairwise disease conclusions derived post hoc from the omnibus grid.

## Manuscript type and title boundary

The work is a secondary compositional robustness and reproducibility audit. Titles and abstracts must name that scope. They must not use “fingerprints,” “discriminates,” “predicts,” “biomarkers,” or equivalent language.

## Stop rules

Stop the manuscript if original processed matrices/splits cannot be audited enough to separate pipeline from inference, if the story requires new taxa or diagnostic performance for interest, or if the frozen sensitivity design is altered after outcome inspection.

Full manuscript writing remains blocked until the user approves the storyline and figure structure.

## Final DeepSeek conditions

- The v5 sensitivity grid is a separate pending execution item and is not evidence until executed and gated.
- The n=400 four-level omnibus is not a reproduction of Han et al.'s n=284 cancer-versus-infection ecological contrast; this distinction must appear in Methods and Results.
- Taxon overlap is pipeline/statistical concordance only; discordance is not biological contradiction.
- No pairwise or subgroup contrast may be derived from the omnibus analysis or introduced in legends.
- Strict-QC n=119 is a pipeline-dependent sensitivity population, never validation or a superior biological cohort.
- Every Bray–Curtis statement must carry its dispersion qualification.
