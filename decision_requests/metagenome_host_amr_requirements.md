# Host-removal / AMR requirements

The current Kraken2/Bracken analysis is complete. Starting host-removal or AMR requires additional local configuration.

## Required before execution

- HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.
- AMR_DB_DIR is not configured or does not exist.

The status publisher is configured to prepare the GRCh38 Bowtie2 host index and AMRFinderPlus database automatically.
