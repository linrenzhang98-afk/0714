#!/usr/bin/env python3
"""Create a second-stage shortlist from first-pass metagenome summaries."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


PATHOGEN_GROUPS = {
    "Acinetobacter": ["acinetobacter"],
    "Burkholderia": ["burkholderia"],
    "Candida": ["candida"],
    "Enterococcus": ["enterococcus"],
    "Enterobacterales": ["klebsiella", "escherichia", "enterobacter", "citrobacter"],
    "Haemophilus": ["haemophilus"],
    "Mycobacteria": ["mycobacter", "mycobacteroides"],
    "Pseudomonas": ["pseudomonas"],
    "Staphylococcus": ["staphylococcus"],
    "Stenotrophomonas": ["stenotrophomonas"],
    "Streptococcus": ["streptococcus"],
    "Other": [],
}

BACKGROUND_KEYWORDS = [
    "arabidopsis",
    "benincasa",
    "cucurbita",
    "homo sapiens",
    "toxoplasma",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def pathogen_group(name: str) -> str:
    lower = name.lower()
    for group, keys in PATHOGEN_GROUPS.items():
        if any(key in lower for key in keys):
            return group
    return "Other"


def is_background(name: str) -> bool:
    lower = name.lower()
    return any(key in lower for key in BACKGROUND_KEYWORDS)


def clean_hits(value: str) -> str:
    names = [name for name in value.split(";") if name]
    return ";".join(name for name in names if not is_background(name))


def as_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan second-stage metagenome analysis")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out-dir", default="reports_public/metagenome_second_stage")
    parser.add_argument("--max-per-group", type=int, default=8)
    parser.add_argument("--max-other", type=int, default=8)
    parser.add_argument("--max-total", type=int, default=80)
    args = parser.parse_args()

    candidate_path = Path(args.candidates)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_tsv(candidate_path)
    for row in rows:
        row["pathogen_group"] = pathogen_group(row.get("top_pathogen", ""))

    rows = sorted(
        rows,
        key=lambda row: (
            int(row.get("second_stage_priority") or 99),
            -as_float(row.get("top_pathogen_fraction", "")),
            -as_float(row.get("classified_pct", "")),
            row.get("run", ""),
        ),
    )

    selected: list[dict[str, str]] = []
    group_counts: Counter[str] = Counter()
    for row in rows:
        if is_background(row.get("top_pathogen", "")):
            continue
        row["clinical_pathogen_hits"] = clean_hits(row.get("clinical_pathogen_hits", ""))
        group = row["pathogen_group"]
        if len(selected) >= args.max_total:
            break
        group_limit = args.max_other if group == "Other" else args.max_per_group
        if group_counts[group] >= group_limit:
            continue
        selected.append(row)
        group_counts[group] += 1

    fields = [
        "pathogen_group",
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
    with (out_dir / "shortlist.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)

    all_group_counts = Counter(row["pathogen_group"] for row in rows)
    with (out_dir / "pathogen_group_counts.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["pathogen_group", "candidate_count", "shortlist_count"])
        for group in sorted(all_group_counts):
            writer.writerow([group, all_group_counts[group], group_counts[group]])

    top_lines = []
    for row in selected[:20]:
        top_lines.append(
            f"- {row.get('run')}: {row.get('top_pathogen')} "
            f"(group {row.get('pathogen_group')}, pathogen fraction {row.get('top_pathogen_fraction')}, "
            f"classified {row.get('classified_pct')}%)"
        )

    lines = [
        "# Metagenome Second-Stage Plan",
        "",
        "## Scope",
        "",
        f"- Input candidate rows: {len(rows)}",
        f"- Shortlisted rows: {len(selected)}",
        "- Source: PRJNA1056765 production first-pass Kraken2/Bracken output",
        "- No new data download is required for this planning step.",
        "",
        "## Group Counts",
        "",
    ]
    for group in sorted(all_group_counts):
        lines.append(f"- {group}: {group_counts[group]} selected / {all_group_counts[group]} candidates")
    lines.extend(
        [
            "",
            "## Top Shortlist Examples",
            "",
            *top_lines,
            "",
            "## Recommended Next Analysis",
            "",
            "- Review `shortlist.tsv` before any heavy re-analysis.",
            "- Keep first-pass Kraken2/Bracken outputs as the screening baseline.",
            "- If proceeding, run host-removal and QC only on the shortlist, not all 400 samples.",
            "- Defer AMR or functional profiling until the pathogen-group shortlist is reviewed.",
            "",
            "## Output Files",
            "",
            "- `shortlist.tsv`",
            "- `pathogen_group_counts.tsv`",
        ]
    )
    (out_dir / "plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
