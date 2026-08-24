# PRJCA039020 final public supplementary-material rescue

All seven publisher-declared supplementary files were inspected from the public PMC12227010 supplementary bundle. The Frontiers article XML is the authoritative file enumeration; the PMC direct download endpoint was bot-gated at retrieval, so the public Europe PMC mirror bundle was used for the actual bounded download. The bundle was 3,459,663 bytes (SHA-256 `43f293720991103e79948ebb0276feaf54ba49ff730ebe46b7b82c1767b9f82a`), below the 20 MiB cap.

## Result

`Table_2.xlsx` is a patient-level clinical workbook: its `CAP-204cases` and `SP-25cases` sheets contain 204 and 25 sequentially numbered clinical rows, respectively. Thus it verifies the paper-level 204/25 clinical table and supplies row-level group membership within the workbook. Its only row key is a sequential `NO.` ordinal, however; it has no stable de-identified participant/sample identifier that deterministically joins to the 233-record repository inventory. The inspected tables/source data contain no deterministic DRR/DRX/DRS/SAMD/SAMC/BALF-to-final-subject-to-CAP/SP bridge. No accession-order, row-order, demographic, file-size, or probabilistic matching was used.

The full supplement inventory, table structures, identifier hits, safe ZIP member inventory, patient-row audit, and deterministic overlap test are in the adjacent TSV artifacts. ZIP members were listed/read in memory only after traversal, entry-count, member-size, and total-uncompressed-size gates; scripts found in Data Sheet 1 were not executed.

Therefore public evidence is exhausted for this specified supplementary-material rescue: the 243 → 233 → 229 linkage, four additional public records, ten nonpublic original records, and exact 204/25 reconstruction remain **UNRESOLVED**. The only permitted next stage is `AUTHOR_CONTACT_REQUIRED`.
