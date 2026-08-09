# PRJNA1056765 Functional Shotgun Profile

Generated at: 2026-08-09T11:04:20+00:00
State: `blocked_setup`

## Reason

- HUMAnN commands remain unhealthy after conda/mamba installation

## Completion

- Samples considered: 30
- Done: 0
- Running: 0
- Failed: 0
- Skipped: 0

## Tools

- humann: `/home/suma/anaconda3/envs/mgshotgun/bin/humann`
- humann_databases: `/home/suma/anaconda3/envs/mgshotgun/bin/humann_databases`
- humann_join_tables: `/home/suma/anaconda3/envs/mgshotgun/bin/humann_join_tables`
- humann_renorm_table: `/home/suma/anaconda3/envs/mgshotgun/bin/humann_renorm_table`
- metaphlan: `/home/suma/anaconda3/envs/mgshotgun/bin/metaphlan`
- diamond: `/home/suma/anaconda3/envs/mgshotgun/bin/diamond`

## Databases

- ChocoPhlAn ready: False
- UniRef ready: False
- Utility mapping ready: False
- Database root: `/mnt/disk1/db/humann`

## Output Files

- `run_status.tsv`
- `summary.json`
- `merged_genefamilies.tsv` if HUMAnN join succeeds
- `merged_pathabundance.tsv` if HUMAnN join succeeds
- `merged_pathabundance_relab.tsv` if HUMAnN renormalization succeeds

## Guardrails

- This stage uses existing host-removed FASTQ files from the deep-review set.
- Functional profiling is exploratory until sample metadata and clinical grouping are strengthened.
