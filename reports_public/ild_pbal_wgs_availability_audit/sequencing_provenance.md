# Sequencing and raw-read provenance

The paper verifies protected BAL from the right middle lobe, Illumina NovaSeq 6000 paired-end 150-bp WGS, and GAIA 2.02 processing. Before library preparation, bacterial DNA was extracted with enzymatic/mechanical lysis using FastPrep-24 and FastDNA Spin Kit. Libraries used Celero DNA-Seq and were quantified/QC'd with Qubit 2.0 and Agilent 2100 Bioanalyzer.

The paper says that raw reads were analysed in GAIA and that human DNA was removed before bacterial OTU identification by removing taxa under Chordata. It also says WGS samples had high human contamination. It does **not** report a pre-sequencing host-depletion protocol, public raw filenames, checksums, per-sample size distribution, compressed total bytes, or a public retrieval mechanism.

Its Data availability statement points only to the Dryad share URL labelled “Private for peer review”. In this audit, that link had no public released dataset DOI or file manifest discoverable through official public records. Accordingly, `RAW_FASTQ`, raw byte totals, checksums, whether deposited files would be pre/post computational host filtering, and individual sample layout remain **UNRESOLVED**. No raw file was requested or downloaded.

Sources: article DOI `10.1186/s12931-025-03404-5`, PMCID `PMC12628550`, and the article's exact Dryad share URL recorded in `data_access_inventory.tsv`.
