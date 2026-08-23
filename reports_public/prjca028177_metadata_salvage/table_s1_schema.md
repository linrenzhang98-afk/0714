# Table S1 schema audit

Source: `spectrum.01087-24-s0001.pdf`, DOI `10.1128/spectrum.01087-24.SuF1`.
The PDF title is “Table S1：Original data of 127 pediatric patients.” It contains 127 case rows numbered 1–127.

## Exact column headers

Line wrapping from the PDF has been removed, while capitalization, wording, and source typos are retained. There are 17 columns:

1. `Patient`
2. `Underlying diseases`
3. `Age (y=years, m=months)`
4. `Gender（M=Male,F=Female）`
5. `Culture`
6. `mPCR`
7. `MP-IgM`
8. `MP IgG antibody titer`
9. `T-spot`
10. `Acid-fast staining (AFS)`
11. `Galactomannan (GM) test`
12. `Pathogens detected by DNA mNGS (relative abundance,%)`
13. `Pathogens detected by RNA mNGS(relative abundance,%)`
14. `Clinical diagnostic pathogens(Pathogenic considerations)`
15. `RMPP`
16. `MP resistance gene mutations detected by DNA mNGS`
17. `Changed antibiotics (refered results), YES=effective, NO=ineffective）`

## Structured extraction coverage

`table_s1_clinical.tsv` contains the deterministically extractable case number, underlying-disease value, age, sex, and RMPP flag. It also retains a whitespace-normalized source-row text field so that the remaining published values are not silently discarded or assigned to the wrong column when long pathogen narratives wrap across the PDF table.

The following requested fields are **not columns in Table S1**:

- a separate patient/sample identifier beyond the `Patient` case number;
- collection date;
- severe-pneumonia status;
- refractory-pneumonia status (the `RMPP` field means refractory *Mycoplasma pneumoniae* pneumonia, not refractory pneumonia generally);
- hospital stay;
- outcome;
- an mNGS identifier;
- a laboratory sample identifier.

The following requested concepts are present, either directly or as part of a broader source column:

- case number (`Patient`);
- age and sex;
- underlying disease;
- mPCR, MP-IgM, MP IgG antibody titer, and culture;
- clinical diagnostic pathogen;
- RMPP;
- antibiotic adjustment/effectiveness.

Because Table S1 has no archive or laboratory identifier, it does not itself bridge its case numbers to BioSample, Experiment, or Run accessions.
