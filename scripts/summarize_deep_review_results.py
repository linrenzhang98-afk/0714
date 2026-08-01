#!/usr/bin/env python3
"""Summarize completed metagenome deep-review QC/Kraken2/Bracken outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


BACKGROUND_KEYWORDS = ["homo sapiens", "toxoplasma", "arabidopsis", "benincasa", "cucurbita"]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_bracken(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append(
                {
                    "name": row.get("name", ""),
                    "taxonomy_id": row.get("taxonomy_id", ""),
                    "fraction_total_reads": as_float(row.get("fraction_total_reads")),
                    "new_est_reads": as_float(row.get("new_est_reads")),
                }
            )
    return rows


def parse_fastp(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    summary = data.get("summary", {})
    before = summary.get("before_filtering", {})
    after = summary.get("after_filtering", {})
    return {
        "before_total_reads": before.get("total_reads", ""),
        "after_total_reads": after.get("total_reads", ""),
        "after_q30_rate": after.get("q30_rate", ""),
        "after_gc_content": after.get("gc_content", ""),
    }


def is_background(name: str) -> bool:
    lower = name.lower()
    return any(key in lower for key in BACKGROUND_KEYWORDS)


def top_non_background(rows: list[dict[str, Any]]) -> dict[str, Any]:
    filtered = [row for row in rows if not is_background(str(row.get("name", "")))]
    if not filtered:
        return {}
    return max(filtered, key=lambda row: row.get("fraction_total_reads", 0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize metagenome deep-review results")
    parser.add_argument("--result-dir", default="results/20260731T000000Z-prjna1056765-metagenome-deep-review-plan")
    parser.add_argument("--baseline", default="reports_public/metagenome_deep_review/deep_review_samples.tsv")
    parser.add_argument("--run-status", default="reports_public/metagenome_deep_review_run/run_status.tsv")
    parser.add_argument("--out-dir", default="reports_public/metagenome_deep_review_summary")
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline = {row.get("run", ""): row for row in read_tsv(Path(args.baseline))}
    statuses = read_tsv(Path(args.run_status))

    rows: list[dict[str, Any]] = []
    stable = 0
    changed = 0
    missing = 0
    group_counts: Counter[str] = Counter()
    for status in statuses:
        run = status.get("run", "")
        base = baseline.get(run, {})
        bracken_rows = parse_bracken(result_dir / "kraken2_confirm" / f"{run}.bracken")
        fastp = parse_fastp(result_dir / "qc" / f"{run}.fastp.json")
        top = top_non_background(bracken_rows)
        baseline_pathogen = base.get("top_pathogen", "")
        confirm_pathogen = str(top.get("name", ""))
        baseline_fraction = as_float(base.get("top_pathogen_fraction"))
        confirm_fraction = as_float(top.get("fraction_total_reads"))
        if not confirm_pathogen:
            consistency = "missing_confirm"
            missing += 1
        elif confirm_pathogen == baseline_pathogen:
            consistency = "stable_same_top"
            stable += 1
        else:
            consistency = "changed_top"
            changed += 1
        group = base.get("pathogen_group", status.get("pathogen_group", ""))
        group_counts[group] += 1
        rows.append(
            {
                "run": run,
                "pathogen_group": group,
                "baseline_top_pathogen": baseline_pathogen,
                "baseline_top_fraction": baseline_fraction,
                "confirm_top_pathogen": confirm_pathogen,
                "confirm_top_fraction": confirm_fraction,
                "confirm_top_reads": top.get("new_est_reads", ""),
                "consistency": consistency,
                "status": status.get("status", ""),
                **fastp,
            }
        )

    fields = [
        "run",
        "pathogen_group",
        "baseline_top_pathogen",
        "baseline_top_fraction",
        "confirm_top_pathogen",
        "confirm_top_fraction",
        "confirm_top_reads",
        "consistency",
        "status",
        "before_total_reads",
        "after_total_reads",
        "after_q30_rate",
        "after_gc_content",
    ]
    with (out_dir / "comparison.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    consistency_counts = Counter(row["consistency"] for row in rows)
    lines = [
        "# Metagenome Deep-Review Summary",
        "",
        f"Runs summarized: {len(rows)}",
        "",
        "## Consistency Counts",
        "",
    ]
    for key, count in sorted(consistency_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Pathogen Groups", ""])
    for group, count in sorted(group_counts.items()):
        lines.append(f"- {group}: {count}")
    lines.extend(["", "## Changed Top Calls", ""])
    changed_rows = [row for row in rows if row["consistency"] == "changed_top"]
    if changed_rows:
        for row in changed_rows[:30]:
            lines.append(
                f"- {row['run']}: {row['baseline_top_pathogen']} -> {row['confirm_top_pathogen']} "
                f"(baseline {row['baseline_top_fraction']}, confirm {row['confirm_top_fraction']})"
            )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `stable_same_top` supports the first-pass pathogen call after QC rerun.",
            "- `changed_top` should be reviewed before biological interpretation.",
            "- Host removal was not performed because no host index was configured.",
            "",
            "## Output Files",
            "",
            "- `comparison.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "runs_summarized": len(rows),
                "stable_same_top": stable,
                "changed_top": changed,
                "missing_confirm": missing,
                "consistency_counts": dict(consistency_counts),
                "group_counts": dict(group_counts),
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
