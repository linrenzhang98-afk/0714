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

CLINICAL_PATHOGEN_KEYWORDS = [
    "acinetobacter",
    "burkholderia",
    "candida",
    "chlamydia",
    "citrobacter",
    "cryptococcus",
    "enterobacter",
    "enterococcus",
    "escherichia coli",
    "haemophilus",
    "klebsiella",
    "legionella",
    "mycobacter",
    "mycobacteroides",
    "nocardia",
    "pneumocystis",
    "prevotella",
    "pseudomonas",
    "rothia",
    "staphylococcus",
    "stenotrophomonas",
    "streptococcus",
    "veillonella",
]

LIKELY_BACKGROUND_KEYWORDS = [
    "homo sapiens",
    "arabidopsis",
    "benincasa",
    "cucurbita",
    "toxoplasma",
]


def read_summary(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_status_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_kreport(path: Path) -> dict[str, Any]:
    root_classified = 0
    unclassified = 0
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
            root_classified = reads
        elif rank == "S":
            species_count += 1
    classified = root_classified
    total = unclassified + classified
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


def pathogen_hits(bracken_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits = []
    for row in bracken_rows:
        name = str(row.get("name", ""))
        name_l = name.lower()
        if any(bg in name_l for bg in LIKELY_BACKGROUND_KEYWORDS):
            continue
        if any(key in name_l for key in CLINICAL_PATHOGEN_KEYWORDS):
            hits.append(row)
    return sorted(hits, key=lambda r: float(r.get("fraction_total_reads", 0) or 0), reverse=True)


def priority_for(row: dict[str, Any]) -> tuple[int, str]:
    status = row.get("status", "")
    if status != "done":
        return 0, "not_done"
    pathogen_fraction = float(row.get("top_pathogen_fraction", 0) or 0)
    classified_pct = float(row.get("classified_pct", 0) or 0)
    species_count = int(row.get("bracken_species_count", 0) or 0)
    if pathogen_fraction >= 0.01:
        return 1, "high_pathogen_fraction"
    if pathogen_fraction >= 0.001:
        return 2, "moderate_pathogen_fraction"
    if classified_pct >= 5 and species_count >= 5:
        return 3, "high_classified_fraction"
    if pathogen_fraction > 0:
        return 4, "low_fraction_clinical_pathogen"
    return 0, "not_selected"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize metagenome pilot result batches")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--pattern", default="20260723T022506Z-prjna1056765-travel-batch-*")
    parser.add_argument("--out-dir", default="reports_public/metagenome_pilot")
    parser.add_argument("--title", default="Metagenome Pilot Summary")
    parser.add_argument("--candidate-limit", type=int, default=80)
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
                    hits = pathogen_hits(bracken_rows)
                    if hits:
                        top_hit = hits[0]
                        row["top_pathogen"] = top_hit["name"]
                        row["top_pathogen_fraction"] = top_hit["fraction_total_reads"]
                        row["top_pathogen_reads"] = top_hit["new_est_reads"]
                        row["clinical_pathogen_hits"] = ";".join(h["name"] for h in hits[:5])
            priority, reason = priority_for(row)
            row["second_stage_priority"] = priority if priority else ""
            row["second_stage_reason"] = reason if priority else ""
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
        "top_pathogen",
        "top_pathogen_fraction",
        "top_pathogen_reads",
        "clinical_pathogen_hits",
        "second_stage_priority",
        "second_stage_reason",
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

    candidates = [
        row
        for row in run_rows
        if row.get("second_stage_priority") not in {"", None}
    ]
    candidates = sorted(
        candidates,
        key=lambda row: (
            int(row.get("second_stage_priority", 99) or 99),
            -float(row.get("top_pathogen_fraction", 0) or 0),
            -float(row.get("classified_pct", 0) or 0),
            str(row.get("run", "")),
        ),
    )[: args.candidate_limit]
    candidate_fields = [
        "second_stage_priority",
        "second_stage_reason",
        "run",
        "batch",
        "classified_pct",
        "total_reads",
        "top_pathogen",
        "top_pathogen_fraction",
        "top_pathogen_reads",
        "clinical_pathogen_hits",
        "top_species",
        "top_species_fraction",
    ]
    with (out_dir / "second_stage_candidates.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=candidate_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidates)

    top_species = species[:30]
    lines = [
        f"# {args.title}",
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
            "- `second_stage_candidates.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
