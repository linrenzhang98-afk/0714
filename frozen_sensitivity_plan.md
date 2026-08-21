# Frozen sensitivity plan

**Re-frozen after five pre-analysis DeepSeek review rounds:** 2026-08-20 Asia/Shanghai, before any new statistical calculation in this phase. **Status: FROZEN v5.** Earlier drafts failed the live supervisor gate and were corrected before outcome inspection. No parameter may be added or changed after this point. Any future addition requires a new user-approved version and cannot be pooled with this run.

## Scope and estimand

Use only the frozen 400-run species matrix, metadata, and existing QC definitions. The estimand is diagnosis-associated community variation in the frozen 400-run cohort. It is **not** a reconstruction of Han et al.'s published cancer-versus-infection ecological contrast in the n=284 training set. This grid does not search for taxa, construct an oral score, analyze HUMAnN, fit diagnostic models, make causal claims, or process FASTQ.

| Dimension | Frozen levels or rule |
|---|---|
| Prevalence | 5% (≥20/400), 10% (≥40/400; anchor), 20% (≥80/400); membership defined once in the full n=400 cohort |
| CLR zero replacement | P1 = 0.5 × the minimum positive retained abundance; P2 = 0.1 × that same minimum; derived once for each prevalence level from the full cohort |
| Distance | Aitchison at P1 and P2; Bray–Curtis on renormalized retained relative abundance |
| Population | Full n=400; existing strict-QC subset where `sensitivity_included=True` (n=119) |
| QC definition | Existing flags only: classified fraction <0.5%; Bracken assigned reads <1,000; observed species ≤2; or absolute robust MAD z-score >3.5 for log10 reads, classified fraction, richness, or dominance |
| Permutations | One pooled PERMANOVA statistic per cell. For each of 9,999 deterministic draws, diagnosis labels are shuffled independently within Training and Test strata, the full permuted label vector is reconstructed, and the pooled statistic is recalculated. Every non-anchor cell has a unique seed and independent permutation draws; only the anchor replay reuses frozen seeds. |
| Dispersion | PERMDISP paired with every PERMANOVA using the identical distance matrix, subset, grouping, and 9,999 permutations |

## Complete grid

The 18 output cells are divided before execution into five non-poolable audit layers. Layer 0 is the exact anchor integrity replay only and produces no new inference. Layer 1 is the full-cohort 10% P2 Aitchison pseudocount audit with the same 30-species membership; it is not an integrity replay. Layer 2 contains the full-cohort 5% and 20% Aitchison cells and is a **feature-space audit**. Layer 3 contains all strict-QC cells and is a **QC-subset audit**, not a transfer population. Layer 4 contains all Bray–Curtis cells and is a **metric/dispersion comparator**. Layers 1–4 cannot be pooled with Layer 0. The entire exercise is audit-only and has no new primary inference.

Each cell must report sample count, retained-feature count, pseudocount where applicable, PERMANOVA R² and permutation P, PERMDISP statistic and P, seed, code path, and input hashes. Results are summarized by effect-size range, direction of inference, and dispersion behavior—not ranked by P value.

The strict-QC population is the exact set of 119 run IDs already marked `sensitivity_included=True` in `reports_public/metagenome_400_formal/qc/cohort_qc.tsv`, SHA-256 `e3e4cfbdaf412d20bd9ee6dd82e1e811d12046556b176adf0678c34c6373f790`. Its matrix is obtained only by row-subsetting the hashed frozen full-cohort matrix; the pipeline is not rerun. Membership is not recalculated. Frozen group counts are bacterial infection 42, fungal infection 19, lung cancer 36, and pulmonary tuberculosis 22. The minimum group-size rule is ≥15; all groups pass.

## Explicit cell enumeration

Cells 1–6 are full cohort at 5%, 10%, and 20% prevalence, each with Aitchison P1 and P2. Cells 7–9 are full cohort Bray–Curtis at 5%, 10%, and 20%; each uses exactly the same prevalence-defined species membership as its Aitchison counterpart. Cells 10–15 repeat the six Aitchison feature/pseudocount combinations in strict-QC n=119. Cells 16–18 are strict-QC Bray–Curtis at 5%, 10%, and 20%, again using the corresponding prevalence-defined membership. Bray–Curtis retains observed zeros, adds no pseudocount, and is calculated on retained relative-abundance rows renormalized to sum to one.

## Interpretation rules fixed before execution

- R² <0.05 is described as negligible or very small; 0.05–<0.10 as small. No R² below 0.10 is described as a substantively meaningful biological driver.
- The frozen anchor Aitchison result remains the prior frozen inference, not a new grid result. Bray–Curtis is excluded from the anchor sensitivity layer and cannot qualify, downgrade, replace, or reinterpret the anchor Aitchison location estimate.
- Aitchison location evidence is dispersion-qualified when the paired PERMDISP permutation P<0.05; the same operational threshold applies to Bray–Curtis. No directional or effect-size exception overrides this rule.
- Bray–Curtis with PERMDISP P<0.05 is described as a location-and/or-dispersion difference, never an unqualified centroid shift.
- Layer 0 reports only whether exact replay passed. Layer 1 independently classifies the P2 cell as dispersion-unqualified (PERMDISP P≥0.05) or dispersion-qualified (P<0.05), then reports its absolute R² difference from the prior frozen anchor descriptively. It does not generate a new “anchor stability” inference.
- Layer 2 reports each prevalence-defined feature space separately, with no pooled range or “majority of cells” statement.
- Layer 3 reports each strict-QC cell separately, is not an anchor sensitivity analysis, cannot contribute to the anchor stability range, cannot be numerically compared with full-cohort cells as the same estimand, and cannot be attributed to biology.
- Layer 4 reports each Bray–Curtis cell separately and is excluded from all statements about robustness of the Aitchison location estimate.
- The strict-QC subset is only a pipeline-dependent sensitivity analysis. Agreement with the full cohort does not validate the pipeline, and disagreement cannot be attributed to biology.
- No cell may be selectively highlighted because it has the smallest P value, largest R², or most favorable dispersion result.
- No disease-specific taxon, cancer/TB/infection “community shift,” or pairwise disease claim may be produced from this omnibus grid. Reporting is restricted to diagnosis-associated variation at the omnibus level.
- No post-hoc pairwise disease or subgroup contrast may be computed or reported from any grid cell.
- The omnibus result cannot be described as evidence of a lung-cancer-associated microbiome, TB-associated microbiome, infection-associated microbiome, or disease-associated community state. X% is reported only as a statistical variance component conditional on this frozen pipeline, not as a biological effect size or evidence that diagnosis is a meaningful driver.
- No result licenses “fingerprint,” “biomarker,” “diagnostic,” “causal,” or “mechanistic” language.
- Every grid conclusion is conditional on the frozen Kraken2/Bracken pipeline. Because database/version, negative-control handling, normalization, and some taxon directions remain unresolved against Han et al., grid results cannot be interpreted as evidence about the biological cohort or as adjudicating biological disagreement between pipelines.

Uncertainty for this bounded phase is the complete prespecified grid range plus permutation compatibility and dispersion behavior. No post-hoc bootstrap or additional model is authorized. New outputs must be separate from `reports_public/metagenome_400_formal` and must never overwrite the frozen analysis.

## Provenance of the frozen anchor result

The previously frozen primary result is not newly calculated in this phase. Its exact definition is full cohort n=400, the same 30-species membership retained at ≥40/400 prevalence, P1 CLR pseudocount `1.0097644219603566e-05`, Aitchison distance, the same pooled Gower statistic, four-level diagnosis, and 9,999 diagnosis-label permutations independently shuffled within Training/Test strata using PERMANOVA seed `1056965` and PERMDISP seed `1056966`. It was generated by `scripts/analyze_prjna1056765_metagenome_400.py` and is recorded in `reports_public/metagenome_400_formal/statistics/permanova_permdisp.tsv` (manifest SHA-256 `090ba6d93cb7f79d75ce953152e3c93a0f26fe72196705df1ef86af5c0e9cdcd`), with PERMANOVA R²=0.0194095366 and P=0.0001 and PERMDISP P=0.487. The exact frozen Aitchison distance output has SHA-256 `55b246e2853eb108fed54c6e4dd2baca8f0bdf216d038bc8a2bd3a177a8b9028`. The frozen species-matrix output has manifest SHA-256 `7d4ce545524869be783aa3f2dc0371315f30db33d3ae6c324d13768f2396053d`; the analysis-parameter file has SHA-256 `560da7b75142979f562bbb4350ff19111880d45ad2df8361183c6ce62cedd9f5`.

The full-cohort 10% P1 cell in the grid is an integrity replay of this exact anchor: identical retained membership, pseudocount, distance/Gower code path, strata, statistic, and seeds. It is not a new primary analysis. Before computing any other cell, the executable must require exact Python numeric equality for PERMANOVA F=2.612771519062346, R²=0.019409536625522597, P=0.0001, PERMDISP F=0.8066530620728115, PERMDISP R²=0.006073890452579873, and P=0.487. Any mismatch aborts execution before output. The manifest must record expected values, observed values, and `anchor_replay_verified_exactly=true`.

The exact 30-species membership and order are read from `frozen_anchor_species.tsv`, SHA-256 `1fea6bdb0199c9ab218c1f1f098b524a4f1f9a774a93f4cdef7b11ee1a655833`, transcribed from the frozen species landscape. The replay does not substitute a newly derived list; the executable separately verifies that the ≥40/400 membership derived from the hashed input is exactly identical to this list.

## Frozen executable and output contract

The only authorized executable is `scripts/run_prjna1056765_frozen_sensitivity_grid.py`, SHA-256 `6b5fed89312923a308df8456e3807dc5f798c9ef3ee92d1d6049b25bd9d460e1`. This hash supersedes the pre-computation commit's executable hash after a DeepSeek-approved deterministic correction that orders equal-prevalence anchor species by the already frozen anchor file; no species, parameter, statistic, seed, cell, or interpretation rule changed. The primary input matrix is `reports_public/metagenome_production/bracken_species_fraction_matrix.tsv`, SHA-256 `0c7ad6930c4e2db5fd3ec0a58861850274eb75dd31350ab00f4428a41a6ad20d`. Clinical metadata SHA-256 is `3de4e218e8f0e9e32545cead271e6750c39ac0dea4c47df291123175292400be`. Before computation the script must verify the exact expected hashes for matrix, clinical metadata, QC membership, and anchor-species file and abort on any mismatch. The manifest must record expected and observed hashes and `input_hashes_verified_exactly=true`.

The only authorized output directory is `reports_public/metagenome_400_sensitivity_v2/`, containing `frozen_sensitivity_grid.tsv` and `manifest.json`. The TSV schema and column order are frozen as: `population`, `prevalence_threshold`, `prevalence_count`, `metric`, `pseudocount_rule`, `pseudocount_value`, `is_anchor_replay`, `n`, `retained_features`, `permanova_F`, `permanova_R2`, `permanova_p`, `permdisp_F`, `permdisp_R2`, `permdisp_p`, `permutations`, `permanova_seed`, `permdisp_seed`, `matrix_sha256`, `qc_sha256`, `clinical_sha256`, `plan_sha256`, `script_sha256`. Python's standard string conversion is used for numeric values; booleans are `True` or `False`; unavailable pseudocount is an empty field.
