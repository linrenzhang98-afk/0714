# ETYY GitHub-mediated compute architecture

WSL/Codex is the sole Git writer. ETYY is compute-only. WSL must not SSH to
ETYY, mount `/mnt/disk1`, or copy databases/FASTQ files. The legacy checkout at
`/mnt/disk1/db/kraken2/0714` is never repaired or used as Git control state.

Run [bootstrap_etty_control_runner.sh](../scripts/bootstrap_etty_control_runner.sh)
once manually on ETYY. It creates the clean control clone at
`/mnt/disk1/0714_control/repo`, configures an exact one-job glob, performs a
zero-command dry-run, and executes only the authorized pilot if all preflight
checks pass. The runner runs under `mgshotgun` without `--no-pull`, so GitHub is
the control transport. Outputs persist under `/mnt/disk1/0714_handoff/`.

For this frozen pilot only, the bootstrap detaches the execution clone at
`03cff4d403bcb1ab0d87848a0b22b06762345070` and uses `--no-pull` for both dry-run
and execution after the revision freeze. The permanent GitHub-mediated design
is unchanged.

The old `etty_remote_job.sh` is retained only as a failing deprecation stub.
