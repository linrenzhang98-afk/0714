# External lower-airway cohort shortlist

## Decision

Thirteen candidate dataset families were screened. One is conditional priority A and two are priority B. Three additional BAL datasets are reserves; seven are excluded from quantitative replication. The shortlist supports a **conditional** cross-cohort programme, not naive pooling and not a claim of multicentre sampling.

### Conditional A priority

1. **PRJCA046985 / CRA034880, Zhang DR-TB (n=130).** Independent prospective BALF cohort, with drug-resistant versus drug-susceptible TB defined by phenotypic or molecular susceptibility testing. It provides the cleanest externally defined two-group phenotype. The GSA run/file layout and exact data size remain to be verified before pilot. The institutional phrase names one affiliated Xuzhou hospital, but repository provenance still requires confirmation.

### B priority

1. **PRJCA039020 / CRA024916 / PRJDB36521, Luo CAP–severe pneumonia (n=229).** Independent BALF cohort processed with Illumina NextSeq 550. It offers a prespecified severity contrast and rich clinical covariates, but the severe group is only 25 and differs strongly in age, sex, illness severity, and treatment. It estimates severity-associated composition, not the anchor's four-diagnosis estimand.
2. **PRJNA977832 / SRP440548, Tan HIV pulmonary infection (718 public runs; paper n=756).** Large independent BALF cohort contrasting pulmonary infection with and without HIV. Public data are host-depleted 40-bp single-end reads. The 38-sample paper–repository discrepancy and institution mismatch must be resolved before production; the 917-GB footprint makes it the last, not first, pilot.

### Reserve requiring label validation

1. **PRJCA027972 / OMIX006862, Zhang suspected CAP (n=66).** Small but inexpensive paired-platform BALF cohort. The Illumina arm is a practical compatibility smoke test. Clinical group definition needs to be frozen from the supplement and shown independent of mNGS before analysis; Nanopore replicates are technical measurements and cannot increase subject n.

### Reserve

- **PRJNA991321 (28 patients, 56 paired BALF samples):** valid BALF shotgun data but only paired tumour-bearing versus ipsilateral normal lung segments in people with lung cancer. It can test representation-dependent heterogeneity, not diagnosis generalizability.
- **PRJNA603592/573853/603675:** scientifically exemplary paired BAL/oral/controls and functional data, but too small and partly overlapping across associated projects for primary cross-diagnosis synthesis.

### Excluded from quantitative replication

- **PRJCA028177:** 127 pediatric BALF cases but no independent comparator; deriving groups from detected pathogens would be circular.
- **PRJNA979827:** paper n=40, public n=22, with only three noninfectious cases.
- **PRJNA450137:** tracheal aspirate, not BAL/BALF; prior descriptions as BAL are incorrect.
- **PRJEB64676:** predominantly endotracheal aspirate, longitudinal and low-biomass-enriched; valuable context but incompatible primary specimen.
- **PRJNA875913:** tracheal aspirate RNA, not BALF DNA.
- **PRJNA419524:** 13 transplant donor–recipient pairs and WGA virome design.
- **PRJNA1216061:** mixed specimen study; a recoverable BALF subset with individual diagnosis labels has not been established.

## Evidence trail

Primary sources used include the [Zhang DR-TB paper](https://doi.org/10.3389/fcimb.2025.1726935), [Luo CAP/SP paper](https://doi.org/10.3389/fmicb.2025.1538109), [Tan HIV paper](https://doi.org/10.1128/spectrum.00005-23), [Zhang paired-platform CAP paper](https://doi.org/10.3389/fcimb.2022.1021320), [Zhao pediatric paper](https://doi.org/10.1128/spectrum.01087-24), and [Langelier critical-illness paper](https://doi.org/10.1073/pnas.1809700115). Repository counts were checked against NCBI RunInfo or NGDC BioProject pages; discrepancies are retained rather than reconciled by assumption.
