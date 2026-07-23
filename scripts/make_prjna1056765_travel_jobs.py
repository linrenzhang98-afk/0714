#!/usr/bin/env python3
"""Create PRJNA1056765 travel-mode batch jobs from SRA RunInfo CSV."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create PRJNA1056765 metagenome travel jobs")
    parser.add_argument("--runinfo", required=True, help="SRA RunInfo CSV")
    parser.add_argument("--out-dir", default="jobs/planned_metagenome")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--max-runs", type=int, default=30)
    parser.add_argument("--max-size-mb", type=int, default=250)
    parser.add_argument("--min-size-mb", type=int, default=1)
    parser.add_argument("--db", default="/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    selected: list[dict[str, str]] = []
    with Path(args.runinfo).open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                size_mb = float(row.get("size_MB", "0") or 0)
            except ValueError:
                continue
            if row.get("LibraryStrategy") != "WGS":
                continue
            if row.get("LibrarySource") != "METAGENOMIC":
                continue
            if row.get("LibraryLayout") != "SINGLE":
                continue
            if "DNA" not in row.get("LibraryName", "").upper():
                continue
            if not (args.min_size_mb <= size_mb <= args.max_size_mb):
                continue
            selected.append(row)

    selected.sort(key=lambda r: float(r.get("size_MB", "0") or 0))
    selected = selected[: args.max_runs]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    now = datetime.now(timezone.utc)

    for batch_index in range(0, len(selected), args.batch_size):
        batch = selected[batch_index : batch_index + args.batch_size]
        batch_number = batch_index // args.batch_size + 1
        job_id = f"{now:%Y%m%dT%H%M%SZ}-prjna1056765-travel-batch-{batch_number:03d}"
        run_accessions = [row["Run"] for row in batch]
        job = {
            "job_id": job_id,
            "task": "metagenome_sra_kraken2",
            "created_at": now.isoformat(timespec="seconds"),
            "params": {
                "project_name": f"prjna1056765_travel_batch_{batch_number:03d}",
                "run_accessions": run_accessions,
                "work_dir": f"/mnt/disk1/public_datasets/prjna1056765_travel_batch_{batch_number:03d}",
                "output_dir": f"/mnt/disk1/db/kraken2/0714/results/prjna1056765_travel_batch_{batch_number:03d}",
                "read_type": "single",
                "threads": args.threads,
                "kraken2_db": args.db,
                "bracken_db": args.db,
                "database_mode": "pilot",
                "allow_large_database_download": False,
                "max_failed_fraction": 0.2,
                "max_failed_runs": 10,
                "disk_free_gb_min": 500,
                "auto_decision_level": "safe",
                "selection_note": f"DNA WGS METAGENOMIC SINGLE; size {args.min_size_mb}-{args.max_size_mb} MB; sorted by size.",
            },
        }
        out_path = out_dir / f"{job_id}.json"
        out_path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        created.append(str(out_path))

    summary = {
        "created_at": now.isoformat(timespec="seconds"),
        "selected_runs": len(selected),
        "batch_size": args.batch_size,
        "jobs": created,
    }
    (out_dir / "selection_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
