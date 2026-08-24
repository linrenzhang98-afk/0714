# Technical compatibility

The official archive is an open 3,116,968,192-byte ZIP, but its platform payloads are FASTA files rather than deposited raw FASTQ. The mNGS records are explicitly named `*.nohost.fasta`; the paper reports quality filtering and GRCh38 human-read removal before alignment to NCBI nt. The repository therefore exposes processed, host-depleted sequences, not a native raw Illumina read layer.

Paper protocol: Illumina NEBNext Ultra II libraries on NextSeq 550 DX, 75-bp single-end, about 20 million reads per sample. Nanopore used Rapid Barcoding SQK-RPB004 (<20 ng/mL) or SQK-RBK004 (>20 ng/mL) on GridION X5, about 0.8 G data/sample. The paper removes adapters, duplicated/short reads (<50 bp Illumina, <500 bp Nanopore), then removes human alignments to GRCh38.

`ILLUMINA_NATIVE_KRAKEN2_FEASIBLE=false` for the intended common native layer: raw read provenance and a deterministic platform/sample mapping are missing, and host-depleted FASTA cannot be represented as a native raw-read reprocessing input without changing the frozen technical definition. No Kraken2 or Bracken command was run.
