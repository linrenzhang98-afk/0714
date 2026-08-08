# PRJNA511633 Amplicon Status

Generated at: 2026-08-08T03:45:49+00:00

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

- command failed: unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; export PATH='/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin':${PATH:-}; '/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/bin/qiime' tools import --type 'SampleData[PairedEndSequencesWithQuality]' --input-path '/mnt/disk1/db/kraken2/0714/results/20260808T050000Z-prjna511633-icpp-16s-full-auto-wide-manifest-retry/manifest.tsv' --output-path '/mnt/disk1/db/kraken2/0714/results/20260808T050000Z-prjna511633-icpp-16s-full-auto-wide-manifest-retry/qiime2/demux.qza' --input-format PairedEndFastqManifestPhred33V2

## Recent Failed Command Stderr

- er_sample_sequences/_formats.py", line 119, in _validate_ validate_paired_ends_equal_record_count( File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/site-packages/q2_types/per_sample_sequences/_util.py", line 390, in validate_paired_ends_equal_record_count fwd_count = count_lines(file_fwd) File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/site-packages/q2_types/per_sample_sequences/_util.py", line 386, in count_lines while block := f.read(1024 * 1024): File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/gzip.py", line 301, in read return self._buffer.read(size) File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/_compression.py", line 68, in readinto data = self.read(len(byte_view)) File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/gzip.py", line 488, in read if not self._read_gzip_header(): File "/home/suma/anaconda3/envs/qiime2-amplicon-2025.10/lib/python3.10/gzip.py", line 436, in _read_gzip_header raise BadGzipFile('Not a gzipped file (%r)' % magic) gzip.BadGzipFile: Not a gzipped file (b'@S') An unexpected error has occurred: Not a gzipped file (b'@S') See above for debug info.
