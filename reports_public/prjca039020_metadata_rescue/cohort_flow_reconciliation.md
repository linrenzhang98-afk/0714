# PRJCA039020 metadata-rescue cohort flow reconciliation

## Evidence status legend

`VERIFIED` means directly stated in a primary paper or represented in the public accession inventory. `SUPPORTED` is consistent with, but does not itself establish, an identity link. `UNRESOLVED` means no auditable public key was found. `CONFLICTING` is reserved for directly incompatible evidence.

## Published and deposited flow

| Transition or claim | Count | Status | Evidence and boundary |
|---|---:|---|---|
| Original pneumonia specimens that underwent mNGS | 243 | VERIFIED | Luo et al., Methods, “Patients and definitions” in the publisher XML for DOI `10.3389/fmicb.2025.1538109`: 243 pneumonia patients retrospectively studied. |
| Original CAP / severe-pneumonia composition | 218 / 25 | VERIFIED | Published cohort-flow fact independently checked against the paper’s reported final exclusion arithmetic: 243 = 218 + 25. |
| Excluded for incomplete clinical data | 14 CAP | VERIFIED | Published cohort-flow fact: 218 original CAP − 204 analyzed CAP = 14; no severe-pneumonia exclusion is reported. |
| Final analyzed cohort | 229 (CAP 204; SP 25) | VERIFIED | Paper Methods and paper clinical tables describe 204 CAP and 25 SP after incomplete-data exclusion. |
| Public accession inventory | 233 | VERIFIED | `public_233_inventory.tsv` has 233 data rows, one `DRR` run with linked `DRX`, `SAMD`, `DRS`, `SAMC`, and `BALF_###` aliases per row. |
| 243 original → 233 public identity mapping | — | UNRESOLVED | No deposited participant identifier, excluded-status field, or paper-to-accession bridge was found in the frozen public metadata. |
| 233 public → 229 final-analysis mapping | — | UNRESOLVED | All 233 inventory rows retain `subject_id=UNRESOLVED` and `published_group=UNRESOLVED`; no accession-order matching was used. |

## Required questions

| Question | Answer | Status |
|---|---|---|
| A. Can all 243 originally sequenced subjects be identified? | No public participant-level list or identity key is available. | UNRESOLVED |
| B. Why are only 233 public? | The ten-record difference is real arithmetic, but no public deposit/exclusion explanation identifies the ten records. | UNRESOLVED |
| C. Which ten original subjects are absent from the public deposit? | Not identifiable from public evidence. | UNRESOLVED |
| D. Which four public records are outside the final 229 analysis? | Not identifiable from public evidence. | UNRESOLVED |
| E. Can every final analyzed patient be linked to run, BioSample, participant, and CAP/SP group? | No; run/BioSample-to-participant and group keys are absent. | UNRESOLVED |
| F. Can CAP=204 and SP=25 be reconstructed exactly at accession level? | No; published totals are verified, but accession-level group membership is not. | UNRESOLVED |

## Hypothesis test

The arithmetic hypothesis—233 public records may be the 229 analyzed patients plus four of 14 excluded CAP records, while ten excluded CAP records were not deposited—is **HYPOTHESIS_NOT_VERIFIED**. It is numerically compatible with the published totals but has no direct sample identity, group, inclusion/exclusion, or repository-status evidence. It was not used to label or exclude any record.

## Conclusion

The 243 → 233 → 229 flow is verified only as aggregate counts. The missing accession-to-subject-to-group bridge is a fatal metadata limitation for a clinical CAP/SP manifest. The permitted next stage is `AUTHOR_CONTACT_REQUIRED`; no raw-read pilot is authorized by this rescue package.
