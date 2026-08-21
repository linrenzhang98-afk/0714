# Live DeepSeek Gate 1: cohort shortlist

Date: 2026-08-21
Model: `deepseek-v4-pro`
Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-20T16-05-15-476Z-32895.jsonl`

## Verdict

**CONDITIONAL GO**

DeepSeek retained PRJCA046985 as conditional A. It demoted PRJCA039020 and PRJNA977832 from A to B and PRJCA027972 from B to reserve pending proof that its clinical labels are independent of mNGS. It confirmed exclusion of tracheal-aspirate, RNA-only, virome/WGA, incomplete, and non-comparator datasets.

## Blocking conditions before production

- Resolve run–sample–subject and site provenance for PRJCA046985.
- Resolve the four extra public BioSamples for PRJCA039020 and treat its CAP/severe contrast as a covariate-imbalanced severity estimand.
- Reconcile 718 public runs with paper n=756, public HIV labels, institution provenance, and batches for PRJNA977832.
- Demonstrate a prespecified clinical label independent of mNGS for PRJCA027972.

No cohort combination supports the term *multicenter*. Dual accessions and paired platforms are duplicate representations of one cohort, not independent cohorts. Selection is a metadata-availability shortlist, not a representative sample of all lower-airway studies.

## Low-risk corrections applied

Priority categories and candidate/exclusion counts were corrected; duplication and terminology warnings were made explicit. No biological or statistical analysis was run.
