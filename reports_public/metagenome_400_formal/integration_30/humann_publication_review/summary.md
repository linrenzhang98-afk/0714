# Fixed-30 HUMAnN publication-grade sensitivity review

This is a selected deep-review functional supplement, never 400-run functional inference.

- UniRef90 uses all 30 samples, prevalence ≥20% (809 features), with 10% and 30% sensitivity ordinations. Pathogen-group PERMANOVA/PERMDISP uses 9,999 permutations but remains exploratory because groups were derived from taxonomy.
- Six samples have zero biological MetaCyc pathways: SRR27343518, SRR27343520, SRR27343522, SRR27343601, SRR27343742, SRR27344041. SRR27344041 has two technical rows (UNMAPPED/UNINTEGRATED), not a header-only file. SRR27343296 is the prespecified extreme-sparse case.
- MetaCyc is compared at n=30, n=24 and n=23 using one fixed prevalence-filtered feature set. 101 pathways retain the same top group and BH q<0.05 at n=23. Signals that disappear are annotation-detectability-driven and are not biological conclusions.
- Gene-family group FDR hits: 635; pathogen-abundance × gene-family association FDR hits: 739. These are hypothesis-generating within the selected 30 only.
