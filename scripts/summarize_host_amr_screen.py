#!/usr/bin/env python3
"""Publish compact host-removal and AMRFinderPlus screen summaries."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def as_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def first_present(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = row.get(name, "")
        if value:
            return value
    return ""


def parse_amrfinder(path: Path, run: str, pathogen_group: str) -> list[dict[str, str]]:
    rows = read_tsv(path)
    parsed: list[dict[str, str]] = []
    for row in rows:
        gene = first_present(row, ["Gene symbol", "Gene", "Element symbol", "Element name"])
        element_type = first_present(row, ["Element type", "Type"])
        element_subtype = first_present(row, ["Element subtype", "Subtype"])
        drug_class = first_present(row, ["Class", "Drug Class", "Subclass"])
        method = first_present(row, ["Method"])
        identity = first_present(row, ["% Identity to reference sequence", "% Identity"])
        coverage = first_present(row, ["% Coverage of reference sequence", "% Coverage"])
        contig = first_present(row, ["Contig id", "Protein identifier", "Sequence name"])
        parsed.append(
            {
                "run": run,
                "pathogen_group": pathogen_group,
                "gene": gene,
                "element_type": element_type,
                "element_subtype": element_subtype,
                "drug_class": drug_class,
                "method": method,
                "identity": identity,
                "coverage": coverage,
                "contig": contig,
            }
        )
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize host-removal AMR screen result directories")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--pattern", default="20260807T000000Z-prjna1056765-host-amr-screen-*")
    parser.add_argument("--out-dir", default="reports_public/metagenome_host_amr_screen")
    args = parser.parse_args()

    results_root = Path(args.results_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_dirs = sorted(path for path in results_root.glob(args.pattern) if path.is_dir())
    run_rows: list[dict[str, str]] = []
    amr_rows: list[dict[str, str]] = []
    for result_dir in result_dirs:
        for row in read_tsv(result_dir / "run_status.tsv"):
            row = dict(row)
            row["job_id"] = result_dir.name
            run_rows.append(row)
            run = row.get("run", "")
            pathogen_group = row.get("pathogen_group", "")
            if run:
                amr_rows.extend(parse_amrfinder(result_dir / "amr_screen" / f"{run}.amrfinder.tsv", run, pathogen_group))

    run_fields = [
        "job_id",
        "run",
        "pathogen_group",
        "status",
        "error",
        "amr_status",
        "amr_records",
        "amr_subset_reads",
        "host_removed_fastq",
        "kreport",
        "bracken",
    ]
    with (out_dir / "run_status.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=run_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(run_rows)

    amr_fields = [
        "run",
        "pathogen_group",
        "gene",
        "element_type",
        "element_subtype",
        "drug_class",
        "method",
        "identity",
        "coverage",
        "contig",
    ]
    with (out_dir / "amrfinder_hits.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=amr_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(amr_rows)

    status_counts = Counter(row.get("status", "unknown") for row in run_rows)
    amr_status_counts = Counter(row.get("amr_status", "unknown") for row in run_rows)
    group_counts = Counter(row.get("pathogen_group", "unknown") for row in run_rows)
    gene_counts = Counter(row.get("gene", "") for row in amr_rows if row.get("gene", ""))
    runs_with_amr = len({row.get("run", "") for row in amr_rows if row.get("run", "")})
    total_reported_amr_records = sum(as_int(row.get("amr_records")) for row in run_rows)

    lines = [
        "# Host-Removal and AMR Screen Summary",
        "",
        f"Generated result directories: {len(result_dirs)}",
        f"Runs summarized: {len(run_rows)}",
        f"Runs with AMRFinderPlus hits: {runs_with_amr}",
        f"AMRFinderPlus hit rows parsed: {len(amr_rows)}",
        f"AMR records reported by runner: {total_reported_amr_records}",
        "",
        "## Run Status",
        "",
    ]
    for key, count in sorted(status_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## AMR Status", ""])
    for key, count in sorted(amr_status_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Pathogen Groups", ""])
    for key, count in sorted(group_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Frequent AMR Genes", ""])
    if gene_counts:
        for gene, count in gene_counts.most_common(30):
            lines.append(f"- {gene}: {count}")
    else:
        lines.append("- None detected in the capped short-read subsets.")
    lines.extend(
        [
            "",
            "## Interpretation Guardrail",
            "",
            "- Host-removal/AMR screen used capped host-removed short-read FASTA subsets.",
            "- Treat AMRFinderPlus hits as exploratory genotypic signals only.",
            "- Do not claim phenotypic resistance without orthogonal validation or culture/AST evidence.",
            "",
            "## Output Files",
            "",
            "- `run_status.tsv`",
            "- `amrfinder_hits.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "result_directories": len(result_dirs),
                "runs_summarized": len(run_rows),
                "runs_with_amr_hits": runs_with_amr,
                "amrfinder_hit_rows": len(amr_rows),
                "runner_reported_amr_records": total_reported_amr_records,
                "status_counts": dict(status_counts),
                "amr_status_counts": dict(amr_status_counts),
                "pathogen_group_counts": dict(group_counts),
                "top_amr_genes": dict(gene_counts.most_common(30)),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
