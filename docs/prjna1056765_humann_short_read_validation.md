# PRJNA1056765 HUMAnN 3.9 short-read validation route

This repository route is bounded to `SRR27343495` and `SRR27343566`, the most
compositionally separated non-smoke pair in the checked-in 30-sample Bray–Curtis
matrix (distance 0.9967198031881912). `SRR27343490` remains the completed smoke
test and is never an output target.

The exact cohort authority is
`reports_public/metagenome_standard_shotgun/species_relative_abundance_matrix.tsv`:
the runner requires exactly 30 unique rows and exact membership equality with
the host/AMR run status. It refuses any membership drift.

Each Bracken fraction is multiplied by 100 for the HUMAnN/MetaPhlAn profile
percent unit. Taxa pass only when abundance is strictly greater than `0.01`,
preserving HUMAnN's prescreen semantics. Profiles have the HUMAnN-3.9-compatible
four fields `#clade_name`, `NCBI_tax_id`, `relative_abundance`, and
`additional_species`. Names and taxids come directly from Bracken. Converting
spaces to underscores is profile serialization only; no unmatched name is
looked up, guessed, or silently remapped.

The explicit `--taxonomic-profile` route bypasses MetaPhlAn raw-read prescreening.
No MetaPhlAn read-length option is changed. Preflight requires the existing
HUMAnN 3.9, Bowtie2 2.5.5, DIAMOND, ChocoPhlAn, and UniRef90 paths and never
installs, downloads, updates configuration, or mutates an environment.

Two reference modes are prepared per validation sample:

- joint union: the strict-threshold union across all 30 Bracken profiles;
- sample specific: that sample's strict-threshold Bracken profile.

HUMAnN documents `--bypass-nucleotide-index` as starting at nucleotide alignment
with the already indexed database supplied by `--nucleotide-database`. The first
joint-union run therefore builds its custom index normally; reuse for the second
joint-union sample is allowed only from that run's single temp directory after a
complete six- or eight-shard Bowtie2 index check. Sample-specific references are
different inputs and are never cross-reused. The execution plan records exact
commands and observed tool versions.

On the hospital workstation, preparation and read-only tool/database preflight:

```bash
python3 scripts/run_prjna1056765_humann_short_reads.py --preflight
```

Execution is an explicit separate action:

```bash
python3 scripts/run_prjna1056765_humann_short_reads.py --execute
```

Do not add sample IDs or release the remaining cohort without user approval.
Prepared/planned state is not downstream validation evidence; results may be
reported only after workstation outputs actually exist and pass review.

Reference: [official HUMAnN workflow documentation](https://github.com/biobakery/humann#workflow-by-bypass-mode).
