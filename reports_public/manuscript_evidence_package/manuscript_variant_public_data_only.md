# Manuscript Variant A: Public-Data-Only Submission

## Positioning

This variant is for immediate submission or pre-submission inquiry when no local wet-lab validation data are available yet.

Recommended article type:

- Short communication
- Brief report
- Public-data re-analysis
- Translational bioinformatics note

Best-fit targets:

- Frontiers in Medicine, if framed around clinical pulmonary infection and mNGS interpretation.
- Infectious-disease or clinical microbiology brief-report journals if a faster, lower-friction route is preferred.
- Journal of Clinical Medicine only if the clinical argument is tightened and the lack of wet-lab validation is clearly framed.

## Title

Public BALF mNGS re-analysis prioritizes pathogen markers for pulmonary infection validation

## Abstract

Bronchoalveolar lavage fluid metagenomic next-generation sequencing can support broad pathogen detection in pulmonary disease, but public mNGS datasets require careful metadata reconstruction and conservative interpretation before they can inform translational follow-up. We re-analyzed PRJNA1056765, a public BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. The final analyzable cohort contained 400 DNA WGS/mNGS runs after two unavailable public WGS records were excluded. Kraken2/Bracken profiling and group-level detection testing prioritized `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus` as the strongest diagnosis-associated candidates. A 30-sample deep-review set retained the same top pathogen after QC re-analysis, and host-removal/AMRFinderPlus screening detected no AMR hit rows in capped host-removed subsets. These results support a public-data framework for prioritizing pathogen markers for short-cycle validation, while diagnostic performance and antimicrobial-resistance inference require independent validation.

## Main Claim

PRJNA1056765 can be re-used as a public BALF mNGS resource to prioritize clinically coherent pathogen markers for later validation.

## What This Variant Can Claim

- Four clinical disease groups were reconstructed from public metadata.
- 400 DNA WGS/mNGS runs were analyzed.
- Candidate pathogens were prioritized by diagnosis-associated detection.
- Selected top-pathogen calls were stable in a 30-sample deep-review subset.
- AMR claims are not supported by the current capped host-removed subset screen.

## What This Variant Must Not Claim

- No clinical diagnostic accuracy.
- No confirmed wet-lab validation.
- No phenotypic antimicrobial-resistance result.
- No healthy-control comparison.
- No claim that all first-pass calls are robust.

## Figure Plan

### Figure 1

Public-data reconstruction and analysis workflow.

Panels:

- SRA and published-label integration.
- Final four-group cohort.
- Analysis modules from Kraken2/Bracken to deep-review and host-AMR guardrail.

### Figure 2

Diagnosis-associated pathogen candidate spectrum.

Panels:

- Candidate species by diagnosis group.
- Detection-rate comparison for `P. aeruginosa`, `M. tuberculosis`, `A. fumigatus`, and `C. neoformans`.
- Candidate tier ranking.

### Figure 3

Robustness and interpretation boundaries.

Panels:

- Deep-review same-top stability.
- Host-AMR screen completion.
- AMRFinderPlus hit rows: zero in capped subsets.
- Interpretation boundary: prioritization only.

## Table Plan

- Table 1: Reconstructed cohort and unavailable WGS records.
- Table 2: Candidate pathogen ranking.
- Table 3: Deep-review and host-AMR guardrail summary.

## Methods Emphasis

The Methods section should emphasize reproducibility of public-data re-analysis:

- public RunInfo and published label reconstruction
- DNA WGS/mNGS inclusion criteria
- Kraken2/Bracken first-pass profiling
- Fisher exact testing and BH-FDR
- selected deep-review stability endpoint
- capped host-removal/AMR guardrail

## Discussion Emphasis

The Discussion should argue that the value of the work is not broad discovery but disciplined candidate prioritization. The manuscript should explicitly state that a future local validation module is the next translational step.

## Submission Risk

Main weakness:

- Descriptive public-data-only studies may be considered insufficiently novel.

Mitigation:

- Emphasize metadata reconstruction, disease-control framing, candidate prioritization, and guardrail analyses.
- Use "candidate prioritization" consistently instead of "diagnostic marker validation."

## Best Use

Use this version if immediate submission speed is more important than maximizing acceptance probability.
