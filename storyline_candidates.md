# Storyline candidates for PRJNA1056765

## Decision frame

These directions are judged against the two original publications, not against the frozen draft. “New method” is not equated with “new biology.” The same 402-patient source cohort cannot externally validate itself, and the 400 downloadable DNA runs are not an independent cohort.

## A. Compositional robustness and heterogeneity

**Central question.** How much lower-airway microbial variation is explained by published diagnosis after compositional, dispersion, sparsity, and low-information safeguards?

**Novelty.** Moderate methodological and interpretive novelty. The original paper reported significant Bray–Curtis disease separation and discriminatory taxa. The frozen analysis adds a full-available-cohort Aitchison result with small effect size, paired PERMDISP, strict-QC sensitivity, sparsity-aware taxon reporting, and a negative cluster-stability result. The key new message is not “diagnoses differ”; it is “the apparent disease signal is small, metric-dependent, and does not form stable community types.”

**Relationship to the original publication.** Direct reanalysis and robustness audit of the same cohort. It qualifies rather than independently confirms Han et al. It must reproduce the original feature space/sample split closely enough to distinguish methodological differences from data-processing differences.

**Strongest evidence now.** Aitchison diagnosis R²=0.0194 with no full-cohort dispersion evidence; Bray R²=0.0153 with PERMDISP p=0.0013; only three of five sparse taxa survive strict QC; Bray/Aitchison clustering agreement is approximately zero; 281/400 runs carry prespecified low-information/QC flags.

**Missing evidence.** Exact reconciliation with the original processed matrices, training split, feature inclusion, negative controls, and database versions. Uncertainty estimates and a prospectively frozen sensitivity grid remain desirable.

**Minimum additional analysis.** Reproduce headline original DNA results using the authors’ released processed matrix and group files; pre-register a small sensitivity grid; report effect sizes/uncertainty; test whether cohort/date and classified fraction materially alter the diagnosis estimate. This is new analysis and therefore must wait for user direction.

**Optional analysis.** Variance partitioning with a few independent, sufficiently complete covariates. No new clustering search and no classifier.

**New dataset requirement.** Not mandatory for a transparent reanalysis/audit paper, but an independent compatible BAL cohort would materially strengthen generalizability.

**Estimated time.** 1–2 weeks for the minimum analysis and an audit-style manuscript package, assuming released matrices map cleanly.

**Main reviewer risk.** “This is a method-driven reanalysis of a recently published dataset with limited biological novelty.” Other risks are inconsistent upstream classifiers/databases and overclaiming a correction when pipelines differ.

**Likely manuscript strength.** Moderate as a focused reproducibility/compositional caution paper; weak if marketed as new disease ecology.

**Decision: CONDITIONAL GO.** Proceed only with an audit-first title/question, exact original-pipeline reconciliation, and explicit acknowledgment that biological disease association and taxa were already published.

## B. Oral–lung ecological continuum

**Central question.** Can cross-disease BALF variation be organized by an independently defined oral-associated ecological signal rather than discrete disease-specific microbiome subtypes?

**Novelty.** Potentially moderate biological novelty in this large cross-disease BALF cohort. Oral enrichment and SPT/BPT ecology are not new concepts, and Han et al. already called P. micra and P. gingivalis oral/airway commensals. What could be new is testing a prospectively external oral reference signal as a continuous axis across cancer, bacterial/fungal infection, and TB, while showing that diagnosis explains little and clusters are unstable.

**Relationship to the original publication.** A reinterpretation of the same taxonomic data, not a new discovery cohort. It shifts the explanatory axis from diagnosis to source ecology. It must not be built from P. micra, P. gingivalis, F. nucleatum, P. endodontalis, and C. rectus simply because they were significant here.

**Biological plausibility.** Strong precedent supports microaspiration, mouth–lung similarity, and oral-taxa-associated lower-airway inflammation. However, PRJNA1056765 has no paired oral samples, no measured aspiration, no bacterial-load assay, and no direct inflammatory assay in the frozen taxonomy analysis. Oral-like BAL composition could reflect immigration, impaired clearance, infection, treatment, sampling carryover, or laboratory signal.

**Strongest evidence now.** The five frozen diagnosis-associated taxa are oral-associated; diagnosis explains only a small proportion of composition; no stable discrete ecotypes were found. This motivates the question but cannot define or validate the oral signal.

**Missing evidence.** A prospective taxon/reference definition; released negative-control assessment; construct validation in paired oral–BAL data; robustness to classified fraction, date, and diagnosis; preferably an independent host RNA or inflammatory correlate.

**Minimum additional analysis.** Before outcome testing, lock an external oral-reference rule based on primary paired oral/BAL studies or an independent reference database. Verify it distinguishes oral samples from background/negative controls in external/released data. Then test the continuous signal in PRJNA1056765 with compositional and QC safeguards.

**Optional analysis.** Validate the construct in PRJNA326122 or the Sulaiman airway datasets; relate it to one prespecified, non-duplicative host RNA endpoint if patient-level mapping and technical validity are adequate.

**New dataset requirement.** Not mandatory for derivation if the reference is entirely external, but external paired oral–BAL data are strongly recommended for construct validation. A disease-matched external cohort is unlikely to be readily compatible.

**Estimated time.** 2–4 weeks for reference curation, construct validation, and minimum analyses; longer if raw external data require reprocessing.

**Circular-analysis risk.** High unless the reference set, weighting, exclusions, and thresholds are frozen before examining diagnosis associations. Using the five significant taxa, tuning a score to maximize PERMANOVA, or naming a cluster “oral” after inspection is disallowed.

**Main reviewer risk.** No paired oral samples, no absolute load, and no aspiration measure. Reviewers may view the continuum as a post-hoc relabeling of the same published taxa.

**Likely manuscript strength.** Potentially moderate-to-strong if externally defined and independently validated; weak without construct validation or an orthogonal host/functional correlate.

**Decision: CONDITIONAL GO.** Scientifically more interesting than a pure audit, but only after a prospective external definition and validation gate. Otherwise NO-GO.

## C. Functional or active microbiome

**Central question.** Can paired DNA taxonomy and public RNA/metatranscriptomic or host data support a distinct, prespecified question about microbial activity rather than taxonomic presence?

**Novelty.** Unclear. Han et al. already analyzed RNA microbial composition, host pathways, immune-cell estimates, transposable elements, CNV, and multimodal models. Tang et al. released RNA microbial and host-expression resources. A generic DNA–RNA comparison, disease pathway screen, or classifier would overlap substantially.

**Relationship to the original publication.** Very close. Any new analysis must target a question Han et al. did not answer and must use an independent endpoint. Sulaiman et al. show that DNA, inferred function, and metatranscriptome can disagree and that activity claims are stronger when connected to measured metabolites.

**Strongest evidence now.** The cohort has matched DNA/RNA at source and public processed RNA/host resources. The frozen selected-30 analysis proves only that the subset is biased: it enriches high-classification, highly dominated samples, misses a major community state, has annotation dropout, and shows dispersion-sensitive functional structure.

**Missing evidence.** Cohort-wide microbial RNA QC, patient mapping, negative-control behavior, RNA/DNA normalization strategy, a distinct biological endpoint, and external validation. There are no measured microbial metabolites in PRJNA1056765.

**Minimum additional analysis.** Metadata/code audit only, followed by a written, prospective single-question protocol. A plausible example is whether an externally defined oral signal shows excess RNA relative to DNA and a prespecified host-response correlate. That remains conditional because it may duplicate original RNA findings and relative RNA/DNA is not a direct activity rate.

**Optional analysis.** Validate assay behavior in Sulaiman’s PRJNA603592/PRJNA573853/PRJNA603675 resources, recognizing their small healthy-smoker cohort is construct validation, not clinical replication.

**New dataset requirement.** Strongly recommended. Independent paired WGS/metatranscriptome plus metabolite or host outcome would be needed for a strong activity/mechanism paper.

**Estimated time.** 3–8 weeks after protocol approval; potentially much longer for raw cohort-wide functional processing.

**Main reviewer risk.** Near-duplication of Han et al.; conflating RNA detection with viable activity; depth/annotation/dispersion artifacts; selected-subset bias; pathway fishing.

**Likely manuscript strength.** Weak with current frozen evidence; potentially strong only with a sharply distinct question and orthogonal validation.

**Decision: NO-GO now.** Do not expand HUMAnN to 400. Reconsider only if the metadata/code audit yields a clearly non-overlapping, externally anchored DNA–RNA question.

## External dataset reconnaissance

This is metadata-level only; no bulk reads were downloaded.

| Accession/resource | Human lower-airway material | Modality and size | Natural use | Compatibility judgment |
|---|---|---|---|---|
| PRJNA603592, PRJNA573853, PRJNA603675 | Upper airway, BAL, background controls from Sulaiman et al. | 16S, WGS, metatranscriptome; 21 recruited/19 adequate RNA | Validate whether an externally defined oral signal corresponds across DNA and RNA and differs from background | Best construct-validation option; too small and clinically different for four-disease replication. |
| PRJNA326122 | Whole/acellular BAL, proximal airway wash, oral wash | 16S; 74 experiments | Validate an oral-source/continuum definition and sampling-compartment behavior | Strong anatomical construct validation, but not shotgun and not disease-matched. |
| phs000633 | BAL plus supraglottic samples | 16S; 29 asymptomatic subjects | Validate SPT/BPT logic and oral–inflammation framework | Controlled-access and not shotgun; scientifically relevant but operationally slower. |
| PRJNA230031 / GSE52791 | BAL from HIV-infected pneumonia patients | 16S; 60 Ugandan cases plus comparison cohort described by study | Test portability of an oral-source ecological score in pneumonia | Phenotype and geography differ substantially; not a natural replication of cancer/TB/fungal/bacterial comparisons. |
| PRJNA450137 | BAL from critically ill adults with suspected LRTI | Metatranscriptomic; study-level clinical cohort | Validate host–microbe diagnostic or activity methods | Useful functional precedent; clinical target and assay differ. Do not pool with PRJNA1056765. |
| PRJCA007286 / CRA008928 | Human BALF lower respiratory infection | DNA mNGS; 41 clinical samples plus mock/technical samples in the validation study | Technical validation of shotgun pathogen profiling and controls | Sample size modest and focused on diagnostic assay performance, not oral ecology. |
| PRJNA636842 | BALF low-biomass workflow study | 16S/microbiome benchmarking | Test extraction/low-biomass sensitivity concepts | Technical validation only; not biological replication. |
| PRJNA1225930 | BALF from early COPD | Raw reads; approximately 2 Gb project total | Potential independent BAL disease ecology check | Metadata currently sparse and likely 16S/amplicon-scale; phenotype incompatible with the four original groups. |
| EGAD50000002144 | Sputum and BAL from cystic fibrosis | Short- and long-read shotgun; 127 samples; controlled access | Functional/technical respiratory metagenomics | Mixed specimen, CF-specific, controlled, and released in 2026; not a natural validation cohort for the current question. |

**External-data decision.** Do not force a multi-cohort disease meta-analysis. The best near-term external use is construct validation for an oral–lung signal in paired upper/lower-airway datasets. No identified public cohort naturally replicates the same four diagnostic groups with comparable human BALF shotgun data and adequate metadata. The original public RNA data are complementary modalities from the same patients, not external validation.

## Comparative verdict

| Direction | Novel scientific unit | Current evidence | Key gate | Verdict |
|---|---|---|---|---|
| A. Robustness/heterogeneity | Quantify how little diagnosis explains after appropriate safeguards | Strong, frozen, but same cohort | Exact reconciliation with original processed data | CONDITIONAL GO |
| B. Oral–lung continuum | Independently defined continuous source-ecology axis across diseases | Plausible but not yet tested prospectively | External definition and construct validation | CONDITIONAL GO; preferred if gate passes |
| C. Functional/activity | Distinct paired DNA–RNA question with orthogonal evidence | Insufficient; fixed-30 biased | Non-overlap with Han plus independent endpoint | NO-GO now |
