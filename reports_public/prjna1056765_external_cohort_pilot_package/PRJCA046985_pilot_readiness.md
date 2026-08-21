# PRJCA046985 pilot readiness

**Scientific status: SCIENTIFICALLY_PREFERRED. Technical status: NOT_READY.**

The DNA manifest contains 130 unique runs and subjects. GSA DNA run aliases directly equal the patient identifiers in Supplementary Table S3, producing 49 `Drug_Resistance` and 81 `Drug_Sensitive` records. The labels derive from independently reported phenotypic or molecular drug-susceptibility testing, not microbiome output.

Exact public compressed total is 2,082,679,760 bytes. Each DNA subject has one public `.fq.gz`; GSA does not declare pairing in the captured metadata. Supplementary Table S3 links the public patient alias to `unhost_reads`, providing stronger host-depletion evidence than PRJCA039020, but exact host tool/reference and library batch remain incomplete. GSA did not publish cryptographic checksums in the verified pages; filename, exact HTTP Content-Length and ETag are recorded.

No explicitly labelled public negative control was found among the 130 DNA plus 130 RNA runs. No control threshold will be borrowed from another cohort.

The cohort is not a substitute pilot in this phase. Matching Bracken redistribution for its actual deposited read length, live hospital resources, layout inspection and checksum strategy must close first.
