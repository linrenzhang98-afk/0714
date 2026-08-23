# Recommended cross-cohort execution plan

## Recommendation: Strategy C

Keep PRJNA1056765 and PRJCA046985 internally processed and analyze them independently. Add a common, separately named **native-read Kraken2 classifier-assignment sensitivity layer** by parsing the already-existing native reports. Do not merge the present matrices and do not represent Kraken2 direct assignments as Bracken abundance.

The practical A+C interpretation was considered: match the Kraken2 database, parameters, rank grammar, and denominator (A-like technical harmonization), then retain cohort-specific inference and cross-study synthesis (C). Because the matching Kraken2 runs already exist, this requires read-only derivation rather than biological reprocessing.

## Why not A or B

### Strategy A — PRJCA046985-only anchor reproduction

- Scientific validity: weak for an exact Bracken reproduction. The anchor used Bracken with an omitted `-r` and evidence of the 100-nt redistribution despite nominal ~50-nt reads. PRJCA046985 has mixed 15–50/75-nt files, for which one-summary-length Bracken and ad hoc length-stratified aggregation are rejected.
- Reproducibility: the anchor Kraken2 path is reconstructed, but exact historical Bracken binary identity is not.
- Cost: moderate; avoidable because it creates no defensible common estimator.
- Risk: high estimator/read-length bias plus irreversible upstream host-state difference.

### Strategy B — new common pipeline on both cohorts

- Scientific validity: no clear advantage. Reprocessing cannot restore host reads removed before PRJCA046985 deposition.
- Reproducibility: a new pipeline can be frozen, but inputs remain biologically/technically non-identical.
- Cost: highest (530 samples), with new storage and compute scope.
- Risk: changes the established anchor and introduces a new estimand without eliminating the major source difference.

### Strategy C — cohort-specific effects and common-estimand synthesis

- Scientific validity: strongest. It avoids unsupported Bracken approximation and exposes preprocessing heterogeneity.
- Reproducibility: exact native report membership and Kraken2 parameters are already recorded for both cohorts.
- Cost/time: low; bounded parsing and within-cohort statistics only.
- Risk: batch/read-length/host-state effects remain, but are qualified rather than hidden.
- Cross-cohort claims: permitted only for an explicitly common estimand. The present diagnosis contrasts differ and cannot be collapsed into one generic “lung disease” effect.

## Next bounded stage (not executed here)

1. Freeze a read-only report parser that extracts direct S- and G-rank Kraken2 assigned counts, clade counts separately, unclassified counts, and all-input-read totals.
2. Validate exactly 400 anchor native reports against `anchor_reconciliation_v2.json` and exactly 130 PRJCA046985 reports (8 pilot plus 122 verified production). Never mix in `*_bracken_species.kreport` files.
3. Produce two independent matrices with the same grammar:
   - raw direct-rank assigned counts;
   - direct-rank counts divided by all input reads;
   - explicit zero only for absent taxa in valid reports;
   - failed/missing samples remain missing, not zero.
4. Apply the prospectively frozen 10% within-cohort prevalence threshold, with 5% and 20% sensitivity views. Do not calculate prevalence on a pooled 530-sample matrix.
5. Run community analyses within cohort only. Every PERMANOVA must have a matching PERMDISP. Report classified fraction/read depth alongside diversity.
6. Before formal meta-analysis, define one clinical estimand shared by the cohorts. PRJNA1056765's four-level diagnosis and PRJCA046985's drug-resistance contrast are not the same estimand; absent a shared contrast, restrict output to cohort-specific findings and technical robustness comparison.

No Kraken2, Bracken, trimming, host filtering, or raw-read download is required for this stage.

## Conditional pilot only if future reprocessing is proposed

Full reprocessing is **not recommended now**. If later evidence establishes a scientifically justified common preprocessing/Bracken route, a pilot is mandatory before production. Reuse exactly these eight frozen PRJCA046985 pilot runs:

- CRR2423961
- CRR2424000
- CRR2423957
- CRR2423986
- CRR2423912
- CRR2423921
- CRR2423991
- CRR2424010

Inputs would remain the frozen local FASTQs and hashes under `/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/`. The present anchor reconstruction does **not** support specifying an exact reproducible host-removal command/reference, nor does it support native mixed-length Bracken. Therefore no host-removal or Bracken command is authorized or presented as executable here.

Any future pilot must first close all of these blockers:

1. a verified host-removal tool, reference identity, and parameters that answer the non-reversible external upstream-depletion issue;
2. exact historical Bracken executable/version identity or a prospectively justified replacement common to both cohorts;
3. a validated read-length rule and matching redistribution for every retained read, without ad hoc mixed-length aggregation;
4. resource estimates measured from a synthetic/technical preflight (RAM, wall time, output size, database identity); and
5. a new authorization because this would change the current no-reprocessing plan.

## Other programme cohorts

- PRJCA039020 / CRA024916 / PRJDB36521 remains the next high-priority candidate, but its clinical mapping and 40-nt Bracken compatibility require separate closure.
- PRJNA977832 / SRP440548 remains deferred because of scale and provenance/mapping gaps.
- PRJCA028177 / CRA017789 remains `METADATA_SALVAGE_ONLY`: 127 DNA and 127 RNA libraries are confirmed, but no deterministic case-to-run mapping exists.

Use “multi-cohort,” “cross-cohort,” or “cross-study.” Do not call the programme multicenter without source evidence.
