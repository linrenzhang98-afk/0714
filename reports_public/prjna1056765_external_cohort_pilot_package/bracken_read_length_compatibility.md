# Bracken read-length compatibility

## Status

**BRACKEN_COMPATIBILITY_UNVERIFIED — EXECUTION STOP**

The frozen PRJCA039020 pilot run, `DRR770839`, has a repository-derived mean read length of 40 nt. The existing project record proves that the hospital workflow used `database100mers.kmer_distrib` with the Kraken2 database at `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`. It does not prove that `database40mers.kmer_distrib` exists, nor does it provide current Kraken2/Bracken versions or a live database hash.

No other legally substitutable installed redistribution file has been verified for the actual 40-nt deposited read length. The 100-mer redistribution is not treated as compatible with 40-nt reads.

The unresolved questions cannot be closed from the stale public status snapshot. A live read-only inventory was not available through the currently visible authorized pathway. Therefore Bracken must stop for this pilot. Kraken2 compatibility by itself does not authorize a partial run presented as a complete classifier pilot.

No database was rebuilt, no redistribution file was generated and no replacement database was downloaded. If the 40-mer file is absent, creating one would constitute a separately authorized database adaptation; this phase does not do so.
