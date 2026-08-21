# External cohort executive brief

## Decision summary

1. **Candidate datasets found:** 13 independent dataset families were screened; duplicate accessions and paired platforms were counted once.
2. **Genuinely usable now:** one conditional A and two B cohorts are scientifically plausible. None is production-ready until run–sample–subject manifests and label provenance are frozen. One additional low-cost cohort is a reserve pending non-circular label validation.
3. **Highest priorities:** PRJCA046985/CRA034880 (conditional A), PRJCA039020/CRA024916/PRJDB36521 (B), and PRJNA977832/SRP440548 (B). PRJCA027972/OMIX006862 is an operational reserve.
4. **Independence:** each priority dataset represents a separate patient cohort and institution from PRJNA1056765. Dual GSA/INSDC registrations for PRJCA039020 are one cohort. Paired Illumina/Nanopore data in PRJCA027972 are one cohort.
5. **Exclusions:** PRJCA028177 lacks an independent comparator; PRJNA979827 is incomplete and severely imbalanced; PRJNA450137, PRJEB64676 and PRJNA875913 use tracheal aspirates and/or RNA; PRJNA419524 is a 13-pair WGA virome; PRJNA1216061 has unresolved mixed specimens. PRJNA991321 and the small Sulaiman BAL projects remain methods-only reserves.
6. **Enough for a cross-cohort SCI:** **conditionally**. The anchor plus two externally usable cohorts could support descriptive cross-cohort generalizability, but only after label/mapping blockers resolve. The cohorts estimate different clinical contrasts, so the paper cannot claim replicated disease signatures or a common pooled diagnosis effect.
7. **Hospital compatibility:** likely, using the existing frozen Kraken2/Bracken infrastructure after hash, read-length and Bracken-file checks. A common database standardizes classification but cannot remove study, host-depletion, extraction, platform or batch differences.
8. **Estimated raw storage:** priority A/B combined is approximately **1.08–1.45 TB**, dominated by verified 917.36 GB for PRJNA977832; the range includes a 150–500 GB provisional reservation for PRJCA046985 and 17–35 GB for PRJCA039020. Temporary capacity is approximately 2–3.3 TB. These are ceilings, not precise forecasts.
9. **Estimated compute:** approximately **1,800–5,600 CPU-hours** for A/B cohorts, with large uncertainty until smoke-test throughput is measured. No environment/database rebuild is planned.
10. **Proceed to pilot:** **yes, conditionally**, only after exact manifests and one explicit bulk/pilot authorization.
11. **First pilot:** PRJCA039020/PRJDB36521 is operationally first because it has a small public INSDC mirror, ordinary Illumina BALF reads and two published groups. PRJCA046985 is scientifically first but operationally second until its GSA file list/layout resolves. PRJNA977832 is last because of unresolved mapping and 917-GB production cost.
12. **Strongest likely storyline:** cohort-specific diagnosis or clinical grouping explains bounded and potentially small fractions of lower-airway compositional variation, while dispersion, feature definition and study-specific processing qualify cross-study generalization. This remains a hypothesis until external cohort estimates exist.

## Final verdict

**CONDITIONAL GO**

Proceed to manifest completion and bounded pilots, not bulk production. The project is a multi-cohort or cross-study analysis, never “multicenter” unless a source cohort itself is explicitly multicenter. Primary results remain cohort-specific; cross-cohort synthesis is descriptive without a pooled R².

## Remaining gate before execution

One authorization is required for any raw-read pilot or bulk production. Before that request, exact accessions, group mappings, layouts, checksums, byte totals, host-depletion provenance, batch/control inventories and resource caps must be frozen.
