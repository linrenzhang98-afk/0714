# Pulmonary fibrosis microbiome review: meta-analysis candidate note

Recorded: 2026-08-23

## Review source

Jiang M, Xu H, Qiu J, et al. *The pulmonary microbiome: unlocking mechanistic insights and novel therapeutic horizons in pulmonary fibrosis.* npj Biofilms and Microbiomes. Published 2026-08-19. DOI: 10.1038/s41522-026-01136-y.

This is a review and does not itself contribute a new sequencing cohort. Its value for the ongoing lower-airway multi-cohort programme is methodological and as a pointer to reusable primary datasets.

## Mechanistic themes worth carrying into cross-cohort synthesis

The review emphasizes pulmonary microbiome dysbiosis, increased bacterial burden, altered microbial metabolites, epithelial injury, immune-metabolic reprogramming, and signaling changes in pulmonary fibrosis.

For the current cross-study programme, these themes should be translated into measurable, cohort-level estimands rather than treated as evidence for one universal disease-associated taxon.

Candidate common estimands/methodological targets:

- alpha diversity / richness / evenness;
- beta-diversity effect size and dispersion;
- community dominance / dysbiosis;
- microbial burden proxies, with explicit caution that shotgun classified fraction is not absolute bacterial load;
- taxon prevalence structure;
- cohort-specific differential taxa followed by cross-study consistency assessment;
- function/pathway-level metrics when genuinely comparable functional profiles exist;
- host-response / clinical-covariate integration where source cohorts provide those variables.

Do not pool non-equivalent clinical contrasts into one common disease effect.

## High-priority primary WGS dataset identified through this literature trail

Knudsen KS, Husebø G, Nielsen R, et al. *Whole genome sequencing of the pulmonary microbiome in interstitial lung disease subtypes.* Respiratory Research. 2025;26:324. DOI: 10.1186/s12931-025-03404-5.

### Cohort

Protected BAL (PBAL), total n=157:

- IPF: n=12
- sarcoidosis: n=34
- unclassifiable ILD: n=11
- healthy controls: n=100

WGS platform: Illumina NovaSeq.

This cohort is potentially valuable because it contains 100 lower-airway healthy controls, which are uncommon in public shotgun studies.

### Published analysis pipeline / methods

Published study used GAIA 2.0 for microbial classification. GAIA applies mapping-based taxonomic assignment with best-alignments plus a Lowest Common Ancestor approach against a custom database derived from NCBI BLAST nt.

Published filtering/statistics included:

- species retained only when supported by at least 2 reads in at least 2 samples;
- human sequences handled within the GAIA output by removal of taxa under Chordata rather than by a demonstrated pre-classification human-reference depletion step;
- alpha diversity on rarefied data: Observed, Chao1, Shannon, Gini-Simpson;
- beta diversity: Bray-Curtis + PCoA;
- PERMANOVA adjusted for age, sex, and smoking status;
- differential abundance: DESeq2 v1.38.3;
- CLR values calculated with `mia`;
- taxon-based Dysbiosis Index (DI) constructed from DESeq2 differential species;
- Youden's J used to select a DI discrimination cut-point.

### Methodological value for our programme

1. The DI concept is worth preserving, but for external validation the feature set/weights should be frozen in a discovery cohort before evaluation in an independent cohort to avoid data leakage.
2. PERMANOVA effect size should be paired with dispersion assessment; P values alone are insufficient.
3. Alpha-diversity, dominance/dysbiosis and dispersion are plausible common ecological estimands across clinically non-identical cohorts.
4. Published GAIA outputs should not be naively merged with Kraken2/Bracken matrices. If raw reads become available, prefer reprocessing through the selected harmonized pipeline or retain this cohort for cohort-specific effect estimation followed by cross-study synthesis.

## Meta-analysis programme status

Current anchor and priority external cohorts remain:

- anchor: PRJNA1056765 (~400 BALF shotgun runs);
- external: PRJCA046985 / CRA034880 (n=130; production Kraken2 completed and technical QC done, harmonization pending);
- next priority: PRJCA039020 / CRA024916 / PRJDB36521 (n≈229);
- large deferred candidate: PRJNA977832 / SRP440548;
- metadata-only reserve: PRJCA028177 / CRA017789 until a deterministic case-to-run identity bridge is obtained.

The ILD WGS cohort above should be added as a candidate for a future availability/provenance audit before inclusion.

## Inclusion rule for later synthesis

Do not call the programme a multicenter study unless the source evidence supports multicenter sampling. Preferred wording: multi-cohort / cross-study / cross-cohort.

Do not directly pool raw abundance matrices across incompatible pipelines or different biological contrasts. Preferred strategy is:

1. harmonize preprocessing/taxonomy where scientifically and operationally justified;
2. estimate effects within each cohort;
3. synthesize only genuinely common estimands;
4. use random-effects meta-analysis only when the same estimand and comparable contrast can be defined across cohorts;
5. otherwise report structured cross-study generalizability rather than a pooled disease effect.

## Pending action

Before this ILD WGS cohort enters the formal candidate set, perform a dedicated public-data availability/provenance audit covering raw-read availability, exact sample/run mapping, host-depletion provenance, sequencing layout/read length, metadata completeness, and compatibility with the harmonized Kraken2/Bracken framework.
