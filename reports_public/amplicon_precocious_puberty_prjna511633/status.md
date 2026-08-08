# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T01:29:07+00:00

Progress state: `failed_needs_patch`

## Current Interpretation

- Next action: Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause.
- Validation errors: 1
- Validation warnings: 0
- Missing expected outputs: 13

## Required Outputs

- validation_report: yes
- manifest: yes
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

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' tools import --type 'SampleData[PairedEndSequencesWithQuality]' --input-path '/mnt/disk1/db/kraken2/0714/results/20260808T040000Z-prjna511633-icpp-16s-full-auto-tsv-retry/manifest.tsv' --output-path '/mnt/disk1/db/kraken2/0714/results/20260808T040000Z-prjna511633-icpp-16s-full-auto-tsv-retry/qiime2/demux.qza' --input-format PairedEndFastqManifestPhred33V2

## Recent Failed Command Stderr

- urces.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81. import pkg_resources There was a problem importing /mnt/disk1/db/kraken2/0714/results/20260808T040000Z-prjna511633-icpp-16s-full-auto-tsv-retry/manifest.tsv: /mnt/disk1/db/kraken2/0714/results/20260808T040000Z-prjna511633-icpp-16s-full-auto-tsv-retry/manifest.tsv is not a(n) PairedEndFastqManifestPhred33V2 file: There was an issue with loading the metadata file: Metadata IDs must be unique. The following IDs are duplicated: 'CH1', 'CH10', 'CH11', 'CH12', 'CH13', 'CH14', 'CH15', 'CH16', 'CH17', 'CH18', 'CH19', 'CH2', 'CH20', 'CH21', 'CH22', 'CH23', 'CH3', 'CH4', 'CH5', 'CH6', 'CH7', 'CH8', 'CH9', 'CP1', 'CP10', 'CP11', 'CP12', 'CP13', 'CP14', 'CP15', 'CP16', 'CP17', 'CP18', 'CP19', 'CP2', 'CP20', 'CP21', 'CP22', 'CP23', 'CP24', 'CP25', 'CP3', 'CP4', 'CP5', 'CP6', 'CP7', 'CP8', 'CP9' There may be more errors present in the metadata file. To get a full report, sample/feature metadata files can be validated with Keemei: https://keemei.qiime2.org Find details on QIIME 2 metadata requirements here: https://docs.qiime2.org/2025.10/tutorials/metadata/
