# PRJNA1056765 Group Differential Summary

## Scope

- Runs analyzed: 400
- Groups: Bacterial infection=114, Fungal infection=78, Lung cancer=122, Pulmonary tuberculosis=86
- Test: species detection in one diagnosis group versus all other groups by two-sided Fisher exact test; BH-FDR reported.
- Abundance metric: Bracken species fraction; medians include zero values.

## Wet-Lab Candidate Targets

- Pseudomonas aeruginosa (Bacterial infection): detect 23/114 vs rest rate 0.02448, FDR 2.48792e-05, tier1_group_enriched, marker oprL or ecfX
- Mycobacterium tuberculosis (Pulmonary tuberculosis): detect 9/86 vs rest rate 0.00000, FDR 0.000533876, tier1_group_enriched, marker IS6110
- Aspergillus fumigatus (Fungal infection): detect 8/78 vs rest rate 0.00932, FDR 0.0332815, tier1_group_enriched, marker ITS or 28S
- Cryptococcus neoformans (Fungal infection): detect 6/78 vs rest rate 0.00621, FDR 0.110067, tier2_suggestive_group_enrichment, marker ITS
- Haemophilus influenzae (Bacterial infection): detect 18/114 vs rest rate 0.05944, FDR 0.260199, tier3_deep_review_case_confirmation, marker hpd
- Candida albicans (Fungal infection): detect 8/78 vs rest rate 0.03727, FDR 1, tier3_deep_review_case_confirmation, marker ITS or ACT1
- Stenotrophomonas maltophilia (Bacterial infection): detect 9/114 vs rest rate 0.03497, FDR 1, tier3_deep_review_case_confirmation, marker smeD or 23S marker
- Staphylococcus aureus (Bacterial infection): detect 7/114 vs rest rate 0.01748, FDR 1, tier3_deep_review_case_confirmation, marker nuc
- Streptococcus pneumoniae (Bacterial infection): detect 20/114 vs rest rate 0.13986, FDR 1, tier3_deep_review_case_confirmation, marker lytA
- Klebsiella pneumoniae (Bacterial infection): detect 5/114 vs rest rate 0.02448, FDR 1, tier3_deep_review_case_confirmation, marker khe or rpoB

## Practical Short-Project Recommendation

- For the shortest publishable wet-lab module, prioritize tier1/tier2 targets: P. aeruginosa, M. tuberculosis, Aspergillus fumigatus, and Cryptococcus neoformans.
- Treat K. pneumoniae, A. baumannii, S. aureus, and Candida albicans as deep-review/case-confirmation targets unless new local samples show stronger group-level separation.
- M. tuberculosis should only be used if the available lab workflow and biosafety approvals are already in place; otherwise keep it as a bioinformatic validation endpoint.
- Use Lung cancer BALF samples as disease controls rather than healthy controls; the public dataset does not provide true healthy BALF controls.
- Report background/low-specificity taxa separately; do not use recurring Homo sapiens, Toxoplasma gondii, or plant taxa as biological findings.

## Output Files

- `group_species_differential.tsv`
- `top_group_enriched_species.tsv`
- `wetlab_validation_candidates.tsv`
