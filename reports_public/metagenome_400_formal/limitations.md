# Limitations

- This is formal inference for the complete 400-run *available public production cohort*, not an unqualified population estimate. Two mapped WGS records had no downloadable reads (`size_MB=0`).
- Kraken2/Bracken results and the compact checked-in matrix were reused; raw reports were not reprocessed. Database composition and false assignments remain measurement limitations.
- Very low classified fractions make absolute microbial signal uncertain in some samples. No sample was deleted; flagged-sample sensitivity is reported.
- Diagnosis is an independent published clinical label. Dominant pathogen labels and community states are abundance-derived and cannot independently validate differential taxa.
- Genus is inferred from the first token of species labels and is a sensitivity view, not a separately rerun Bracken genus estimate.
- CLR pseudocount, prevalence filtering, clustering and taxon networks are analytical choices. CLR associations are compositional hypotheses, not ecological interactions or causality.
- The fixed 30 deep-review samples were selected for pathogen-focused review. Their HUMAnN/AMR results are functional exploration only and cannot represent the full 400-run functional landscape.
