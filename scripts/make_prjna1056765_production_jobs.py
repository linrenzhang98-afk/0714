#!/usr/bin/env python3
"""Create PRJNA1056765 production descriptive batch jobs from candidate table."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create PRJNA1056765 production descriptive jobs")
    parser.add_argument("--candidates", required=True, help="candidate_dna_wgs_runs.tsv")
    parser.add_argument("--out-dir", default="jobs/planned_production_prjna1056765")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--db", default="/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209")
    parser.add_argument("--start-batch", type=int, default=1)
    parser.add_argument("--max-runs", type=int, default=400)
    args = parser.parse_args()

    with Path(args.candidates).open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    rows = sorted(rows, key=lambda r: (float(r.get("size_MB", 0) or 0), r.get("Run", "")))
    rows = rows[: args.max_runs]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    now = datetime.now(timezone.utc)
    for offset in range(0, len(rows), args.batch_size):
        batch_rows = rows[offset : offset + args.batch_size]
        batch_number = args.start_batch + offset // args.batch_size
        job_id = f"{now:%Y%m%dT%H%M%SZ}-prjna1056765-production-descriptive-batch-{batch_number:03d}"
        run_accessions = [row["Run"] for row in batch_rows]
        job = {
            "job_id": job_id,
            "task": "metagenome_sra_kraken2",
            "created_at": now.isoformat(timespec="seconds"),
            "params": {
                "project_name": f"prjna1056765_production_descriptive_batch_{batch_number:03d}",
                "run_accessions": run_accessions,
                "work_dir": f"/mnt/disk1/public_datasets/prjna1056765_production_batch_{batch_number:03d}",
                "output_dir": f"/mnt/disk1/db/kraken2/0714/results/prjna1056765_production_descriptive_batch_{batch_number:03d}",
                "read_type": "single",
                "threads": args.threads,
                "kraken2_db": args.db,
                "bracken_db": args.db,
                "database_mode": "production_first_pass",
                "allow_large_database_download": False,
                "max_failed_fraction": 0.2,
                "max_failed_runs": 10,
                "disk_free_gb_min": 500,
                "auto_decision_level": "safe",
                "analysis_boundary": "descriptive pathogen-spectrum first pass only; no clinical grouping or final biological conclusion",
                "selection_note": "All PRJNA1056765 candidate DNA WGS METAGENOMIC SINGLE runs from production planning table, sorted by size.",
            },
        }
        out_path = out_dir / f"{job_id}.json"
        out_path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        created.append(str(out_path))

    summary = {
        "created_at": now.isoformat(timespec="seconds"),
        "candidate_runs": len(rows),
        "batch_size": args.batch_size,
        "jobs": created,
    }
    (out_dir / "production_job_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
