# Live DeepSeek manifest and pilot gate

**Verdict: DO_NOT_RUN**

Model: `deepseek-v4-pro`
Live audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T04-37-39-959Z-51086.jsonl`
Review completed: 2026-08-21

## Findings

- PRJCA039020 contains 233 exact public runs but no direct accession-to-subject-to-CAP/severe mapping. `DRR770839` is the exact median-size run and is frozen only as a technical candidate.
- The deposited-file host state is unresolved.
- Existing project evidence confirms use of `database100mers.kmer_distrib`; it does not establish a matching 40-nt Bracken redistribution.
- CRA034880 has a direct 130-subject mapping through the GSA alias and Supplementary Table S3: 49 `Drug_Resistance` and 81 `Drug_Sensitive`.
- PRJNA977832 has 718 public runs versus 756 eligible paper participants, lacks an accession-linked HIV map and remains metadata-only.

## Blocking issues

1. Obtain accession-level documentary evidence for the deposited-file host-depletion state of `DRR770839`.
2. Verify an existing 40-nt Bracken redistribution matching the exact Kraken database and installed Bracken version. Do not build one under this phase.
3. Complete a live read-only workstation inventory of executable versions/hashes, database identity, redistribution files, free disk, CPU and RAM.
4. CAP/severe mapping remains blocked for any biological use. It is not required for a strictly technical pilot after the execution blockers close.

No raw reads were downloaded and no hospital, database or environment state was changed.
