# Methods wording support

| Proposed manuscript wording | Supporting sources | Boundary to retain |
|---|---|---|
| “Species counts were treated as compositional and analyzed through log-ratios.” | Aitchison 1982; Gloor et al. 2017 | Sequencing compositionality does not identify biomass or solve confounding. |
| “Zeros were handled using exact zCompositions 1.6.2 CZM before closure and CLR.” | Palarea-Albaladejo & Martín-Fernández 2015; package documentation | State the exact call; do not claim all zeros are sampling zeros or approximate CZM. |
| “Euclidean distance in CLR space was used as Aitchison distance.” | Aitchison 1982 | The feature set is a classifier-defined subcomposition. |
| “Group-associated multivariate variation was tested by PERMANOVA with restricted permutations.” | Anderson 2001 | The permutation exchangeability structure must match the frozen split. |
| “Every PERMANOVA was paired with a test of multivariate dispersion.” | Anderson 2006 | PERMDISP qualifies location interpretation; nonsignificance is not proof of identical distributions. |
| “ANCOM-BC2 was reserved for multigroup exploratory DA, with ALDEx2 as a compositional sensitivity.” | Lin & Peddada 2024; Fernandes et al. 2014 | Method agreement and adequate covariates/controls are not guaranteed. |
| “Direct sequencing provides a modality-specific view of lower-airway ecology.” | Sulaiman et al. 2021 | That study does not validate the current clinical effects. |
| “Sparse taxon claims require caution in low-biomass respiratory specimens.” | Salter et al. 2014 | Lack of controls prevents declaring a given taxon contaminant or genuine. |

Avoid claiming that CLR is a universal cure, that CZM recovers true absent organisms, that PERMANOVA proves centroid separation without dispersion assessment, or that either source-cohort paper independently verifies the reanalysis.
