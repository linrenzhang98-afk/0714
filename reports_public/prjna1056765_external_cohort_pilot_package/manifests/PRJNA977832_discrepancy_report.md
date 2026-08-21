# PRJNA977832 discrepancy report

The paper reports 781 screened patients and 756 eligible patients: 476 HIV-positive and 280 HIV-negative. The public BioProject currently exposes 718 runs, 718 experiments and 718 unique BioSamples. Therefore 38 paper participants have no identifiable one-to-one public run under this BioProject. No duplicate BioSample occurs among the 718 runs, but subject identifiers are absent, so distinct BioSamples cannot be proven to represent distinct patients.

The public records contain no HIV field and the article supplement is an aggregate patient-characteristics table, not an accession key. Consequently, run-to-HIV-group mapping is **unresolved** and no 718-run subset can be assigned by filename, library number or ordering.

Repository metadata names the submitting centre as Zhongnan Hospital, Wuhan University. The paper describes retrospective BALF collection at the First Hospital of Changsha and lists both institutions among author affiliations. This is a provenance discrepancy, not evidence of a multicentre cohort.

The runs are single-end NovaSeq records: 648 have mean length 50 nt and 70 have mean length 40 nt. The 70 filenames include `unhost`; many 50-nt filenames include `nonhuman.nonspike`. These filename signals are not accepted as proof of deposited-file processing. File-level host-depletion provenance remains unresolved pending an explicit repository or submitter statement.

Exact ENA compressed total: 504,633,902,336 bytes (504.634 GB decimal). No raw-read retrieval is authorized. Status: **METADATA_ONLY**.
