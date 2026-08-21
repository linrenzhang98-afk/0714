# Technical blocker resolution summary

## Outcome

The earlier `DO_NOT_RUN` state has been superseded by the verified live hospital inventory and the bounded A/B/C technical review. Raw-read execution remains unauthorized pending the live DeepSeek re-gate.

1. **Bracken compatibility:** `BRACKEN_40NT_REDISTRIBUTION_ABSENT`. Installed lengths are 50, 75, 100, 150, 200, 250 and 300 nt. A 50-nt file is not an accepted substitute for 40-nt reads.
2. **Host provenance:** `DRR770839` is classified `RAW` based on the paper's explicit raw-deposit statement and pipeline ordering. Wet-lab Benzonase treatment is recorded separately. The 40-nt versus ≥70-bp workflow discrepancy remains a required pilot inspection item.
3. **Hospital inventory:** `READ_ONLY_INVENTORY_COMPLETE`. ETYY has Kraken2 2.17.1, Bracken 3.0.1, 32 logical threads, approximately 119 GB available RAM and approximately 2.96 TB free project storage. The database path is `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`.
4. **PRJCA039020:** `TECHNICAL_PILOT_ONLY`; direct CAP/SP mapping remains unresolved.
5. **PRJCA046985:** scientifically preferred with direct DR/DS mapping, but technically not ready.

No raw FASTQ, new database, redistribution file, environment, service or biological analysis was created or run.
