# PRJNA1056765 Functional Shotgun Profile

Generated at: 2026-08-12T06:50:38+00:00
State: `initializing`

## Reason

- Functional profiling worker started.

## Completion

- Samples considered: 30
- Done: 0
- Running: 0
- Failed: 0
- Skipped: 0

## Tools

- humann: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/humann`
- humann_databases: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/humann_databases`
- humann_join_tables: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/humann_join_tables`
- humann_renorm_table: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/humann_renorm_table`
- metaphlan: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/metaphlan`
- diamond: `/home/suma/anaconda3/envs/humann-shotgun-clean/bin/diamond`

## Databases

- ChocoPhlAn ready: True
- UniRef ready: True
- Utility mapping ready: True
- Database root: `/mnt/disk1/db/humann`
- MetaPhlAn DB ready: False
- MetaPhlAn DB root: `/mnt/disk1/db/metaphlan/vJun23`
- MetaPhlAn DB index: `mpa_vJun23_CHOCOPhlAnSGB_202403`

## Output Files

- `run_status.tsv`
- `summary.json`
- `merged_genefamilies.tsv` if HUMAnN join succeeds
- `merged_pathabundance.tsv` if HUMAnN join succeeds
- `merged_pathabundance_relab.tsv` if HUMAnN renormalization succeeds

## Guardrails

- This stage uses existing host-removed FASTQ files from the deep-review set.
- Functional profiling is exploratory until sample metadata and clinical grouping are strengthened.
