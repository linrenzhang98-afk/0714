# PRJNA1056765 Short-Project Evidence Package

## Working Title

BALF mNGS pathogen signatures distinguish pulmonary infection categories from lung cancer controls in PRJNA1056765.

## Recommended Manuscript Type

- Bioinformatics-led short communication or brief report.
- Wet-lab module should be targeted qPCR/ddPCR validation in independent/local BALF samples, not broad discovery.
- Current public-data analysis is sufficient for hypothesis generation and candidate prioritization; it is not sufficient for phenotypic antimicrobial resistance claims.

## Central Claim

Four clinically labeled BALF mNGS groups in PRJNA1056765 show diagnosis-associated pathogen spectra, with selected pathogen calls stable after QC re-analysis and host-removal/AMR exploratory screening.

## Evidence Already Available

- 400 DNA WGS/mNGS runs analyzed.
- Clinical groups mapped from published supplementary labels:
  - Bacterial infection: 114
  - Fungal infection: 78
  - Lung cancer: 122
  - Pulmonary tuberculosis: 86
- Two public WGS records were unavailable in SRA RunInfo because `size_MB=0`: SRR27343810 and SRR27343463.
- Deep-review selected 30 pathogen-positive samples across pathogen groups.
- Deep-review stability: 30/30 selected samples retained the same top pathogen after QC rerun.
- Host-removal/AMR screen: 30/30 completed; AMRFinderPlus detected 0 AMR hit rows in capped host-removed short-read subsets.

## Primary Bioinformatic Results To Build Around

1. Cohort reconstruction and public-data audit
   - Reconstruct four diagnosis groups from BioProject/Supplementary metadata.
   - Report missing/unavailable WGS runs transparently.

2. Diagnosis-associated pathogen spectrum
   - Main comparison: bacterial infection, fungal infection, pulmonary tuberculosis, lung cancer.
   - Lung cancer should be treated as disease control, not healthy control.

3. Candidate pathogens for focused validation
   - `Pseudomonas aeruginosa`: bacterial infection enriched; 23/114 vs rest rate 0.02448; FDR 2.48792e-05.
   - `Mycobacterium tuberculosis`: tuberculosis enriched; 9/86 vs rest rate 0; FDR 0.000533876.
   - `Aspergillus fumigatus`: fungal infection enriched; 8/78 vs rest rate 0.00932; FDR 0.0332815.
   - `Cryptococcus neoformans`: suggestive fungal enrichment; 6/78 vs rest rate 0.00621; FDR 0.110067.

4. Robustness and guardrails
   - Deep-review result supports stability of selected top-pathogen calls.
   - Background/low-specificity taxa such as `Homo sapiens`, plant taxa, and recurrent unlikely taxa should be reported separately and not interpreted as disease biology.
   - AMR screen is negative in capped read subsets and should be framed as "no exploratory AMR signal detected", not as absence of resistance.

## Wet-Lab Validation Priority

Tier 1, shortest practical validation:

- `Pseudomonas aeruginosa`: qPCR marker `oprL` or `ecfX`.
- `Aspergillus fumigatus`: ITS or 28S assay.
- `Cryptococcus neoformans`: ITS assay if enough fungal BALF positives are available.

Conditional:

- `Mycobacterium tuberculosis`: `IS6110` only if the lab already has approved TB workflow and biosafety conditions. Otherwise keep as bioinformatic endpoint.

Tier 2 case confirmation:

- `Haemophilus influenzae` (`hpd`)
- `Staphylococcus aureus` (`nuc`)
- `Streptococcus pneumoniae` (`lytA`)
- `Klebsiella pneumoniae` (`khe` or `rpoB`)
- `Candida albicans` (ITS or `ACT1`)

## Suggested Figure Plan

- Figure 1: Study workflow and cohort reconstruction.
- Figure 2: Diagnosis-group pathogen spectrum and top enriched taxa.
- Figure 3: Wet-lab candidate ranking with detection rates, FDR, and validation markers.
- Figure 4: Deep-review stability plus host-removal/AMR guardrail summary.

## Key Limitations To State Explicitly

- Public dataset is BALF mNGS from disease groups; no true healthy BALF control group.
- Kraken2/Bracken results depend on database composition and low-classified fractions.
- Host-removal/AMR screen used capped subsets and is exploratory.
- Wet-lab validation is required before clinical diagnostic claims.

## Immediate Next Action

Draft a manuscript outline and results narrative using this evidence package, then define the smallest wet-lab validation panel: `P. aeruginosa`, `A. fumigatus`, and optional `C. neoformans` or TB depending on available samples and biosafety.
