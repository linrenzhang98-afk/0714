# PRJCA028177 / CRA017789 metadata-salvage audit

## Outcome

The public archive verifies 254 distinct libraries/runs: 127 explicitly labelled DNA and 127 explicitly labelled RNA. Table S1 was retrieved and its 127 case rows were extracted. Nevertheless, the cohort cannot be upgraded to a formal run-level external cohort because no deterministic case-to-library identifier bridge was found.

The archive gives one BioSample per library rather than one shared BioSample per biological subject. DNA/RNA sample names are library-specific. Patterns such as neighbouring accessions or adjacent numeric suffixes were not treated as evidence of a pair. Table S1 provides only case numbers 1–127, age, sex, and clinical fields; it provides no archive accession, laboratory sample name, mNGS identifier, or collection date.

The mismatch in sex totals is additional blocking evidence: Table S1 has 67 female and 60 male cases, while each 127-library molecule set has 65 female and 62 male records. Sex is neither sufficient nor fully concordant.

## Counts

- Table S1 cases: 127
- public libraries/runs: 254
- explicit DNA libraries: 127
- explicit RNA libraries: 127
- confirmed DNA/RNA subject pairs: 0
- confirmed case-to-run mappings: 0
- Table S1 underlying-disease cases: 19
- Table S1 RMPP flags: 11
- per-case severe/refractory status: unavailable

## Gate

`CASE_RUN_MAPPING_UNRESOLVED`

Final recommendation: `METADATA_SALVAGE_ONLY`.

The underlying-disease field is an independent clinical candidate at the Table S1 case level, and RMPP is explicitly flagged for 11 cases. Neither can be attached to sequencing runs without an identity bridge. The complete common-MPP membership also cannot be proven independent of mNGS from the combined clinical-diagnosis field.
