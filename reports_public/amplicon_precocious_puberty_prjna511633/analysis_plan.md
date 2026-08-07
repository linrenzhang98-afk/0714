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

## Current First Stage

Job:

- `jobs/20260808T000000Z-prjna511633-icpp-16s-demux.json`

Task:

- `amplicon_qiime2`

Planned execution:

1. Download the 48 SRA runs to `/mnt/disk1/public_datasets/prjna511633_icpp_16s`.
2. Convert paired SRA files with `fasterq-dump --split-files`.
3. Generate a QIIME2 paired-end manifest.
4. Run `qiime tools import`.
5. Run `qiime demux summarize`.

## Stop Boundary

The first stage intentionally stops after `demux.qzv`.

Do not run DADA2 automatically until quality plots are inspected and defensible paired-end truncation lengths are set. This avoids silently choosing poor trimming parameters for a publication-facing 16S analysis.

## Next Decision After Demux

After `demux.qzv` is generated:

1. Export or inspect the quality summary.
2. Set `trunc_len_f` and `trunc_len_r`.
3. Run DADA2 denoising.
4. Generate alpha/beta diversity summaries.
5. Compare ICPP vs healthy control.
6. Focus interpretation on reproducible re-analysis and conservative validation of reported taxa, not causal claims.

## Publication Framing

This project should be treated as a re-analysis or validation-oriented secondary analysis of public 16S data. It is not an independent clinical cohort and should not be written as a new diagnostic biomarker study unless an external validation cohort is added.
