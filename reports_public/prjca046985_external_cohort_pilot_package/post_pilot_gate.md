# PRJCA046985 formal post-pilot gate

**Verdict: CONDITIONAL_GO**

The 8-run native-read Kraken2-only pilot completed successfully with all runs returning exit code 0, consistent database identity and provenance, and resource usage within available limits. Technical execution is sound. However, the pilot did not explicitly record Kraken2 confidence and minimum-hit-groups parameters, relying on defaults, which must be pinned to ensure the same common sensitivity estimand is reproducible at expanded scale. Host filtering and trimming were not performed, but this is consistent with the native-read Kraken2-only method and does not affect the assessment.

## Conditions

- Explicitly specify and document Kraken2 --confidence and --minimum-hit-groups parameters (or confirm that defaults are intentionally used and identical to pilot defaults) in the expanded-scale run configuration.
- Maintain identical Kraken2 version, database manifest identity, and input read processing (native reads, no host filtering/trimming) unless a separate method validation is performed.
- Use pilot resource metrics (136 seconds wall time for 8 samples, ~15.7 GB peak RAM per run, ~20 MB output per run) to plan compute and storage for expanded scale.

Production remains blocked in this task.
