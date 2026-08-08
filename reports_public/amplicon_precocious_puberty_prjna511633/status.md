# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T00:09:04+00:00

Progress state: `failed_needs_patch`

## Current Interpretation

- Next action: Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause.
- Validation errors: 1
- Validation warnings: 0
- Missing expected outputs: 14

## Required Outputs

- validation_report: yes
- manifest: no
- command_log: yes
- demux_artifact: no
- demux_visualization: no
- feature_table: no
- rep_seqs: no
- taxonomy: no
- taxa_barplot: no
- genus_relative_table: no
- species_relative_table: no
- core_metrics: no
- shannon_group_significance: no
- bray_curtis_group_significance: no
- genus_export: no
- species_export: no

## Errors

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' tools import --type 'SampleData[PairedEndSequencesWithQuality]' --input-path '/mnt/disk1/db/kraken2/0714/results/20260808T030000Z-prjna511633-icpp-16s-full-auto-manifest-retry/manifest.tsv' --output-path '/mnt/disk1/db/kraken2/0714/results/20260808T030000Z-prjna511633-icpp-16s-full-auto-manifest-retry/qiime2/demux.qza' --input-format PairedEndFastqManifestPhred33V2
