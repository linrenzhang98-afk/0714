#!/usr/bin/env python3
"""Example report generation task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    title = job["params"].get("title", "Analysis Report")

    report = [
        f"# {title}",
        "",
        f"- Job ID: `{job['job_id']}`",
        f"- Task: `{job['task']}`",
        f"- Source result dir: `{job['params'].get('source_result_dir', '')}`",
        "",
        "This is a placeholder report. Replace `scripts/generate_report.py` with your real report builder."
    ]
    (out_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
