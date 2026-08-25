# Cross-cohort scientific question

## Frozen evidence boundary

The analysis universe is 400 unique PRJNA1056765 BALF DNA runs and 130 unique PRJCA046985 BALF DNA runs. Every run has one valid native Kraken2 report in the verified common classifier-assignment layer. The cohorts remain separate analytical populations. No pooled 530-sample matrix, common diagnosis variable, multicenter claim, or formal meta-analysis is justified.

The cohort audit uses `reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv`, `reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv`, the frozen harmonization decision, and the successful GitHub handoff commit `029f500` (`matrix_validation.json`, resolver verification, summary and result). No ETYY filesystem was accessed.

## Strongest defensible manuscript question

**Across two independently assembled lower-airway shotgun cohorts, how much do the prespecified clinical groupings explain within-cohort microbial community organization when measured with the same Kraken2 direct-assignment grammar, and which ecological and taxonomic properties are observable in both cohorts without asserting a shared disease effect?**

This question supports a comparative ecological architecture, not a disease-signature replication manuscript.

## What each layer means

1. **Cohort-specific clinical association.** PRJNA1056765 estimates the omnibus association of four published diagnoses with BALF community composition. PRJCA046985 estimates the association of independently documented TB drug-resistance status with BALF community composition. These are the primary biological questions and are estimated separately.
2. **Cross-cohort ecological generalizability.** The same ecological concepts—composition, diversity, dominance, prevalence, explained community variance and dispersion—can be evaluated in both cohorts. Similar behavior means ecological concordance under different clinical contrasts, not replication of one disease effect.
3. **Cross-cohort technical comparability.** Database identity, classifier version/parameters, report grammar, direct-count definition and parser are aligned. Input read architecture and upstream host state are not identical, so cohort differences in absolute classifier yield are descriptive technical evidence only.
4. **Taxonomic overlap and prevalence structure.** The verified layer contains 5,198 anchor and 4,888 external species taxids, with 166 species at at least 10% prevalence in both; the corresponding genus counts are 1,633, 1,496 and 45. These counts define a shared observable inventory. They do not establish equal abundance, equal biology, or absence of cohort-specific detection bias.
5. **Genuine replication.** Replication would require another cohort with the same clinical exposure/contrast, comparable eligibility and specimen collection, deterministic labels, a compatible feature-generating process, and a prespecified effect in the same direction with compatible uncertainty. Neither current cohort replicates the other's clinical contrast.
6. **Concordant ecological behavior.** Similar directions in diversity or dominance, comparable bounded PERMANOVA R² values, similar dispersion qualifications, or shared prevalent taxa are concordant behavior. These observations can strengthen generalizability of the ecological framework while remaining non-replicative.

## Claims permitted and rejected

Permitted claims are that published diagnosis is associated with community structure within PRJNA1056765, that drug-resistance status is associated with community structure within PRJCA046985 if supported by formal analysis, and that a common classifier-assignment layer permits qualified comparison of ecological behavior and taxonomic observability.

Rejected claims include a single 530-person disease effect, independent multicenter replication, causal effects of diagnosis or resistance, absolute bacterial burden from classified fraction, and formal meta-analysis of the two clinical coefficients.

## Unit, identity and missingness audit

- PRJNA1056765 has 400 unique runs, patient IDs, BioSamples and library IDs: bacterial infection 114, fungal infection 78, lung cancer 122 and pulmonary tuberculosis 86. Core run, diagnosis, published training/test split and collection-date fields are complete. The 400 dates span 2021–2023. Two additional clinically mapped records with zero-size SRA entries are outside the frozen 400-run universe. No repeated subject or technical replicate is identified among the 400.
- PRJCA046985 has 130 unique DNA runs, subjects, BioSamples and experiments: `Drug_Resistance` 49 and `Drug_Sensitive` 81. The labels are bridged from Supplementary Table S3 and derive from phenotypic or molecular drug-susceptibility evidence, not the microbiome output. One DNA run per subject is present; 130 RNA records are excluded by modality. No repeated subject or technical replicate is identified.
- Demographics, recent antibiotics, treatment history, disease severity and comorbidities are not available as frozen run-linked covariates for both cohorts. They must not be invented or reconstructed from taxonomic output.
