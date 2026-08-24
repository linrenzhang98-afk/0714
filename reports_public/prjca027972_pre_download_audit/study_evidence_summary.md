# PRJCA027972 / OMIX006862 pre-download audit

Study: Zhang et al., *Frontiers in Cellular and Infection Microbiology* (2022), DOI `10.3389/fcimb.2022.1021320`; corrigendum DOI `10.3389/fcimb.2024.1468511`.

| Finding | Status | Evidence |
|---|---|---|
| Prospective suspected-CAP BALF cohort at Nanjing First Hospital | VERIFIED | Article Methods, study population and design |
| Recruitment October 2021--April 2022 | VERIFIED | Article Methods |
| 66 enrolled patients; BALF within 48 h and split for culture and two mNGS platforms | VERIFIED | Article abstract and Methods |
| Inclusion required sufficient BALF, consent, complete clinicopathological/follow-up information; refusal of consent excluded | VERIFIED | Article Methods |
| 53/66 were established-or-excluded for pathogenic infection (40 established, 13 excluded) | VERIFIED | Article Results |
| Illumina: NEBNext Ultra II; NextSeq 550 DX; 75-bp single-end; about 20M reads/sample | VERIFIED | Article library/sequencing Methods |
| Nanopore: Rapid Barcoding SQK-RPB004/RBK004; GridION X5; about 0.8G/sample | VERIFIED | Article library/sequencing Methods |
| 2024 corrigendum corrects the data-availability statement to OMIX006862 | VERIFIED | Corrigendum |

The article describes paired measurements of one BALF specimen, but the released ZIP manifests do not provide a documented crosswalk joining all Illumina and Nanopore records to the same subject/specimen. This audit therefore does not treat the 132 platform-level sample records, nor the portal's reported 138 "Number/Samples", as independent people. A lexical suffix-stripping check found eight potentially related laboratory stems, but the release does not document that transformation; it is recorded only as a warning signal and is not used as a mapping.

Sources consulted without bulk-read download: official Frontiers article and corrigendum; official OMIX release page and HTTP headers; 128 KiB ZIP central directory plus 25,474 bytes of small manifest records. Total locally acquired archive metadata was 156,546 bytes, below the 50-MB cap.
