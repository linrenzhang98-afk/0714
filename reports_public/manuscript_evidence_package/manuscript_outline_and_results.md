# Manuscript Outline and Results Narrative

## One-Sentence Argument

In public BALF mNGS data from PRJNA1056765, diagnosis-associated pathogen spectra distinguish bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer disease controls, supported by a 400-run re-analysis, group-level pathogen enrichment, 30-sample deep-review stability, and a negative exploratory host-removal/AMR screen.

## Terminology Ledger

- BALF: bronchoalveolar lavage fluid.
- mNGS: metagenomic next-generation sequencing.
- PRJNA1056765: public BioProject analyzed in this work.
- Disease control: lung cancer BALF samples, not healthy controls.
- First-pass profiling: Kraken2/Bracken profiling across 400 DNA WGS/mNGS runs.
- Deep-review: QC re-analysis of 30 selected pathogen-positive samples.
- Host-AMR screen: host-removal plus AMRFinderPlus exploratory screen on capped host-removed short-read subsets.

## Proposed Title Options

1. Diagnosis-associated pathogen signatures in BALF mNGS distinguish pulmonary infections from lung cancer controls
2. Re-analysis of PRJNA1056765 reveals infection-specific pathogen spectra in BALF metagenomes
3. Public BALF mNGS re-analysis prioritizes pathogen markers for rapid pulmonary infection validation

Most defensible title: option 1. It states the system, signal, and comparator without overclaiming clinical diagnostic performance.

## Manuscript Structure

### Abstract

Use an unstructured abstract unless the target journal requires headings.

Draft:

Bronchoalveolar lavage fluid metagenomic sequencing is increasingly used to investigate pulmonary infection, but public datasets can also support targeted marker prioritization when clinical labels are reconstructed carefully. We re-analyzed PRJNA1056765, a BALF mNGS BioProject with published labels for bacterial infection, fungal infection, pulmonary tuberculosis, and lung cancer. Among 400 analyzable DNA WGS/mNGS runs, Kraken2/Bracken profiling showed diagnosis-associated pathogen spectra, with `Pseudomonas aeruginosa`, `Mycobacterium tuberculosis`, and `Aspergillus fumigatus` emerging as the strongest group-enriched validation candidates. A 30-sample deep-review set retained the same top pathogen after QC re-analysis, supporting the robustness of selected calls. Host-removal and AMRFinderPlus screening completed for all 30 deep-review samples, with no AMR hits detected in capped host-removed short-read subsets. These results support a focused, bioinformatics-led short project in which public BALF mNGS data prioritize pathogen markers for independent qPCR/ddPCR validation, while antimicrobial resistance conclusions remain outside the supported scope.

### Introduction

Paragraph plan:

1. Clinical need: pulmonary infections and malignancy can produce overlapping respiratory presentations, and BALF mNGS offers broad microbial detection.
2. Bottleneck: public mNGS re-analyses often struggle with incomplete metadata, background taxa, low classified fractions, and overinterpretation of pathogen or AMR calls.
3. Gap: PRJNA1056765 provides a large BALF clinical resource, but a short-project framing needs clinically mapped groups, conservative pathogen prioritization, and explicit validation boundaries.
4. Present study: reconstruct four diagnosis groups, profile pathogen spectra, prioritize wet-lab targets, and test selected call stability with QC plus host-removal/AMR guardrails.

### Results

#### Result 1: Cohort reconstruction produced a four-group BALF mNGS analysis set.

Draft:

We reconstructed the clinical grouping of PRJNA1056765 from the published metadata and retained 400 DNA WGS/mNGS runs for analysis. The final analysis set included 114 bacterial infection runs, 78 fungal infection runs, 86 pulmonary tuberculosis runs, and 122 lung cancer runs. Two expected WGS records, SRR27343810 and SRR27343463, had `size_MB=0` in SRA RunInfo and were therefore treated as unavailable public records rather than failed analyses. This reconstruction establishes lung cancer as a disease-control group rather than a healthy BALF control group.

#### Result 2: Diagnosis groups showed distinct pathogen-enrichment patterns.

Draft:

Species-level detection patterns differed across the four diagnosis groups. `Pseudomonas aeruginosa` was enriched in bacterial infection samples, detected in 23 of 114 bacterial infection runs compared with a 0.02448 detection rate in the remaining groups (BH-FDR 2.48792e-05). `Mycobacterium tuberculosis` was enriched in pulmonary tuberculosis, detected in 9 of 86 tuberculosis runs and absent from the comparison groups (BH-FDR 0.000533876). `Aspergillus fumigatus` was enriched in fungal infection samples, detected in 8 of 78 fungal infection runs compared with a 0.00932 detection rate in the remaining groups (BH-FDR 0.0332815). `Cryptococcus neoformans` showed a weaker but biologically plausible fungal-enrichment signal and should be treated as a secondary validation candidate.

#### Result 3: Deep-review supported stability of selected pathogen calls.

Draft:

To test whether selected pathogen calls were robust to an additional QC pass, we deep-reviewed 30 pathogen-positive samples spanning Acinetobacter, Candida, Enterobacterales, Haemophilus, Mycobacteria, Pseudomonas, Staphylococcus, Stenotrophomonas, and Streptococcus groups. All 30 samples retained the same top pathogen after QC re-analysis. This result supports the stability of selected high-priority calls, while not implying that all first-pass calls across the full cohort are equally robust.

#### Result 4: Host-removal/AMR screening added a conservative interpretation boundary.

Draft:

Host-removal and exploratory AMR screening completed for all 30 deep-review samples. AMRFinderPlus detected no AMR hit rows in capped host-removed short-read subsets. This negative result should be interpreted conservatively: it does not establish absence of antimicrobial resistance, but it reduces support for making resistance claims from the current public-data workflow. The manuscript should therefore frame AMR as a checked but unsupported exploratory endpoint.

### Discussion

Main interpretation:

- The strongest short-project story is not broad microbiome discovery; it is conservative pathogen-marker prioritization from a public BALF mNGS cohort.
- `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus` are the most defensible group-associated targets.
- Lung cancer controls help assess disease-context specificity but do not substitute for healthy controls.
- Negative AMR findings are useful as a boundary: they prevent overclaiming and strengthen methodological discipline.

Limitations:

- Public metadata are reconstructed from published supplemental labels.
- Kraken2/Bracken profiling is database-dependent and classified fractions are low.
- The deep-review set is selected, not a full-cohort re-analysis.
- AMR screening used capped short-read subsets and cannot support phenotypic resistance inference.
- Wet-lab validation is still required for translational claims.

### Conclusion

Draft:

This re-analysis converts PRJNA1056765 from a large public BALF mNGS resource into a focused pathogen-prioritization framework for a short translational bioinformatics project. The strongest current evidence supports targeted validation of `P. aeruginosa`, `A. fumigatus`, and conditionally `M. tuberculosis`, with lung cancer BALF samples used as disease controls. The work should be presented as candidate prioritization and robustness checking, not as a stand-alone clinical diagnostic or resistance study.

## Claim-Evidence Map

- Claim: PRJNA1056765 can support a four-group BALF mNGS re-analysis. Evidence: 400 mapped DNA WGS/mNGS runs across bacterial, fungal, tuberculosis, and lung cancer labels. Status: supported.
- Claim: `P. aeruginosa`, `M. tuberculosis`, and `A. fumigatus` are priority validation candidates. Evidence: group enrichment and FDR values. Status: supported.
- Claim: selected pathogen calls are stable after QC re-analysis. Evidence: 30/30 stable same-top calls. Status: supported for selected samples.
- Claim: AMR can be inferred from current workflow. Evidence: no AMRFinderPlus hits in capped subsets. Status: not supported; use as negative exploratory boundary only.

## Immediate Writing Tasks

1. Convert this outline into a full Results section with tables referenced explicitly.
2. Prepare a one-page wet-lab validation protocol around the minimal target panel.
3. Decide target journal format and abstract structure before full manuscript drafting.
