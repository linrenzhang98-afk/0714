# Live DeepSeek Gate 3: final go/no-go

Date: 2026-08-21
Model: `deepseek-v4-pro`
Audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-20T16-13-31-730Z-35539.jsonl`

## Final verdict

**CONDITIONAL GO to manifest completion and bounded pilots only. NO-GO for bulk production or cross-cohort scientific claims until blockers clear.**

### Cohort disposition

- Conditional A: PRJCA046985 / CRA034880.
- B: PRJCA039020 / CRA024916 / PRJDB36521; PRJNA977832 / SRP440548.
- Reserve: PRJCA027972 / OMIX006862; PRJNA991321; PRJNA603592/573853/603675.
- Exclude from quantitative replication: PRJCA028177, PRJNA979827, PRJNA450137, PRJEB64676, PRJNA875913, PRJNA419524, PRJNA1216061.

### Resource envelope

Conditional A plus B cohorts require an estimated 1.084–1.452 TB raw storage, 1.95–3.30 TB temporary working storage, 350–700 GB final retained output, and 1,820–5,600 CPU-hours. These are reservation ceilings.

### Pilot order

1. PRJCA039020/PRJDB36521 after resolving four extra BioSamples and freezing labels.
2. PRJCA046985 after exact GSA DNA manifest and file properties resolve.
3. PRJNA977832 only after public/paper counts, labels, provenance, depletion and Bracken compatibility resolve.
4. PRJCA027972 only as an optional Illumina reserve; skip if it adds no information.

### Scientific conclusion

There are conditionally enough data for a descriptive cross-study SCI if at least two external cohorts clear mapping and label gates. There are not enough comparable estimands for a common disease-effect, pooled-abundance or formal R² meta-analysis paper. The strongest prospective storyline is that prespecified clinical groupings explain bounded, potentially small community variation, while dispersion, representation, host depletion and study-specific processing qualify generalization. This remains a hypothesis, not a result.

DeepSeek vetoed *multicenter* framing, pooled primary matrices, pooled R², convenience-based inclusion, duplicate counting, and full processing of the 917-GB cohort before its incremental scientific value is established.
