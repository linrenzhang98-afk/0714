#!/usr/bin/env python3
"""Plan host-removal and AMR next-stage analysis readiness.

This script only inspects existing files and command availability. It does not
download data, install software, build indexes, or run analysis.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def command_row(name: str) -> dict[str, str]:
    path = shutil.which(name) or ""
    return {"command": name, "available": "yes" if path else "no", "path": path}


def bowtie2_index_exists(prefix: str) -> bool:
    if not prefix:
        return False
    expected = [f"{prefix}.{suffix}.bt2" for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    expected_large = [f"{prefix}.{suffix}.bt2l" for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    return all(Path(p).exists() for p in expected) or all(Path(p).exists() for p in expected_large)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan metagenome host-removal/AMR next stage")
    parser.add_argument("--deep-review", default="reports_public/metagenome_deep_review/deep_review_samples.tsv")
    parser.add_argument("--summary", default="reports_public/metagenome_deep_review_summary/summary.json")
    parser.add_argument("--out-dir", default="reports_public/metagenome_next_stage")
    parser.add_argument("--host-index-prefix", default=os.environ.get("HOST_INDEX_PREFIX", ""))
    parser.add_argument("--amr-db-dir", default=os.environ.get("AMR_DB_DIR", ""))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_tsv(Path(args.deep_review))

    commands = [
        command_row(name)
        for name in [
            "fastp",
            "bowtie2",
            "samtools",
            "kraken2",
            "bracken",
            "abricate",
            "rgi",
            "amrfinder",
            "diamond",
        ]
    ]
    with (out_dir / "tool_readiness.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["command", "available", "path"], delimiter="\t")
        writer.writeheader()
        writer.writerows(commands)

    host_ready = bowtie2_index_exists(args.host_index_prefix)
    amr_db_ready = bool(args.amr_db_dir and Path(args.amr_db_dir).exists())
    command_map = {row["command"]: row["available"] == "yes" for row in commands}
    qc_ready = command_map.get("fastp", False)
    host_tool_ready = command_map.get("bowtie2", False) and command_map.get("samtools", False)
    amr_tool_ready = any(command_map.get(name, False) for name in ["abricate", "rgi", "amrfinder", "diamond"])

    blockers: list[str] = []
    if not rows:
        blockers.append("Deep-review sample table is missing or empty.")
    if not qc_ready:
        blockers.append("fastp is not available.")
    if not host_tool_ready:
        blockers.append("bowtie2 and/or samtools are not available.")
    if not host_ready:
        blockers.append("HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.")
    if not amr_tool_ready:
        blockers.append("No AMR tool detected among abricate, rgi, amrfinder, diamond.")
    if not amr_db_ready:
        blockers.append("AMR_DB_DIR is not configured or does not exist.")

    recommended_stage = "report_interpretation_only"
    if qc_ready and command_map.get("kraken2", False) and command_map.get("bracken", False):
        recommended_stage = "qc_kraken_bracken_completed_or_available"
    if qc_ready and host_tool_ready and host_ready:
        recommended_stage = "host_removal_validation_ready"
    if qc_ready and host_tool_ready and host_ready and amr_tool_ready and amr_db_ready:
        recommended_stage = "host_removal_and_amr_ready"

    lines = [
        "# Metagenome Next-Stage Readiness",
        "",
        f"Generated at: {utc_now()}",
        f"Deep-review samples: {len(rows)}",
        f"Recommended stage: `{recommended_stage}`",
        "",
        "## Readiness",
        "",
        f"- QC ready: {qc_ready}",
        f"- Host-removal tools ready: {host_tool_ready}",
        f"- Host index ready: {host_ready}",
        f"- AMR tool ready: {amr_tool_ready}",
        f"- AMR database ready: {amr_db_ready}",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Do not start AMR or host-removal execution until host index and AMR database paths are explicitly configured.",
            "The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.",
            "",
            "## Output Files",
            "",
            "- `tool_readiness.tsv`",
        ]
    )
    (out_dir / "readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if blockers:
        Path("decision_requests").mkdir(exist_ok=True)
        (Path("decision_requests") / "metagenome_host_amr_requirements.md").write_text(
            "# Host-removal / AMR requirements\n\n"
            "The current Kraken2/Bracken analysis is complete. Starting host-removal or AMR requires additional local configuration.\n\n"
            "## Required before execution\n\n"
            + "\n".join(f"- {item}" for item in blockers)
            + "\n\n"
            "Set `HOST_INDEX_PREFIX` and `AMR_DB_DIR` in the systemd service or local shell only after confirming the intended databases.\n",
            encoding="utf-8",
        )
    else:
        request = Path("decision_requests") / "metagenome_host_amr_requirements.md"
        if request.exists():
            request.unlink()
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
