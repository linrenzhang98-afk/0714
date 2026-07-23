# Ten-Day Travel Analysis Process

## Strategy

Run a small number of robust jobs rather than trying to process every available public dataset.

Priority:

1. `PRJNA1056765` BALF mNGS, DNA WGS runs, Kraken2/Bracken first pass.
2. One respiratory or pediatric BALF 16S dataset for QIIME2, because 16S has lower failure risk.
3. `PRJNA511633` central precocious puberty gut 16S as a separate exploratory theme.

## Recommended Data Volume

- Metagenome first pass: 20-40 DNA WGS runs.
- Metagenome upper bound during travel: 50-100 runs only after the first batch succeeds.
- Amplicon: 30-80 samples preferred; 100-150 acceptable if metadata and read quality are clean.

Do not run all 868 `PRJNA1056765` runs during travel.

## Main Project

`PRJNA1056765` is the main travel-mode metagenome project because a 2-run validation already succeeded.

First batch:

- Select DNA WGS / METAGENOMIC / SINGLE runs.
- Prefer smaller runs first.
- Use `database_mode: test` or `pilot`.
- Use Kraken2/Bracken only.

Output level:

- Per-run Kraken2 report.
- Per-run Bracken species table.
- Batch status table.
- Merged species abundance table when all selected runs finish.
- Public status summary only.

## Backup Projects

Use 16S projects when metagenome download, database, or classification failures block progress.

Suggested 16S backup order:

1. Pediatric BALF / respiratory 16S dataset after accession confirmation.
2. `PRJNA511633` central precocious puberty gut 16S.

For QIIME2, run only to demux summary if truncation lengths are missing. Do not automatically choose DADA2 truncation lengths for production-like interpretation.

## Failure Decisions

Automatically continue:

- Network download retry.
- Single-run download failure after retry.
- Single-run FASTQ conversion failure after retry.
- Single-run Kraken2 failure after retry.
- Bracken failure when Kraken2 succeeded.

Stop and write `decision_requests/*.md`:

- More than 20% selected runs fail.
- More than 10 runs fail.
- Database missing.
- Required software missing.
- Disk free space below 500 GB.
- Metadata missing for group comparison.
- Any large database download is needed.

## Codex Monitoring

Codex checks GitHub every 8 hours at 01:00, 09:00, and 17:00.

Codex should inspect only:

- `reports_public/platform_status.md`
- `decision_requests/*.md`

Codex should not download raw data, full results, or databases.
