#!/usr/bin/env python3
"""Summarize travel-mode Kraken2/Bracken pilot batches."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


KREPORT_RE = re.compile(r"^\s*([\d.]+)\s+(\d+)\s+(\d+)\s+([A-Z0-9-]+)\s+(\d+)\s+(.+?)\s*$")


def read_summary(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_status_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_kreport(path: Path) -> dict[str, Any]:
    total = None
    unclassified = 0
    classified = 0
    species_count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = KREPORT_RE.match(line)
        if not match:
            continue
        _pct, reads_clade, _reads_direct, rank, taxid, name = match.groups()
        reads = int(reads_clade)
        if taxid == "0" and "unclassified" in name.lower():
            unclassified = reads
        elif rank == "R":
            total = reads
        elif rank == "S":
            species_count += 1
    if total is None:
        total = unclassified + classified
    classified = max(0, total - unclassified)
    pct = classified / total * 100 if total else 0
    return {
        "total_reads": total,
        "classified_reads": classified,
        "unclassified_reads": unclassified,
        "classified_pct": round(pct, 4),
        "kraken_species_count": species_count,
    }


def parse_bracken(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                fraction = float(row.get("fraction_total_reads", 0) or 0)
                new_est = float(row.get("new_est_reads", 0) or 0)
            except ValueError:
                continue
            rows.append(
                {
                    "name": row.get("name", ""),
                    "taxonomy_id": row.get("taxonomy_id", ""),
                    "fraction_total_reads": fraction,
                    "new_est_reads": new_est,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize metagenome pilot result batches")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--pattern", default="20260723T022506Z-prjna1056765-travel-batch-*")
    parser.add_argument("--out-dir", default="reports_public/metagenome_pilot")
    args = parser.parse_args()

    results_root = Path(args.results_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    batch_dirs = sorted(p for p in results_root.glob(args.pattern) if p.is_dir())
    run_rows: list[dict[str, Any]] = []
    species_matrix: dict[str, dict[str, float]] = defaultdict(dict)
    species_seen = Counter()

    for batch_dir in batch_dirs:
        summary_path = batch_dir / "summary.json"
        status_path = batch_dir / "run_status.tsv"
        if not summary_path.exists() or not status_path.exists():
            continue
        summary = read_summary(summary_path)
        statuses = read_status_tsv(status_path)
        status_by_run = {row.get("run", ""): row for row in statuses}
        kraken_dir = batch_dir / "kraken2"
        for run, status in sorted(status_by_run.items()):
            row: dict[str, Any] = {
                "batch": batch_dir.name,
                "job_id": summary.get("job_id", batch_dir.name),
                "run": run,
                "status": status.get("status", ""),
                "error": status.get("error", ""),
            }
            kreport = kraken_dir / f"{run}.kreport"
            if kreport.exists():
                row.update(parse_kreport(kreport))
            bracken = kraken_dir / f"{run}.bracken"
            if bracken.exists():
                bracken_rows = parse_bracken(bracken)
                row["bracken_species_count"] = len(bracken_rows)
                for b in bracken_rows:
                    species = b["name"]
                    species_matrix[species][run] = b["fraction_total_reads"]
                    if b["fraction_total_reads"] > 0:
                        species_seen[species] += 1
                if bracken_rows:
                    top = max(bracken_rows, key=lambda r: r["fraction_total_reads"])
                    row["top_species"] = top["name"]
                    row["top_species_fraction"] = top["fraction_total_reads"]
            run_rows.append(row)

    run_fields = [
        "batch",
        "job_id",
        "run",
        "status",
        "total_reads",
        "classified_reads",
        "unclassified_reads",
        "classified_pct",
        "kraken_species_count",
        "bracken_species_count",
        "top_species",
        "top_species_fraction",
        "error",
    ]
    with (out_dir / "run_qc_summary.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=run_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(run_rows)

    runs = [row["run"] for row in run_rows]
    species = sorted(species_matrix, key=lambda s: (-species_seen[s], s))
    with (out_dir / "bracken_species_fraction_matrix.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["species", "detected_runs", *runs])
        for sp in species:
            writer.writerow([sp, species_seen[sp], *[species_matrix[sp].get(run, 0) for run in runs]])

    top_species = species[:30]
    lines = [
        "# Metagenome Pilot Summary",
        "",
        f"Batches summarized: {len(batch_dirs)}",
        f"Runs summarized: {len(run_rows)}",
        "",
        "## Status Counts",
        "",
    ]
    status_counts = Counter(str(row.get("status", "")) for row in run_rows)
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")
    if run_rows:
        classified_values = [float(row.get("classified_pct", 0) or 0) for row in run_rows]
        lines.extend(
            [
                "",
                "## Classification",
                "",
                f"- Min classified %: {min(classified_values):.3f}",
                f"- Median classified %: {sorted(classified_values)[len(classified_values)//2]:.3f}",
                f"- Max classified %: {max(classified_values):.3f}",
            ]
        )
    lines.extend(["", "## Frequently Detected Species", ""])
    for sp in top_species:
        lines.append(f"- {sp}: detected in {species_seen[sp]} runs")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `run_qc_summary.tsv`",
            "- `bracken_species_fraction_matrix.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
