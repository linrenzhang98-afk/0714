# Publication-Ready Tables And Figure Captions

## Recommended Main Tables

### Table 1. Reconstructed PRJNA1056765 BALF mNGS cohort

Purpose: document cohort reconstruction and make missing public records transparent.

Suggested columns:

| Column | Content |
|---|---|
| Diagnosis group | Bacterial infection, fungal infection, pulmonary tuberculosis, lung cancer |
| Analyzed DNA WGS/mNGS runs | Final number analyzed |
| Median classified fraction | Kraken2/Bracken classified fraction by group |
| Median top-pathogen fraction | Top-pathogen fraction by group |
| High-confidence runs | Existing public summary count |
| Unavailable WGS records | Run accessions with `size_MB=0`, if any |

Main text message: 400 runs were analyzable, while SRR27343810 and SRR27343463 were unavailable public records rather than analysis failures.

### Table 2. Prioritized pathogen candidates for wet-lab validation

Purpose: connect group-enrichment statistics to practical validation targets.

Suggested columns:

| Column | Content |
|---|---|
| Candidate species | Species-level pathogen candidate |
| Associated diagnosis group | Group where the signal is enriched |
| Detection in target group | Detected runs / group total |
| Detection in other groups | Comparator rate or count |
| BH-FDR | Multiple-testing-adjusted value |
| Validation tier | Tier 1, tier 2, or case-confirmation |
| Suggested marker | qPCR/ddPCR target |
| Interpretation note | Core, conditional, or optional |

Core rows:

| Candidate species | Associated group | Evidence | Suggested marker | Tier |
|---|---|---|---|---|
| `Pseudomonas aeruginosa` | Bacterial infection | 23/114 vs rest rate 0.02448, FDR 2.48792e-05 | `oprL` or `ecfX` | Tier 1 |
| `Mycobacterium tuberculosis` | Pulmonary tuberculosis | 9/86 vs rest rate 0, FDR 0.000533876 | `IS6110` | Tier 1, biosafety-dependent |
| `Aspergillus fumigatus` | Fungal infection | 8/78 vs rest rate 0.00932, FDR 0.0332815 | ITS or 28S | Tier 1 |
| `Cryptococcus neoformans` | Fungal infection | 6/78 vs rest rate 0.00621, FDR 0.110067 | ITS | Tier 2 |

### Table 3. Deep-review and host-AMR guardrail summary

Purpose: show robustness checks and prevent overclaiming.

Suggested columns:

| Column | Content |
|---|---|
| Pathogen group | Deep-review category |
| Deep-review sample count | Number of selected samples |
| Same top pathogen after QC | Count or fraction |
| Host-AMR screen completed | Yes/no |
| AMRFinderPlus hit rows | Count |
| Interpretation boundary | Stability supported, AMR not supported |

Main text message: 30/30 selected deep-review samples retained the same top pathogen after QC; AMRFinderPlus found 0 hit rows in capped host-removed subsets.

## Recommended Main Figures

### Figure 1. Public-data reconstruction and analysis workflow

Caption draft:

Public-data workflow for PRJNA1056765 BALF mNGS re-analysis. Public SRA RunInfo records and published clinical labels were integrated to reconstruct four diagnosis groups: bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. DNA WGS/mNGS runs were profiled with Kraken2/Bracken, followed by group-level species detection testing, selected-sample deep-review QC, host-removal, and exploratory AMRFinderPlus screening. Lung cancer samples were analyzed as disease controls, not healthy controls. Two expected WGS records with `size_MB=0` in SRA RunInfo were reported as unavailable public records.

Panel suggestions:

- Panel A: metadata-to-cohort flow diagram.
- Panel B: four diagnosis groups with analyzed run counts.
- Panel C: analysis modules from first-pass profiling to validation candidate ranking.

### Figure 2. Diagnosis-associated pathogen spectra in BALF mNGS

Caption draft:

Diagnosis-associated species detection patterns across the reconstructed PRJNA1056765 BALF mNGS cohort. The analysis focused on clinically coherent pathogen signals after excluding recurrent low-specificity or background taxa from biological interpretation. `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus` showed the most defensible group-associated signals, while `Cryptococcus neoformans` was retained as a secondary fungal candidate.

Panel suggestions:

- Panel A: heatmap of selected pathogen detection or Bracken fraction by diagnosis group.
- Panel B: dot plot of candidate species with target-group detection rate, comparator rate, and FDR.
- Panel C: tiered validation candidate ranking.

### Figure 3. Validation candidate prioritization

Caption draft:

Wet-lab validation prioritization based on public BALF mNGS re-analysis. Candidate ranking integrated clinical coherence, diagnosis-group enrichment, statistical support, and practical assay feasibility. The shortest validation panel prioritizes `Pseudomonas aeruginosa` using `oprL` or `ecfX` and `Aspergillus fumigatus` using ITS or 28S. `Cryptococcus neoformans` is an optional fungal target if sample numbers permit. `Mycobacterium tuberculosis` is a strong bioinformatic target but should be validated only under approved tuberculosis biosafety workflows.

Panel suggestions:

- Panel A: tiered candidate table or lollipop plot.
- Panel B: minimal qPCR/ddPCR validation design.
- Panel C: interpretation decision tree separating core targets, optional targets, and biosafety-dependent targets.

### Figure 4. Robustness checks and interpretation boundaries

Caption draft:

Robustness and guardrail analyses for selected pathogen calls. Thirty selected pathogen-positive samples spanning nine pathogen groups retained the same top pathogen after QC re-analysis. Host-removal and AMRFinderPlus screening completed for all 30 samples and detected no AMR hit rows in capped host-removed short-read subsets. These results support stability of selected pathogen calls but do not support phenotypic antimicrobial resistance inference.

Panel suggestions:

- Panel A: deep-review pathogen group composition.
- Panel B: same-top pathogen stability summary.
- Panel C: host-AMR screen completion and AMRFinderPlus hit count.
- Panel D: interpretation boundary statement for AMR.

## Supplementary Tables

### Supplementary Table 1. Run-level clinical mapping

Source file: `reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv`

Use: run accession, diagnosis label, sample name, analyzed status.

### Supplementary Table 2. Group-level species differential results

Source file: `reports_public/prjna1056765_group_differentials/group_species_differential.tsv`

Use: full statistical output for species detection comparisons.

### Supplementary Table 3. Wet-lab validation candidate list

Source file: `reports_public/prjna1056765_group_differentials/wetlab_validation_candidates.tsv`

Use: complete candidate ranking beyond the main text tier-1 species.

### Supplementary Table 4. Deep-review comparison results

Source file: `reports_public/metagenome_deep_review_summary/comparison.tsv`

Use: selected-sample top pathogen consistency after QC re-analysis.

### Supplementary Table 5. Host-AMR screen results

Source files:

- `reports_public/metagenome_host_amr_screen/run_status.tsv`
- `reports_public/metagenome_host_amr_screen/amrfinder_hits.tsv`

Use: host-removal/AMR run completion and negative AMRFinderPlus hit table.

## Figure Preparation Notes

- Use disease-control wording for lung cancer throughout.
- Do not plot `Homo sapiens`, plant taxa, or recurrent low-specificity taxa as biological discoveries.
- Separate discovery/prioritization panels from validation panels.
- Mark AMR as exploratory and negative in capped subsets; do not display it as a resistance phenotype.
