# PRJNA511633 ICPP Gut 16S Analysis Plan

## Dataset

- BioProject: `PRJNA511633`
- Study: The Association of Gut Microbiota With Idiopathic Central Precocious Puberty in Girls
- Public article: https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2019.00941/full
- Data type: fecal 16S rDNA amplicon sequencing, Illumina MiSeq paired-end
- Public RunInfo records: 48
- Total public SRA size: approximately 622 MB

## Reconstructed Groups

The public article reports 25 girls with idiopathic central precocious puberty (ICPP) and 23 healthy girls. Public SRA sample names use two clear prefixes:

- `CP*`: treated as idiopathic central precocious puberty
- `CH*`: treated as healthy control

This grouping is suitable for first-pass analysis, but the manuscript should state that the mapping was reconstructed from the public article and sample naming. If a supplementary table with exact sample-level labels is later recovered, it should be used to confirm the assignment.

## Current Analysis Jobs

Jobs:

- `jobs/20260808T000000Z-prjna511633-icpp-16s-demux.json`
- `jobs/20260808T010000Z-prjna511633-icpp-16s-full-auto.json`

Task:

- `amplicon_qiime2`

Full automatic execution:

1. Download the 48 SRA runs to `/mnt/disk1/public_datasets/prjna511633_icpp_16s`.
2. Convert paired SRA files with `fasterq-dump --split-files`.
3. Generate a QIIME2 paired-end manifest.
4. Run `qiime tools import`.
5. Run `qiime demux summarize`.
6. Run DADA2 denoising with first-pass MiSeq V3-V4 parameters: `trunc_len_f=280`, `trunc_len_r=220`.
7. Assign taxonomy with the QIIME2 official human-stool weighted SILVA 138 99% classifier.
8. Generate taxa barplot, genus/species relative abundance tables, alpha diversity, beta diversity, and group-difference outputs.

## Analysis Objectives

The required outputs for manuscript screening are:

- Species and genus composition tables.
- Relative-abundance stacked barplot through `taxa-bar-plots.qzv`.
- Alpha diversity: at minimum Shannon diversity and observed features.
- Beta diversity: at minimum Bray-Curtis distance and group significance by `analysis_group`.
- Group comparison: ICPP vs healthy control using QIIME2 group significance outputs, and ANCOM-BC if the installed QIIME2 build supports it.
- Exported tables for independent downstream statistics and figure generation.

## Automatic Failure Handling

The status publisher now writes:

- `reports_public/amplicon_precocious_puberty_prjna511633/status.md`
- `reports_public/amplicon_precocious_puberty_prjna511633/status.json`

These files explicitly report whether each required output exists. If the workstation is idle for more than one check interval and outputs are missing, treat the state as stalled and inspect `validation_report.json` plus `command_log.jsonl`.

Likely fixable failure classes:

- Missing `qiime`: use the absolute QIIME2 binary configured in the full-auto job.
- Classifier missing: download the configured QIIME2 official classifier and verify SHA256.
- DADA2 merge failure: adjust `trunc_len_f`/`trunc_len_r`; for V3-V4 MiSeq PE300, first-pass values are 280/220.
- Low rarefaction depth: lower `diversity_sampling_depth` after checking table summaries.

## Publication Framing

This project should be treated as a re-analysis or validation-oriented secondary analysis of public 16S data. It is not an independent clinical cohort and should not be written as a new diagnostic biomarker study unless an external validation cohort is added.

## Practical Research Direction

The most defensible short-cycle direction is:

**Gut microbiota composition and diversity shifts associated with idiopathic central precocious puberty in girls: a reproducible public 16S re-analysis with targeted validation candidates.**

Primary claims should stay conservative:

- ICPP-associated gut microbial community structure differs from healthy controls.
- Differential taxa can nominate validation targets, but public 16S data alone cannot prove causality.
- Species-level labels from SILVA and short-read 16S should be treated as tentative unless validated.

Wet-lab validation should prioritize fast, low-risk assays:

- qPCR for a short list of reproducible ICPP-associated taxa after the re-analysis confirms direction and abundance.
- SCFA-related follow-up, preferably acetate/propionate/butyrate measurement if a metabolomics platform is available.
- Plating/counting only for cultivable facultative organisms; strict anaerobic gut taxa are not well suited to simple routine plating.

Potential validation candidates from the original report and expected gut biology include `Ruminococcus`, `Gemmiger`, `Roseburia`, `Coprococcus`, and selected `Bacteroides` taxa. The final list should be locked only after the current re-analysis confirms abundance direction, prevalence, and statistical robustness.
