#!/usr/bin/env python3
"""Publish compact status for the metagenome deep-review run_plan execution."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def process_alive(pid_path: Path) -> tuple[bool, str]:
    if not pid_path.exists():
        return False, ""
    pid = pid_path.read_text(encoding="utf-8", errors="replace").strip()
    if not pid.isdigit():
        return False, pid
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False, pid
    return True, pid


def tail_text(path: Path, limit: int = 40) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish deep-review run status")
    parser.add_argument("--result-dir", default="results/20260731T000000Z-prjna1056765-metagenome-deep-review-plan")
    parser.add_argument("--out-dir", default="reports_public/metagenome_deep_review_run")
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = read_tsv(result_dir / "selected_runs.tsv")
    kraken_dir = result_dir / "kraken2_confirm"
    qc_dir = result_dir / "qc"
    alive, pid = process_alive(result_dir / "deep_review_run.pid")
    log_tail = tail_text(result_dir / "deep_review_run.log")

    rows: list[dict[str, str]] = []
    for row in selected:
        run = row.get("run", "").strip()
        if not run:
            continue
        fastp_json = qc_dir / f"{run}.fastp.json"
        kreport = kraken_dir / f"{run}.kreport"
        bracken = kraken_dir / f"{run}.bracken"
        if bracken.exists():
            status = "bracken_done"
        elif kreport.exists():
            status = "kraken2_done"
        elif fastp_json.exists():
            status = "qc_done"
        else:
            status = "pending_or_running"
        rows.append(
            {
                "run": run,
                "pathogen_group": row.get("pathogen_group", ""),
                "top_pathogen": row.get("top_pathogen", ""),
                "status": status,
                "fastp_json": str(fastp_json) if fastp_json.exists() else "",
                "kreport": str(kreport) if kreport.exists() else "",
                "bracken": str(bracken) if bracken.exists() else "",
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    fields = ["run", "pathogen_group", "top_pathogen", "status", "fastp_json", "kreport", "bracken"]
    with (out_dir / "run_status.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "generated_at": utc_now(),
        "result_dir": str(result_dir),
        "selected_count": len(rows),
        "pid": pid,
        "process_alive": alive,
        "status_counts": counts,
    }
    (out_dir / "status.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Metagenome Deep-Review Run Status",
        "",
        f"Generated at: {summary['generated_at']}",
        f"Result directory: `{result_dir}`",
        f"Process PID: {pid or 'not recorded'}",
        f"Process alive: {alive}",
        "",
        "## Status Counts",
        "",
    ]
    if counts:
        for status, count in sorted(counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No selected run status found.")
    lines.extend(["", "## Recent Log Tail", ""])
    if log_tail:
        lines.extend(f"- {line[-240:]}" for line in log_tail[-20:])
    else:
        lines.append("- No `deep_review_run.log` found.")
    lines.extend(["", "## Output Files", "", "- `run_status.tsv`", "- `status.json`"])
    (out_dir / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
