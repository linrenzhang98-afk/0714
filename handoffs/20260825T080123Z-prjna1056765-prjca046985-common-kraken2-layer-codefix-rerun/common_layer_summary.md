# Common native Kraken2 classifier-assignment layer

Status: **VERIFIED**

- Layer: `COMMON_NATIVE_KRAKEN2_CLASSIFIER_ASSIGNMENT_LAYER`
- Anchor: PRJNA1056765, 400/400 valid native reports
- External: PRJCA046985, 130/130 valid native reports
- Primary matrices: direct S/G assignments; clade counts were parsed and validated separately, never substituted
- Fractions: direct assignments divided by all input reads (primary) and by classified reads (retained sensitivity)
- Prevalence: 5%, 10%, and 20% calculated separately within each cohort
- Bray-Curtis: cohort-specific 10% species layer; PERMANOVA paired with PERMDISP (999 permutations)
- Pooled 530-sample matrix: not created
- Formal meta-analysis ready: no; clinical contrasts differ

Species taxa: anchor 5198, external 4888, common at 10% 166.
Genus taxa: anchor 1633, external 1496, common at 10% 45.

Classified fraction is technical classifier behavior and is not bacterial load. Diversity metrics are computed from the direct-species subcomposition and remain sensitivity/ecological descriptors. No supervised dysbiosis index was trained; such a model requires discovery, a frozen specification, and external validation.
