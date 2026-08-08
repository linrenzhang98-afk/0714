# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T12:50:56+00:00

Progress state: `analysis_outputs_ready_with_optional_warnings`

## Current Interpretation

- Next action: Summarize exported taxa tables and report rarefied QIIME2 group-significance visualizations as unavailable due low retained sample count.
- Validation errors: 0
- Validation warnings: 3
- Missing required outputs: 0
- Missing optional outputs: 2

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
- genus_export: yes
- species_export: yes

## Recent Failed Command Stderr

- ld change (lfc), standard error (se), P values, Q values, and W scores. Inputs: --i-data ARTIFACT FeatureData[DifferentialAbundance | ANCOMBC2Output] The ANCOM-BC or ANCOM-BC2 output to be tabulated. [required] Outputs: --o-visualization VISUALIZATION [required] Miscellaneous: --output-dir PATH Output unspecified results to a directory --verbose / --quiet Display verbose output to stdout and/or stderr during execution of this action. Or silence output if execution is successful (silence is golden). --example-data PATH Write example data and exit. --citations Show citations and exit. --use-cache DIRECTORY Specify the cache to be used for the intermediate work of this action. If not provided, the default cache under $TMP/qiime2/<uname> will be used. IMPORTANT FOR HPC USERS: If you are on an HPC system and are using parallel execution it is important to set this to a location that is globally accessible to all nodes in the cluster. --help Show this message and exit. There was a problem with the command: (1/1) Invalid value for '--i-data': /mnt/disk1/db/kraken2/0714/results/202608 08T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional- retry/qiime2/genus-ancombc.qza does not exist.

## Warnings

- optional command failed and was skipped: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' diversity alpha-group-significance --i-alpha-diversity '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/core-metrics/shannon_vector.qza' --m-metadata-file '/mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv' --o-visualization '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/shannon-group-significance.qzv'
- optional command failed and was skipped: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' diversity beta-group-significance --i-distance-matrix '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/core-metrics/bray_curtis_distance_matrix.qza' --m-metadata-file '/mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv' --m-metadata-column 'analysis_group' --p-pairwise --o-visualization '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/bray-curtis-group-significance.qzv'
- optional command failed and was skipped: if unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' composition ancombc --help >/dev/null 2>&1; then unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' composition ancombc --i-table '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/genus-table.qza' --m-metadata-file '/mnt/disk1/db/kraken2/0714/reports_public/amplicon_precocious_puberty_prjna511633/sample_metadata.tsv' --p-formula 'analysis_group' --o-differentials '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/genus-ancombc.qza' && unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' composition tabulate --i-data '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/genus-ancombc.qza' --o-visualization '/mnt/disk1/db/kraken2/0714/results/20260808T110000Z-prjna511633-icpp-16s-full-auto-depth10-optional-retry/qiime2/genus-ancombc.qzv'; else echo 'QIIME2 composition ancombc unavailable; skipping ANCOM-BC.'; fi
