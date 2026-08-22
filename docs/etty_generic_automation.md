# Generic ETYY bounded automation

Jobs are reviewed, explicitly `authorized`, and pinned to a commit before ETYY pulls
them. A source manifest contains only allowlisted HTTPS URLs, destination paths,
expected byte counts and a cumulative cap. `scripts/etty_bounded_job.py` validates
the manifest, streams downloads into `.part` files, verifies bytes, atomically renames,
and records restart-safe state. Commands are argv arrays (never shell strings), with
reviewed executable/version and resource limits. Only small allowlisted metadata may
be published to `etty-handoff`; ETYY never writes `main` and the legacy publisher is
not used. Project-specific manifests and validators supply domain rules; this module
contains no scientific assumptions.
