#!/usr/bin/env python3
"""Example allowlisted analysis task.

Replace this demo with your real analysis logic. Keep the CLI stable:
  script.py --job path/to/job.json --out path/to/output_dir
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = json.loads(job_path.read_text(encoding="utf-8"))
    params = job["params"]
    dataset_path = Path(params["dataset_path"])

    summary = {
        "job_id": job["job_id"],
        "task": job["task"],
        "dataset_path": str(dataset_path),
        "exists": dataset_path.exists(),
        "rows": 0,
        "columns": [],
        "group_counts": {}
    }

    if dataset_path.exists():
        with dataset_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            summary["columns"] = reader.fieldnames or []
            group_col = params.get("group_col")
            for row in reader:
                summary["rows"] += 1
                if group_col and group_col in row:
                    key = row.get(group_col, "")
                    summary["group_counts"][key] = summary["group_counts"].get(key, 0) + 1

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "README.md").write_text(
        "# Demo metabolomics analysis\n\n"
        f"- Job: `{job['job_id']}`\n"
        f"- Dataset exists: `{summary['exists']}`\n"
        f"- Rows: `{summary['rows']}`\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
