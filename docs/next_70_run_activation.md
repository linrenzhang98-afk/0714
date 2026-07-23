# Next 70-Run Activation

The 30-run pilot completed successfully. The authorized travel scope allows expanding `PRJNA1056765` to at most 100 DNA WGS metagenomic runs.

## Generate Additional Planned Jobs On Linux

Use the existing RunInfo CSV:

```bash
cd /mnt/disk1/db/kraken2/0714
conda activate mgshotgun

python scripts/make_prjna1056765_travel_jobs.py \
  --runinfo /mnt/disk1/public_datasets/prjna1056765_metadata/runinfo.csv \
  --out-dir jobs/planned_metagenome_100 \
  --batch-size 10 \
  --max-runs 100 \
  --max-size-mb 250 \
  --threads 4
```

The first three batches overlap with the completed 30-run pilot. Activate only batches 004-010.

## Activate One Batch At A Time

Example for batch 004:

```bash
cp jobs/planned_metagenome_100/*batch-004.json jobs/
python runner/runner.py --config runner/config.local.json --no-pull
bash scripts/publish_status_to_github.sh
```

Check:

```bash
cat results/*batch-004/summary.json
column -t -s $'\t' results/*batch-004/run_status.tsv
```

Proceed to the next batch only if the previous batch is `done` or has acceptable failures under policy.

## Stop Conditions

Stop and wait for review if:

- Any batch has more than 20% failed runs.
- More than 10 runs fail in one batch.
- Disk free space drops below 500 GB.
- A database or required command is missing.
- GitHub status cannot be pushed repeatedly.
