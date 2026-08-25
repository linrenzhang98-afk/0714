# Four-figure manuscript architecture

## Figure 1 — Provenance, analytical populations and common observability

- **Scientific question:** What evidence is shared, and what remains cohort specific?
- **Cohorts:** PRJNA1056765 and PRJCA046985, displayed in parallel rather than merged.
- **Panels:** (A) provenance flow from frozen membership to 400 and 130 verified reports; (B) clinical-group counts; (C) classifier/database/parser commonality and upstream-processing differences; (D) descriptive classified-fraction distributions plus species/genus inventory and the 166/45 common-at-10% intersections.
- **Statistical test:** None for cross-cohort classified-fraction levels; descriptive medians and distributions only.
- **Effect size:** Sample counts, classified-fraction medians, intersection/union or Jaccard summaries.
- **Supports:** A verified common classifier grammar and a clearly bounded two-cohort design.
- **Must not support:** Equal pipelines, absolute bacterial burden, one 530-person cohort or multicenter sampling.

## Figure 2 — Anchor four-diagnosis ecological association

- **Scientific question:** How much community variation is associated with published diagnosis among the 400 anchor patients?
- **Cohort:** PRJNA1056765 only.
- **Panels:** (A) Aitchison ordination with four diagnosis groups; (B) PERMANOVA R² and paired PERMDISP result; (C) richness, Shannon and dominance distributions with omnibus effects; (D) forest plot for the three prespecified lung-cancer-versus-each-infectious-diagnosis secondary contrasts if the omnibus gate is met.
- **Statistical test:** Four-level Aitchison PERMANOVA with 9,999 restricted permutations; matching PERMDISP; Kruskal-Wallis with epsilon-squared for alpha metrics; multiplicity-corrected post-omnibus pairwise tests.
- **Effect size:** PERMANOVA R², dispersion summary, epsilon-squared and pairwise rank-biserial or standardized effects with confidence intervals.
- **Supports:** A bounded diagnosis-associated ecological signal and its dispersion/representation qualification.
- **Must not support:** Causal disease effects, diagnostic accuracy, a healthy-versus-disease claim or external replication.

## Figure 3 — External TB drug-resistance ecological association

- **Scientific question:** Is independently documented drug-resistance status associated with BALF community organization among 130 TB subjects?
- **Cohort:** PRJCA046985 only.
- **Panels:** (A) Aitchison ordination by `Drug_Resistance`/`Drug_Sensitive`; (B) PERMANOVA R² with paired PERMDISP; (C) richness, Shannon and dominance effects; (D) technical robustness by nominal 50/75-nt category and classified fraction.
- **Statistical test:** Binary Aitchison PERMANOVA and PERMDISP with 9,999 permutations; Wilcoxon rank-sum or prespecified robust model for alpha metrics; marginal/stratified nominal-length sensitivity.
- **Effect size:** PERMANOVA R², dispersion summary, rank-biserial/Hedges g and confidence intervals.
- **Supports:** A cohort-specific association between independently documented resistance grouping and ecology, if the formal analysis supports it.
- **Must not support:** Resistance-caused dysbiosis, equivalence to the anchor diagnoses, or independent anchor replication.

## Figure 4 — Qualified cross-cohort ecological synthesis

- **Scientific question:** Which ecological properties and taxonomic observability patterns are concordant despite different clinical contrasts?
- **Cohorts:** Both, summarized at cohort/contrast level only.
- **Panels:** (A) side-by-side clinical-group PERMANOVA R² and PERMDISP qualifications; (B) contrast-labelled standardized diversity/dominance effects; (C) species and genus prevalence-set overlap at 5%, 10% and 20%; (D) descriptive prevalence behavior of a small prespecified set of common taxa, or omit this panel if no outcome-independent selection rule is frozen.
- **Statistical test:** No pooled test. Cohort-specific tests retain their own nulls. Overlap is descriptive; any common-taxon sign/rank summary is explicitly exploratory and multiplicity controlled.
- **Effect size:** Cohort-specific R², standardized alpha effects, intersection/union/Jaccard values and contrast-specific prevalence effects.
- **Supports:** Generalizability of ecological measurement and common taxonomic observability across independently analyzed cohorts.
- **Must not support:** A common disease coefficient, formal meta-analysis, replicated taxa, multicenter inference or pooled clinical prediction.

Differential-abundance results, full sensitivity grids, covariate missingness and complete common-taxon tables belong in supplementary material unless a later, explicitly authorized gate elevates a narrowly prespecified result.
