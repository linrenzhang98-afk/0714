# ETYY remote-compute architecture

WSL/Codex is the sole Git writer. ETYY is compute-only and must never commit,
rebase, reset or push. WSL must not mount or copy ETYY database or FASTQ files.

`scripts/etty_remote_job.sh` requires an exact full Git commit and job JSON. It
requires a clean WSL tree and BatchMode SSH, archives the exact commit,
transfers only the bundle to `/mnt/disk1/0714_handoff/executions/`, executes
under ETYY's `mgshotgun` environment, and retrieves only small handoff files.
ETYY evidence belongs under `/mnt/disk1/0714_handoff/`, never only `/tmp`.

The runner CLI is:

`python pipelines/metagenome_deep_review_runner.py --job JOB_JSON --out OUT_DIR`

Use `--preflight-only` before execution. The wrapper fails closed on dirty WSL
state, SSH failure, missing database, missing handoff directory or non-ETYY
hostname.
