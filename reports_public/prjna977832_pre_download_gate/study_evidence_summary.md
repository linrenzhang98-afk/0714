# PRJNA977832 / SRP440548 pre-download gate

Study: Tan et al., *Microbiology Spectrum* 2023, DOI `10.1128/spectrum.00005-23`, PMID `37436163`, BioProject `PRJNA977832` / SRA study `SRP440548`.

## Verified paper cohort

The paper reports retrospective BALF mNGS at the First Hospital of Changsha from January 2019 to June 2022. Among 781 reviewed pulmonary-infection patients, exclusions were 17 unknown HIV-status, 6 aged under 18, and 2 pregnant; 756 remained (476 HIV-infected, 280 HIV-uninfected). HIV status was extracted from medical records, so it is an exposure defined independently of mNGS. Pulmonary-infection eligibility, however, was decided by two senior clinicians using clinical presentation, laboratory/imaging and conventional tests **plus positive BALF mNGS and response to antibiotic therapy**. It is therefore not an independent outcome label for microbiome ecology.

BALF DNA was extracted with TIANamp Micro DNA kit. The paper reports library preparation followed by BGISEQ-50/MGISEQ-2000 sequencing, low-quality-read removal, computational human subtraction against hg19 with BWA, and low-complexity removal before PMDB classification. Current SRA metadata instead labels the instrument Illumina NovaSeq 6000; this unresolved platform discrepancy is recorded as a technical-provenance blocker rather than silently harmonized.

## Public inventory result

Current official NCBI RunInfo and ENA read-run reports each contain 718 mutually matching runs/experiments/BioSamples. Every run is SINGLE; 648 have mean length 50 nt and 70 have mean length 40 nt. The 718 distinct BioSamples do not prove 718 distinct people because no participant field is populated. All SRA `Subject_ID`, `Disease`, `Sex`, `Body_Site`, and `Affection_Status` fields are blank.

Sources: [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10434007/), [NCBI BioProject](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA977832), [NCBI RunInfo](https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA977832), and [ENA read-run report](https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA977832&result=read_run&fields=run_accession,experiment_accession,sample_accession,secondary_sample_accession,sample_alias,study_accession,library_name,instrument_model,library_layout,base_count,read_count,fastq_bytes,fastq_md5,fastq_ftp&format=tsv&limit=0). No sequence data were opened or downloaded.
