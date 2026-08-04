# Host-removal / AMR requirements

The current Kraken2/Bracken analysis is complete. Starting host-removal or AMR requires additional local configuration.

## Required before execution

- fastp is not available.
- bowtie2 and/or samtools are not available.
- HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.
- No AMR tool detected among abricate, rgi, amrfinder, diamond.
- AMR_DB_DIR is not configured or does not exist.

Set `HOST_INDEX_PREFIX` and `AMR_DB_DIR` in the systemd service or local shell only after confirming the intended databases.
