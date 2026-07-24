# PRJNA1056765 Production Sample Planning

Generated at: 2026-07-24T16:12:04+00:00

## Candidate Counts

- Total RunInfo rows: 868
- Candidate DNA WGS metagenomic single-end runs: 400
- Unique BioSamples among candidates: 400
- Representative runs by BioSample: 400
- Duplicate BioSample run rows: 0
- Excluded runs: 468

## Size Bins

- 001_lt25mb: 356
- 002_25_99mb: 36
- 003_100_249mb: 6
- 005_500mb_plus: 2

## Production Before-Run Checklist

- Confirm clinical question and grouping labels.
- Confirm whether DNA and RNA libraries should remain separate.
- Confirm BioSample duplicate handling; default candidate rule is largest run per BioSample.
- Confirm whether all candidate DNA WGS runs or representative BioSample runs should be used.
- Confirm final database/method choices before production conclusions.
- Do not treat travel-mode pilot/focused results as final biological conclusions.

## Output Files

- `candidate_dna_wgs_runs.tsv`
- `representative_runs_by_biosample.tsv`
- `duplicate_biosample_runs.tsv`
- `excluded_runs.tsv`
- `production_candidate_summary.json`
