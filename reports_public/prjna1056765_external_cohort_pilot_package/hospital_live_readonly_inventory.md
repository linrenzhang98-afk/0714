# Hospital live read-only inventory

## Status

**READ_ONLY_INVENTORY_UNAVAILABLE**

The visible authorized project pathway provides a versioned status snapshot generated on 2026-08-15, not a live shell or a current inventory endpoint. That snapshot confirms the established executable paths for Kraken2 and Bracken, the database path, and completed use of a 100-mer Bracken redistribution. It does not expose current hostname, user, executable versions/hashes, database content identity, complete redistribution-file inventory, free disk, CPU, memory, active load or directory writability.

No new runner task, service change, remote shell, production directory or system configuration was created merely to force access. The two pre-existing unrelated local modifications to `reports_public/platform_status.md` and `reports_public/metagenome_deep_review_summary/summary.md` were not used as live evidence and were not modified.

Before any raw-read execution, the existing hospital pathway must produce a current read-only snapshot containing:

- `hostname`, `id -un`, current time and Python/runtime;
- `kraken2 --version`, `bracken -v`, resolved paths and executable hashes;
- database path, stable file inventory/hash/date and taxonomy files;
- all `database*mers.kmer_distrib` names, sizes and supported ranks;
- `df` for the 0714 and candidate work filesystems;
- CPU model/logical threads, memory availability and safe current load;
- a read-only parent-path/writability assessment for a later pilot directory.

This missing live snapshot remains an execution blocker.
