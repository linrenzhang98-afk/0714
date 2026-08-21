# PRJCA046985 pilot readiness

**Scientific status: SCIENTIFICALLY_PREFERRED. Technical status: CONDITIONAL_PILOT_READY.**

The DNA manifest contains 130 unique runs and subjects. GSA DNA run aliases directly equal the patient identifiers in Supplementary Table S3, producing 49 `Drug_Resistance` and 81 `Drug_Sensitive` records. The labels derive from independently reported phenotypic or molecular drug-susceptibility testing, not microbiome output.

Exact public compressed total is 2,082,679,760 bytes. Each DNA subject has one public `.fq.gz`; GSA does not declare pairing in the captured metadata. Supplementary Table S3 links the public patient alias to `unhost_reads`, providing stronger host-depletion evidence than PRJCA039020, but exact host tool/reference and library batch remain incomplete. GSA did not publish cryptographic checksums in the verified pages; filename, exact HTTP Content-Length and ETag are recorded.

No explicitly labelled public negative control was found among the 130 DNA plus 130 RNA runs. No control threshold will be borrowed from another cohort.

Live inventory confirms installed 50- and 75-nt Bracken redistribution files. Two allowlisted deposited files have expected 50- and 75-nt architectures and total 10,526,255 bytes. Execution must verify actual FASTQ layout and read length and stop before Bracken on any mismatch. Integrity uses exact recorded bytes, file identity/ETag where available, and gzip/FASTQ checks because GSA did not publish cryptographic checksums. This remains a technical pilot; two samples cannot support biological inference.
