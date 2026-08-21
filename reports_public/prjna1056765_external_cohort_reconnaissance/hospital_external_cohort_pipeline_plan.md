# Hospital workstation plan for external cohorts

Status: design only. No production execution, database change, environment rebuild, service change, or raw-read download is authorized by this document.

## Directory layout

Use `results/external_cohorts/<study_id>/` with `raw_manifest/`, `metadata/raw/`, `metadata/harmonized/`, `qc/`, `taxonomy/`, `community/`, `source_data/`, and `logs/`. Raw reads, if later authorized, should reside on the existing high-capacity read volume referenced by manifest rather than be committed to Git.

## Manifest-first workflow

For each study, version-lock: accession list; BioSample snapshot; subject map; expected layout; expected run/sample/patient counts; file sizes; MD5/ENA checksum when available; repository retrieval date; paper DOI; grouping map; and explicit exclusions. The workflow stops if observed counts, layout, or checksums differ from the locked manifest.

## Download design

- Accession-bounded, resumable retrieval with a per-study allowlist and per-study byte cap.
- Preflight available space at least 1.5 times raw plus temporary estimate; no uncontrolled parallelism.
- Verify repository checksum/size before declaring complete; retain per-file attempt and error logs.
- Stop an accession after three repeat failures and continue the study manifest; never silently substitute another file.

## Pilot authorization and resource envelope

This document does **not** authorize pilot execution. After Gate 3, pilot execution still requires the user's one bulk-execution authorization. Each future pilot manifest must set all of: per-run byte cap, total download cap, minimum free-space requirement, working-space cap, thread cap, memory cap, wall-time stop, and an explicit ban on host filtering unless separately approved. Provisional ceilings are 20 GB per run, 40 GB total per cohort pilot, 16 threads, 128 GB RAM, and 24 wall-clock hours; lower manifest-derived limits take precedence. Exceeding a cap stops the sample without substitution.

## FASTQ QC

Check gzip/FASTQ integrity, mate agreement, read count, layout, read-length distribution, quality summaries, and whether files are already host-depleted. Record host-removal compatibility and low-information flags. No sample is automatically deleted. Host-depleted public data must not undergo a second irreversible host filter without a documented pilot check.

## Taxonomy

Use the anchor cohort's existing frozen Kraken2/Bracken executable and database snapshot if the hospital inventory confirms the same hashes and the reads pass compatibility checks. A single current database improves *within-reanalysis* cross-cohort comparability, even though it will differ from some original papers. It does not erase library, host-depletion, centre, or study effects and cannot be presented as reproduction of original taxonomy. Do not rebuild or update the database in this phase.

Before any pilot, freeze a classifier compatibility record containing executable hashes, Kraken2 database hash/date/taxonomy mapping, parameters and confidence, report format, Bracken version/rank/threshold, and every installed Bracken read-length redistribution file. A read length without a compatible Bracken file is a stop condition, not permission to rebuild a database. Identical taxonomy processing provides procedural consistency only; it is neither batch correction nor biological exchangeability.

## QC boundary

Universal reported metrics are read count, bases, layout, read length, classified fraction, unclassified fraction, human fraction when available, microbial reads, detected features, dominance, zero fraction, and control status. Exclusion thresholds are not transferred automatically across studies. Each cohort retains a primary all-eligible population plus only prospectively approved cohort-specific QC sensitivities. Negative controls are processed as controls and inform contamination interpretation; they are not pooled with biological samples or used to create post-hoc thresholds.

Create a per-cohort control inventory with control material, extraction/library batch match, read depth, accession, and public availability. Controls calibrate only their matched cohort/batch. Missing public controls are reported as a limitation and preclude strong contamination-sensitive claims; they do not trigger a borrowed threshold. Before production, freeze cohort-specific QC criteria and produce diagnosis-by-site, diagnosis-by-batch, diagnosis-by-platform, and diagnosis-by-depletion-provenance cross-tabs without viewing diagnosis-associated community results.

## Community analysis and synthesis

Generate one species matrix per cohort, prevalence summaries, prespecified CLR/Aitchison analysis, Bray comparator, PERMANOVA, PERMDISP, effect-size estimates and cluster diagnostics only where sample size/grouping supports them. Cohort outputs remain separate. Cross-cohort work begins from a cohort-level estimate table and produces a forest-style descriptive summary, dispersion-status table, feature-space robustness comparison, and cluster-stability comparison. Raw abundance matrices are not concatenated for the primary test.

## Safety and audit checks

Preflight existing disk, CPU, memory, Kraken2/Bracken versions, database hash, and host reference without modification. No sudo, systemd, services, large dependency install, or database download. Execution requires a separate bulk authorization after the pilot manifests pass Gate 3.
