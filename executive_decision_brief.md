# Executive decision brief

## Decision

A scientifically distinct manuscript may exist, but the current taxonomy-led disease story does not. Han et al. already published alpha/beta diversity, disease-associated microbial taxa, the key taxa P. micra, P. gingivalis, and F. nucleatum, RNA microbial results, host pathways, and diagnostic modeling in the same 402 patients. Tang et al. then released the same cohort’s matrices, controls, RNA resources, and code. The frozen 400-run analysis therefore cannot claim an independent cohort, new disease fingerprints, new biomarkers, or new oral taxa.

The strongest completed contribution is a restrictive one: diagnosis explains little of composition; the Bray result is dispersion-confounded; taxon findings are sparse and partly QC-sensitive; and clustering does not support stable ecotypes. This can support a transparent compositional robustness/reproducibility paper if exact differences from the original pipeline are reconciled.

The most scientifically interesting direction is an oral–lung ecological continuum, but it is not yet earned. The five significant taxa cannot define the score. The oral reference must be selected and locked from independent paired oral/lower-airway literature or data before testing PRJNA1056765. It then needs negative-control/QC checks and preferably construct validation in paired upper/lower-airway datasets. Without those safeguards it is post-hoc relabeling and should be rejected.

The functional/activity direction is not ready. The selected 30 HUMAnN samples are biased and cannot represent the 400. The original paper already covers RNA microbial, host, and multimodal analyses. Cohort-wide HUMAnN expansion would add compute before establishing a distinct question. Activity or mechanism would require an orthogonal endpoint and ideally external paired DNA/RNA evidence.

## Supervisor red-team findings

- Novelty inflation blocked: the main biology and diagnostic claims are already published.
- Circular oral score blocked: significant taxa from this dataset cannot define the hypothesis tested in the same dataset.
- P-hacking blocked: no threshold sweep, cluster search, or pathway screen should be used to rescue a positive story.
- Biomarker/mechanism language blocked: the data do not establish clinical validation, aspiration, viability, inflammation, or causality.
- Forced integration blocked: no identified external dataset naturally matches the four diagnoses, BALF, shotgun method, and metadata well enough for automatic pooling.
- Unnecessary computation blocked: no HUMAnN expansion and no new classifier at this gate.

A live DeepSeek control session was not active during this audit. The requested DeepSeek challenge criteria were therefore applied as an explicit red-team gate by the executor and are documented above; no claim of live DeepSeek review is made.

Recommended storyline: Oral–lung ecological continuum, **conditional** on a prospectively external oral-reference definition, control/QC validation, and independent paired upper/lower-airway construct validation.

Alternative: Compositional robustness and heterogeneity as a focused reproducibility/audit manuscript centered on small effect size, dispersion confounding, sparse QC-sensitive taxa, and absence of stable ecotypes.

No-go storyline(s): Disease-specific taxonomic fingerprints; P. micra/P. gingivalis/F. nucleatum novelty; diagnostic modeling in the same split; current functional/active-microbiome manuscript; expansion of the selected-30 HUMAnN analysis.

Why: These claims substantially overlap Han et al.; method changes do not create biological novelty; the oral story is currently vulnerable to circularity; and functional evidence is biased, overlapping, or lacks an independent activity endpoint.

Minimum next analysis: After direction selection, either (1) lock and validate an external oral-reference construct before any PRJNA1056765 outcome test, or (2) exactly reproduce/reconcile the original processed DNA analysis and run a prospectively frozen compositional/dispersion/QC sensitivity grid.

Estimated time: Oral–lung direction 2–4 weeks for the minimum gate; robustness direction 1–2 weeks; functional direction not authorized and not estimated for execution.

**ASK_USER: Choose the manuscript direction before any new analysis: oral–lung continuum (conditional preferred), compositional robustness/heterogeneity (alternative), or stop/no-go.**
