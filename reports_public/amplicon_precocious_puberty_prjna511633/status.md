# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T05:51:54+00:00

Progress state: `failed_needs_patch`

## Current Interpretation

- Next action: Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause.
- Validation errors: 1
- Validation warnings: 0
- Missing expected outputs: 8

## Required Outputs

- validation_report: yes
- manifest: yes
- command_log: yes
- demux_artifact: yes
- demux_visualization: yes
- feature_table: yes
- rep_seqs: yes
- taxonomy: yes
- taxa_barplot: no
- genus_relative_table: no
- species_relative_table: no
- core_metrics: no
- shannon_group_significance: no
- bray_curtis_group_significance: no
- genus_export: no
- species_export: no

## Errors

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' feature-table summarize --i-table '/mnt/disk1/db/kraken2/0714/results/20260808T080000Z-prjna511633-icpp-16s-full-auto-dada2-output-retry/qiime2/table.qza' --m-sample-metadata-file '/mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv' --o-visualization '/mnt/disk1/db/kraken2/0714/results/20260808T080000Z-prjna511633-icpp-16s-full-auto-dada2-output-retry/qiime2/table.qzv'

## Recent Failed Command Stderr

- /home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/site-packages/rescript/evaluate.py:25: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81. import pkg_resources There was an issue with loading the file /mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv as metadata: Metadata column name 'sample_name' conflicts with a name reserved for the ID column header. Reserved ID column headers: Case-insensitive: 'feature id', 'feature-id', 'featureid', 'id', 'sample id', 'sample-id', 'sampleid' Case-sensitive: '#OTU ID', '#OTUID', '#Sample ID', '#SampleID', 'sample_name' There may be more errors present in the metadata file. To get a full report, sample/feature metadata files can be validated with Keemei: https://keemei.qiime2.org Find details on QIIME 2 metadata requirements here: https://docs.qiime2.org/2025.10/tutorials/metadata/
