# Live DeepSeek bounded technical gate v3

**Verdict: APPROVE_BOUNDED_PILOT**

Model: `deepseek-v4-pro`

Review date: 2026-08-21

## Preferred option

Option C, a two-run PRJCA046985 technical smoke pilot using `CRR2423962` at expected 50 nt and `CRR2423909` at expected 75 nt.

## Blocking issues

None for the strictly bounded technical pilot. Raw-read download and execution remain subject to explicit user authorization.

## Scientific and technical rationale

- The full manifest contains 130 unique direct mappings: 81 drug-sensitive and 49 drug-resistant subjects, totaling 2,082,679,760 compressed bytes.
- Pilot file sizes sum exactly to 10,526,255 bytes.
- Expected 50- and 75-nt architectures match installed Bracken 3.0.1 redistribution files. Observed deposited length remains a mandatory pre-Bracken check.
- The input records map directly to supplementary `unhost_reads` records. They must bypass further host filtering.
- Kraken2 2.17.1, Bracken 3.0.1 and the existing database are read-only inputs. No derivative, database rebuild or environment modification is needed.
- Option A cannot validate Bracken because 40-nt redistribution is absent. Option B is a separately approvable future database-derivative task and is unnecessary for this pilot.
- Clinical labels are valid provenance for later cohort planning but irrelevant to this two-run technical pilot. No group comparison or biological inference is permitted.

## Low-risk edits applied after review

- Added both Option C runs to the host-depletion provenance table.
- Defined the exact transfer cap as cumulative across retries and recorded per-run byte expectations.
- Required read-only database use and pre-classification identity recording.
- Defined any mixed or nonconforming read length as a stop-before-Bracken condition.
- Removed wording that could imply that the two-run pilot itself has scientific inferential value.

Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T08-37-02-001Z-62079.jsonl`
