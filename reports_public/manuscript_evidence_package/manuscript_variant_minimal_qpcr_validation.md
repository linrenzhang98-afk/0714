# Manuscript Variant B: Public Data Plus Minimal qPCR Validation

## Positioning

This variant is stronger for Frontiers in Medicine or Journal of Clinical Medicine because it adds a short wet-lab validation module without turning the project into a long mechanistic study.

Recommended article type:

- Original research
- Brief report
- Translational bioinformatics short communication

## Title

Public BALF mNGS re-analysis and targeted qPCR validation prioritize pathogen markers for pulmonary infection

## Abstract Template

Bronchoalveolar lavage fluid metagenomic next-generation sequencing can support broad pathogen detection in pulmonary disease, but public mNGS datasets require targeted validation before translational interpretation. We re-analyzed PRJNA1056765, a public BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. Among 400 analyzable DNA WGS/mNGS runs, Kraken2/Bracken profiling prioritized `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus` as the strongest diagnosis-associated candidates. A selected 30-sample deep-review set retained the same top pathogen after QC re-analysis, and host-removal/AMRFinderPlus screening detected no AMR hit rows in capped host-removed subsets. We then performed targeted qPCR validation for [validated targets] in [local BALF sample design]. [Insert validation result: detection rates, concordance, or effect direction.] These findings support a short-cycle strategy in which public BALF mNGS re-analysis prioritizes pathogen markers for focused local validation, while antimicrobial-resistance and clinical diagnostic claims remain outside the supported scope.

## Minimal Validation Question

Do locally available BALF samples show directional support for the public-data-prioritized targets?

## Recommended Minimal Target Panel

| Target | Role | Preferred validation readout |
|---|---|---|
| `Pseudomonas aeruginosa` | Core bacterial target | qPCR/ddPCR presence or copy signal |
| `Aspergillus fumigatus` | Core fungal target | qPCR/ddPCR presence or copy signal |
| `Cryptococcus neoformans` | Optional secondary fungal target | qPCR/ddPCR only if enough fungal-positive samples exist |
| `Mycobacterium tuberculosis` | Strong bioinformatic endpoint | Include only under existing approved TB workflow |

## Minimal Local Cohort Design

Preferred:

- bacterial infection BALF group
- fungal infection BALF group
- lung cancer BALF disease-control group or other non-target BALF controls

Minimum useful design:

- target-positive clinical group versus non-target BALF comparator group

Avoid:

- healthy-control wording unless true healthy BALF controls exist
- diagnostic accuracy claims unless a prespecified validation cohort exists
- resistance claims unless independent AST/culture/resistance data exist

## Plate Count / Culture Support

Plate count or routine culture can be included only as a conventional supportive readout for routine bacterial targets when local clinical-lab workflow already permits it.

Best use:

- supportive bacterial burden evidence for `P. aeruginosa`
- concordance with qPCR positivity

Do not use as:

- the main validation endpoint for the public mNGS re-analysis
- a tuberculosis workflow
- a fungal workflow unless already routine and approved locally
- a basis for resistance inference

## Results Insert Template

### Targeted validation supported the public-data prioritization of selected markers

Targeted qPCR validation was performed in [N] local BALF samples, including [group counts]. `Pseudomonas aeruginosa` was detected in [x/y] bacterial infection samples and [x/y] comparator samples. `Aspergillus fumigatus` was detected in [x/y] fungal infection samples and [x/y] comparator samples. The validation results were directionally consistent with the public mNGS re-analysis, supporting the feasibility of using public BALF mNGS data for short-cycle pathogen-marker prioritization.

If results are weak:

Targeted qPCR validation showed partial concordance with the public-data-prioritized signals. This finding does not invalidate the public-data result, but suggests that local cohort composition, sample handling, or assay sensitivity may affect transferability.

## Additional Figure/Table

### Figure 4 or Figure 5

Targeted validation of prioritized pathogen markers.

Panels:

- qPCR detection by local clinical group
- concordance with public-data target ranking
- optional culture/plate count support for routine bacterial target only

### Validation Table

Suggested columns:

- local sample ID
- clinical group
- qPCR target
- positive/negative or quantitative readout
- culture/plate count supportive result if available
- concordance category

## Discussion Insert

The validation module is designed to test feasibility rather than establish clinical diagnostic performance. Directional agreement for `P. aeruginosa` and `A. fumigatus` would strengthen the central claim that public BALF mNGS datasets can prioritize short-cycle validation targets. Discordance should be interpreted as a transferability boundary rather than as a failure of the public-data analysis.

## Best Use

Use this version if qPCR validation can be completed quickly. It is more suitable than the public-data-only version for Frontiers in Medicine or Journal of Clinical Medicine.
