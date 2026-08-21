# Hospital live read-only inventory

## Status

**READ_ONLY_INVENTORY_COMPLETE**

The existing GitHub-mediated hospital pathway verified the following state without modifying the workstation:

- hostname: `ETYY`
- user: `suma`
- project: `/mnt/disk1/db/kraken2/0714`
- Kraken2: 2.17.1
- Bracken: 3.0.1
- database: `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`
- logical threads: 32
- RAM: approximately 127 GB total and 119 GB available
- free project disk: approximately 2.96 TB
- installed Bracken read lengths: 50, 75, 100, 150, 200, 250 and 300 nt
- 40-nt redistribution: definitively absent

The inventory did not supply a database content hash, exact taxonomy hash, file sizes for redistribution files, CPU model or current load. These remain `NOT_REPORTED`, not inferred.

No direct SSH, sudo, service action, environment change, database change or data processing was used.
