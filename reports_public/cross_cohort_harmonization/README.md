# PRJNA1056765–PRJCA046985 shotgun harmonization audit

This is a read-only reconstruction of the committed pipelines and completed ETYY handoffs. No FASTQ was read or downloaded and no classifier, abundance estimator, trimmer, or host-removal tool was run.

## Decision

The current matrices are **not directly mergeable**. PRJNA1056765's checked-in primary matrix is a Bracken species fraction matrix subsequently stripped of six background labels and closed to unit sum. PRJCA046985 currently has native Kraken2 reports/output only. In addition, the anchor classifier received locally unfiltered native SRA reads, whereas PRJCA046985's deposited files are linked to upstream `unhost_reads` records whose exact host-removal tool and reference were not recovered.

The recommended strategy is **C**: preserve each cohort, derive the already-frozen native-read Kraken2 classifier-assignment layer from existing reports without rerunning Kraken2, analyze cohorts independently, and synthesize only genuinely common estimands. The frozen PRJNA1056765 Bracken v5 analysis remains its primary analysis; the Kraken2-only layer is a separately named sensitivity layer.

Strategy A was considered but rejected as an exact matrix-harmonization route: PRJCA046985 contains variable-length reads and native mixed-length Bracken is not validated. Strategy B was considered but rejected because reprocessing both cohorts would not recover an identical pre-host-removal starting point and would change a much larger frozen anchor without a demonstrated scientific advantage. An A+C variant—matching the common Kraken2 layer while retaining cohort-specific inference—is already subsumed by Strategy C and does not require classification reruns.

## Evidence hierarchy

The most important evidence is:

- `reports_public/prjna1056765_external_cohort_pilot_package/taxonomy_method_adjudication/anchor_reconciliation_v2.json`
- `reports_public/prjna1056765_external_cohort_pilot_package/taxonomy_method_adjudication/anchor_compatibility_record.json`
- `pipelines/metagenome_sra_kraken2_runner.py`
- `reports_public/production_planning/prjna1056765/candidate_dna_wgs_runs.tsv`
- `reports_public/metagenome_production/bracken_species_fraction_matrix.tsv`
- `scripts/analyze_prjna1056765_metagenome_400.py`
- `reports_public/prjna1056765_external_cohort_pilot_package/hospital_runner_inventory/hospital_readonly_inventory.json`
- `reports_public/prjna1056765_external_cohort_pilot_package/hospital_read_length_audit/read_length_audit_summary.json`
- `origin/etty-handoff:handoffs/20260822T120000Z-prjca046985-native-kraken2-pilot/{provenance.json,pilot_summary.json}`
- `origin/etty-handoff:handoffs/20260823T043904Z-prjca046985-122-native-kraken2-production-qc/{result.json,production_qc.json}`

Repository paths in the TSV files are citations to committed evidence. Handoff citations name the remote branch and immutable job path; their contents were read without accessing ETYY.

## Scope notes

- “Host removal not performed” refers to local processing immediately before the recorded classifier command. PRJCA046985 deposited files have high-confidence upstream host-depleted provenance; this is a non-reversible cohort difference.
- Classified fraction is technical classifier behavior, not a biological result.
- The 30-sample host-removal/fastp/HUMAnN work is a separate selected subset and is not evidence that the primary 400-run matrix used those steps.
- PRJCA028177 / CRA017789 remains `METADATA_SALVAGE_ONLY`: 127 DNA and 127 RNA libraries are confirmed, but no deterministic case-to-run bridge exists.
