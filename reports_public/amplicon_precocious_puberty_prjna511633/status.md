# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T08:49:53+00:00

Progress state: `failed_needs_patch`

## Current Interpretation

- Next action: Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause.
- Validation errors: 1
- Validation warnings: 0
- Missing expected outputs: 4

## Required Outputs

- validation_report: yes
- manifest: yes
- command_log: yes
- demux_artifact: yes
- demux_visualization: yes
- feature_table: yes
- rep_seqs: yes
- taxonomy: yes
- taxa_barplot: yes
- genus_relative_table: yes
- species_relative_table: yes
- core_metrics: yes
- shannon_group_significance: no
- bray_curtis_group_significance: no
- genus_export: no
- species_export: no

## Errors

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' diversity alpha-group-significance --i-alpha-diversity '/mnt/disk1/db/kraken2/0714/results/20260808T100000Z-prjna511633-icpp-16s-full-auto-depth100-retry/qiime2/core-metrics/shannon_vector.qza' --m-metadata-file '/mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv' --o-visualization '/mnt/disk1/db/kraken2/0714/results/20260808T100000Z-prjna511633-icpp-16s-full-auto-depth100-retry/qiime2/shannon-group-significance.qzv'

## Recent Failed Command Stderr

- /home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/site-packages/rescript/evaluate.py:25: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81. import pkg_resources Plugin error from diversity: Either the metadata file does not meet the requirements of this visualizer, or the samples associated with the metadata do not meet the requirements. The visualizer requires at least one metadata column that contains categorical data, isn't empty, doesn't consist of unique values, and doesn't consist of exactly one value. The contents of the metadata file associated with the samples present in the alpha-diversity metric are: CH20, CP21. Please check your metadata file and the diversity metric to ensure an appropriate sampling depth was selected. If your sampling depth is too deep, it may result in too few samples being retained for the visualizer. Debug info has been saved to /tmp/qiime2-q2cli-err-4lnhnq3v.log
