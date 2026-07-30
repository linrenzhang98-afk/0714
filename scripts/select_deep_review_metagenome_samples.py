#!/usr/bin/env python3
"""Select a compact deep-review set from metagenome second-stage shortlist."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


CORE_GROUPS = [
    "Acinetobacter",
    "Enterobacterales",
    "Haemophilus",
    "Mycobacteria",
    "Pseudomonas",
    "Staphylococcus",
    "Streptococcus",
]


def as_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def rank_key(row: dict[str, str]) -> tuple[int, float, float, str]:
    return (
        int(row.get("second_stage_priority") or 99),
        -as_float(row.get("top_pathogen_fraction", "")),
        -as_float(row.get("classified_pct", "")),
        row.get("run", ""),
    )


def select(rows: list[dict[str, str]], max_total: int, max_per_group: int) -> list[dict[str, str]]:
    sorted_rows = sorted(rows, key=rank_key)
    selected: list[dict[str, str]] = []
    selected_runs: set[str] = set()
    group_counts: Counter[str] = Counter()

    # First pass: force representation of core pathogen groups.
    for group in CORE_GROUPS:
        group_rows = [row for row in sorted_rows if row.get("pathogen_group") == group]
        for row in group_rows[:max_per_group]:
            run = row.get("run", "")
            if run in selected_runs:
                continue
            selected.append(row)
            selected_runs.add(run)
            group_counts[group] += 1
            if len(selected) >= max_total:
                return selected

    # Second pass: fill by overall rank, still respecting per-group limits.
    for row in sorted_rows:
        run = row.get("run", "")
        group = row.get("pathogen_group", "")
        if run in selected_runs:
            continue
        if group_counts[group] >= max_per_group:
            continue
        selected.append(row)
        selected_runs.add(run)
        group_counts[group] += 1
        if len(selected) >= max_total:
            break
    return sorted(selected, key=rank_key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select compact deep-review metagenome sample set")
    parser.add_argument("--shortlist", required=True)
    parser.add_argument("--out-dir", default="reports_public/metagenome_deep_review")
    parser.add_argument("--max-total", type=int, default=30)
    parser.add_argument("--max-per-group", type=int, default=4)
    args = parser.parse_args()

    rows = read_tsv(Path(args.shortlist))
    selected = select(rows, args.max_total, args.max_per_group)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

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
    with (out_dir / "deep_review_samples.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)

    group_counts = Counter(row.get("pathogen_group", "") for row in selected)
    lines = [
        "# Metagenome Deep-Review Sample Set",
        "",
        f"- Source shortlist rows: {len(rows)}",
        f"- Selected samples: {len(selected)}",
        f"- Max per group: {args.max_per_group}",
        "- Purpose: compact set for possible QC/host-removal/Kraken2 confirmation.",
        "- No heavy analysis has been started by this planning step.",
        "",
        "## Selected Groups",
        "",
    ]
    for group, count in sorted(group_counts.items()):
        lines.append(f"- {group}: {count}")
    lines.extend(["", "## Top Selected Samples", ""])
    for row in selected[:20]:
        lines.append(
            f"- {row.get('run')}: {row.get('top_pathogen')} "
            f"({row.get('pathogen_group')}, fraction {row.get('top_pathogen_fraction')}, "
            f"classified {row.get('classified_pct')}%)"
        )
    lines.extend(
        [
            "",
            "## Recommended Execution",
            "",
            "- Use this set before any larger re-analysis.",
            "- Start with QC and host-removal validation on these selected runs.",
            "- If results are coherent, expand within the same pathogen groups.",
            "",
            "## Output Files",
            "",
            "- `deep_review_samples.tsv`",
        ]
    )
    (out_dir / "plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
