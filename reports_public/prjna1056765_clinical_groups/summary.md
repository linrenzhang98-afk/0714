# PRJNA1056765 Clinical Group Summary

## Source Interpretation

- Dataset: PRJNA1056765 BALF clinical mNGS.
- Main article: Metagenomic fingerprints in bronchoalveolar lavage differentiate pulmonary diseases.
- Data descriptor: Bronchoalveolar lavage fluid metagenomic datasets: a multidimensional clinical biomolecular resource.
- Published clinical labels were parsed from Supplementary Data S1/S2.

## Analyzed DNA WGS Runs

- Bacterial infection: 114 runs; median classified 1.9034%; median top-pathogen fraction 0.10494; high-confidence runs 26
- Fungal infection: 78 runs; median classified 1.5793%; median top-pathogen fraction 0.02936; high-confidence runs 1
- Lung cancer: 122 runs; median classified 2.0530%; median top-pathogen fraction 0.02913; high-confidence runs 14
- Pulmonary tuberculosis: 86 runs; median classified 1.6587%; median top-pathogen fraction 0.02071; high-confidence runs 1

## Deep-Review Diagnosis Coverage

- Bacterial infection: 14/14 stable same-top calls
- Fungal infection: 1/1 stable same-top calls
- Lung cancer: 10/10 stable same-top calls
- Pulmonary tuberculosis: 5/5 stable same-top calls

## Clinical WGS Runs Not Analyzed

- SRR27343810 (20210709MCX011, Fungal infection), size_MB=0
- SRR27343463 (20211125MCX012, Lung cancer), size_MB=0

## Practical Interpretation

- The current 400-run result is suitable for four-group BALF mNGS re-analysis: Cancer, Bacterial infection, Fungal infection, and Pulmonary tuberculosis.
- The two missing clinical WGS runs have size_MB=0 in RunInfo, so their absence should be reported as unavailable public SRA records rather than analysis failure.
- Next statistical work should compare pathogen spectra across diagnosis groups and validate high-confidence pathogens after host removal/AMR screening.

## Output Files

- `run_clinical_mapping.tsv`
- `diagnosis_summary.tsv`
- `diagnosis_top_pathogen_counts.tsv`
- `deep_review_by_diagnosis.tsv`
- `clinical_wgs_runs_not_analyzed.tsv`
