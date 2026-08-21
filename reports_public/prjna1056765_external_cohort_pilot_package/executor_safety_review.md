# Final executor-safety review

## Status artifact resolution

`stalled_status_generation_failed` is a fallback literal embedded in `scripts/publish_status_to_github.sh`. It is written only if the generic progress-governor generator fails to create its status files. It is not the current state and is not emitted by the bounded external-pilot path.

The current hospital-originated status was generated on 2026-08-21 at 16:53:12 +08:00. It reports `progress_state=public_data_submission_ready`, `runner_return_code=0`, and both `status_md_exists=true` and `status_json_exists=true`. The current general-runner status also records `metagenome_deep_review_allowlisted=true`, `jobs_glob=jobs/*.json`, and the expected hospital results root. Therefore the phrase is an inactive generic-publisher fallback, not a current runner failure.

## Dispatch and frozen scope

- The existing allowlisted task is `metagenome_deep_review`, dispatched to `pipelines/metagenome_deep_review_runner.py`.
- That runner explicitly accepts `execute_mode=bounded_external_pilot`.
- The job contains exactly `CRR2423962` and `CRR2423909` and exactly 10,526,255 cumulative authorized bytes.
- Both entries must be `HOST_DEPLETED`; host filtering is explicitly false and no host-filter command exists in the bounded path.
- Both 50- and 75-nt redistribution files are resolved for existence before any download begins.

## Enforced limits

- Each Kraken2 and Bracken child receives a non-privileged `RLIMIT_AS` of 64 GiB. A watchdog additionally observes resident memory and terminates the child on a reported cap breach. No sudo, cgroup or systemd change is used.
- Workspace size is checked before download, on every download chunk, before Kraken2, during Kraken2, before Bracken, during Bracken and between runs. The cap is 5 GB.
- All commands use the remaining common eight-hour deadline. The watchdog terminates a child when the total deadline is exhausted.
- Response URL and Content-Length are checked before body transfer. Each chunk is charged to one cumulative budget shared across attempts and runs before it is written. Partial failed transfers remain charged, so retries cannot exceed 10,526,255 bytes.
- Any mixed or unexpected read length stops the run before Kraken2/Bracken. The observed length must be exclusively 50 nt or 75 nt for the respective frozen run.

## Publisher boundary

The bounded publisher copies only the technical summary, database identity, redistribution inventory, Kraken reports, Bracken tables and logs. It does not publish FASTQ, modify scientific outputs, add accessions or trigger further analysis. This bounded addition does not resolve or redefine the broader production-checkout branch-divergence model.
