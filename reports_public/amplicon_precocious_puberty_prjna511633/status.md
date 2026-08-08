# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T04:48:55+00:00

Progress state: `failed_needs_patch`

## Current Interpretation

- Next action: Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause.
- Validation errors: 1
- Validation warnings: 0
- Missing expected outputs: 11

## Required Outputs

- validation_report: yes
- manifest: yes
- command_log: yes
- demux_artifact: yes
- demux_visualization: yes
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

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' dada2 denoise-paired --i-demultiplexed-seqs '/mnt/disk1/db/kraken2/0714/results/20260808T070000Z-prjna511633-icpp-16s-full-auto-local-gzip-retry/qiime2/demux.qza' --p-trim-left-f 0 --p-trim-left-r 0 --p-trunc-len-f 280 --p-trunc-len-r 220 --p-n-threads 4 --o-table '/mnt/disk1/db/kraken2/0714/results/20260808T070000Z-prjna511633-icpp-16s-full-auto-local-gzip-retry/qiime2/table.qza' --o-representative-sequences '/mnt/disk1/db/kraken2/0714/results/20260808T070000Z-prjna511633-icpp-16s-full-auto-local-gzip-retry/qiime2/rep-seqs.qza' --o-denoising-stats '/mnt/disk1/db/kraken2/0714/results/20260808T070000Z-prjna511633-icpp-16s-full-auto-local-gzip-retry/qiime2/denoising-stats.qza'

## Recent Failed Command Stderr

- t each quality score. [required] Miscellaneous: --output-dir PATH Output unspecified results to a directory --verbose / --quiet Display verbose output to stdout and/or stderr during execution of this action. Or silence output if execution is successful (silence is golden). --example-data PATH Write example data and exit. --citations Show citations and exit. --use-cache DIRECTORY Specify the cache to be used for the intermediate work of this action. If not provided, the default cache under $TMP/qiime2/<uname> will be used. IMPORTANT FOR HPC USERS: If you are on an HPC system and are using parallel execution it is important to set this to a location that is globally accessible to all nodes in the cluster. --help Show this message and exit. Examples: # ### example: denoise paired qiime dada2 denoise-paired \ --i-demultiplexed-seqs demux-paired.qza \ --p-trunc-len-f 150 \ --p-trunc-len-r 140 \ --o-representative-sequences representative-sequences.qza \ --o-table table.qza \ --o-denoising-stats denoising-stats.qza \ --o-base-transition-stats base-transition-stats.qza There was a problem with the command: (1/1) Missing option '--o-base-transition-stats'. ("--output-dir" may also be used)
