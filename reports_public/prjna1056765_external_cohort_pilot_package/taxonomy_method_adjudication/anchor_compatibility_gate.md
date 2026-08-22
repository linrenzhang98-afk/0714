# Stage C DeepSeek anchor compatibility reconciliation gate

OVERALL = INSUFFICIENT_EVIDENCE

Model: `deepseek-v4-pro`

Mode: thinking / high reasoning

Review date: 2026-08-22

1. **Is anchor-side compatibility sufficiently established? No.** Artifact and ledger accessibility, software provenance and database provenance are established, but the native-report membership and representative actual invocation records are not persisted in the review package.
2. **Are the existing native reports admissible now? No.** Their existence is `VERIFIED_PROVENANCE`, but admission requires the suffix/path-classified native inventory to match the frozen 400-run anchor membership. The combined 1124-file count is not admissible as a native count.
3. **Is an anchor rerun unnecessary? Yes.** The original reports and ledgers remain accessible. No Kraken2 or Bracken rerun is justified.
4. **Is database identity sufficient? Yes, at provenance level.** The stable path, historical jobs, 2022 core-file timestamps, manifest identity, `opts.k2d`/`taxo.k2d` hashes and redistribution hashes are sufficient for this bounded sensitivity decision. A new SHA-256 of the approximately 16-GB `hash.k2d` is not required.
5. **Is the PRJCA046985 pilot authorized? No.** No pilot manifest is frozen and no pilot may launch until the remaining record is reviewed.
6. **Exactly one remaining evidence item:** a persisted ETYY-derived reconciliation record containing both (a) the suffix/path-classified native `*.kreport` inventory tied to all 400 frozen PRJNA1056765 runs and separately counting `*_bracken_species.kreport`, and (b) representative original production Kraken2 `args` records extracted from the per-batch `command_log.jsonl` files.

The one record is the smallest decision-changing item because it simultaneously proves which original artifacts are the native classifier reports and that their actual invocations match the frozen command provenance. It requires read-only inspection only. Frozen v5 remains unchanged.
