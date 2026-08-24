# PRJCA039020 pre-analysis evidence summary

## Scope and identity

| Claim | Status | Evidence |
|---|---|---|
| PRJCA039020 / CRA024916 / PRJDB36521 are cross-registrations of one cohort, not independent cohorts | VERIFIED | `external_cohort_reconnaissance.tsv`; `external_cohort_executive_brief.md` |
| Luo et al. reports BALF shotgun DNA on Illumina NextSeq 550 | VERIFIED | `external_cohort_reconnaissance.tsv`; `PRJCA039020_pilot_readiness.md` |
| Paper cohort is 229 patients: CAP 204, severe pneumonia 25 | VERIFIED | `external_cohort_reconnaissance.tsv` |
| Public accession layer contains 233 runs/BioSamples | VERIFIED | `manifests/PRJCA039020_exact_manifest.tsv` (233 rows); `manifest_closure_summary.json` |
| One deposited run is one clinical subject/sample | SUPPORTED, not individually linked | Submitted aliases are BALF_001–BALF_233, but no public key joins them to paper clinical rows. |
| The four public records beyond paper n=229 have a defined role | UNRESOLVED | Prior frozen exclusions record explicitly says they are unidentifiable from public evidence; accession order was not used. |
| CAP/severe labels can be assigned to public runs | UNRESOLVED | Every frozen manifest row has `subject_id=UNRESOLVED`, `published_group=UNRESOLVED`, and `pilot_biological_eligibility=NO`. |

## Readiness implications

The deposit is a real, single BALF shotgun cohort and may be evaluated as a cohort-specific severity-associated community question. It cannot support a biological CAP-versus-severe analysis, a frozen clinical manifest, or a raw-read biological pilot until a traceable public or author-supplied key reconciles run/BioSample, participant, inclusion/exclusion status, and published group.

The existing metadata also records raw deposited reads, wet-lab Benzonase before extraction, and downstream SNAP-to-hg38 in the paper workflow. That is relevant to future technical compatibility, but no raw data or biological processing is performed in this gate.

## Evidence boundaries

No accession order, file size, sequencing order, or group-count arithmetic was used to select 229 records or assign four extras. No raw files, report contents, or biological results were inspected.
