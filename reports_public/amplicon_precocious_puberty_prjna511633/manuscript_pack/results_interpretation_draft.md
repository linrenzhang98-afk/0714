# PRJNA511633 Results Interpretation Draft

Generated at: 2026-08-14T13:21:34+00:00

## Analysis Status

- The current analyzable dataset is the reverse-read DADA2 result.
- The summary includes 48 samples: 23 healthy controls and 25 ICPP samples.
- A rarefaction depth of 10000 reads is defensible for primary diversity analysis; 5000 reads retains all 48 samples and 10000 reads retains 47 samples.

## Core Findings

- Alpha diversity is consistently higher in ICPP across Shannon diversity, observed features, and evenness.
- shannon: control median 4.29763, ICPP median 5.30847, q=6.92341e-06.
- observed_features: control median 57, ICPP median 117, q=2.31145e-06.
- evenness: control median 0.715062, ICPP median 0.797282, q=0.00095994.

## Genus-Level Signals

- [Ruminococcus]_gnavus_group: lower in ICPP, delta=-0.0198, q=0.0390868
- Agathobacter: higher in ICPP, delta=0.0176, q=0.0390868
- [Eubacterium]_coprostanoligenes_group: higher in ICPP, delta=0.0071, q=0.0390868
- Ruminococcus: higher in ICPP, delta=0.0181, q=0.0431643

## Conservative Interpretation

- The public-data result supports an association between ICPP and altered fecal microbial diversity/composition.
- The analysis should not claim causality or diagnostic performance without independent validation.
- Species-level outputs should be framed as exploratory because the dataset is 16S V3-V4 rather than shotgun metagenomics.
