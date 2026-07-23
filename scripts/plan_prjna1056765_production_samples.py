#!/usr/bin/env python3
"""Plan production-candidate samples for PRJNA1056765 from SRA RunInfo.

This script is read-only with respect to raw data. It does not download reads.
It creates candidate tables and a decision checklist for later production
analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def read_runinfo(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan PRJNA1056765 production candidate samples")
    parser.add_argument("--runinfo", required=True)
    parser.add_argument("--out-dir", default="reports_public/production_planning/prjna1056765")
    parser.add_argument("--max-size-mb", type=float, default=1000)
    parser.add_argument("--min-size-mb", type=float, default=1)
    args = parser.parse_args()

    runinfo = read_runinfo(Path(args.runinfo))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dna_wgs: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in runinfo:
        size_mb = parse_float(row.get("size_MB", ""))
        keep = True
        reasons: list[str] = []
        if row.get("LibraryStrategy") != "WGS":
            keep = False
            reasons.append("not_wgs")
        if row.get("LibrarySource") != "METAGENOMIC":
            keep = False
            reasons.append("not_metagenomic")
        if row.get("LibraryLayout") != "SINGLE":
            keep = False
            reasons.append("not_single")
        if "DNA" not in row.get("LibraryName", "").upper():
            keep = False
            reasons.append("not_dna_library")
        if size_mb < args.min_size_mb:
            keep = False
            reasons.append("too_small")
        if size_mb > args.max_size_mb:
            keep = False
            reasons.append("too_large_for_travel_planning")

        record = {
            "Run": row.get("Run", ""),
            "BioSample": row.get("BioSample", ""),
            "Sample": row.get("Sample", ""),
            "SampleName": row.get("SampleName", ""),
            "LibraryName": row.get("LibraryName", ""),
            "LibraryStrategy": row.get("LibraryStrategy", ""),
            "LibrarySource": row.get("LibrarySource", ""),
            "LibraryLayout": row.get("LibraryLayout", ""),
            "spots": row.get("spots", ""),
            "bases": row.get("bases", ""),
            "avgLength": row.get("avgLength", ""),
            "size_MB": size_mb,
            "ScientificName": row.get("ScientificName", ""),
            "Disease": row.get("Disease", ""),
            "Body_Site": row.get("Body_Site", ""),
            "CenterName": row.get("CenterName", ""),
        }
        if keep:
            dna_wgs.append(record)
        else:
            record["exclude_reasons"] = ",".join(reasons)
            excluded.append(record)

    dna_wgs.sort(key=lambda r: (str(r["BioSample"]), float(r["size_MB"]), str(r["Run"])))

    by_biosample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dna_wgs:
        by_biosample[str(row.get("BioSample", ""))].append(row)

    representative: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    for biosample, rows in sorted(by_biosample.items()):
        chosen = sorted(rows, key=lambda r: (-float(r["size_MB"]), str(r["Run"])))[0]
        chosen = dict(chosen)
        chosen["representative_rule"] = "largest_size_mb_per_biosample"
        representative.append(chosen)
        if len(rows) > 1:
            for row in rows:
                dup = dict(row)
                dup["representative_run"] = chosen["Run"]
                duplicate_rows.append(dup)

    size_bins = Counter()
    for row in dna_wgs:
        size = float(row["size_MB"])
        if size < 25:
            size_bins["001_lt25mb"] += 1
        elif size < 100:
            size_bins["002_25_99mb"] += 1
        elif size < 250:
            size_bins["003_100_249mb"] += 1
        elif size < 500:
            size_bins["004_250_499mb"] += 1
        else:
            size_bins["005_500mb_plus"] += 1

    fields = [
        "Run",
        "BioSample",
        "Sample",
        "SampleName",
        "LibraryName",
        "LibraryStrategy",
        "LibrarySource",
        "LibraryLayout",
        "spots",
        "bases",
        "avgLength",
        "size_MB",
        "ScientificName",
        "Disease",
        "Body_Site",
        "CenterName",
    ]
    write_tsv(out_dir / "candidate_dna_wgs_runs.tsv", dna_wgs, fields)
    write_tsv(out_dir / "representative_runs_by_biosample.tsv", representative, fields + ["representative_rule"])
    write_tsv(out_dir / "duplicate_biosample_runs.tsv", duplicate_rows, fields + ["representative_run"])
    write_tsv(out_dir / "excluded_runs.tsv", excluded, fields + ["exclude_reasons"])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_runinfo_rows": len(runinfo),
        "candidate_dna_wgs_runs": len(dna_wgs),
        "unique_biosamples_in_candidates": len(by_biosample),
        "representative_runs": len(representative),
        "duplicate_biosample_run_rows": len(duplicate_rows),
        "excluded_runs": len(excluded),
        "size_bins": dict(sorted(size_bins.items())),
        "max_size_mb_filter": args.max_size_mb,
        "min_size_mb_filter": args.min_size_mb,
    }
    (out_dir / "production_candidate_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# PRJNA1056765 Production Sample Planning",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "## Candidate Counts",
        "",
        f"- Total RunInfo rows: {summary['total_runinfo_rows']}",
        f"- Candidate DNA WGS metagenomic single-end runs: {summary['candidate_dna_wgs_runs']}",
        f"- Unique BioSamples among candidates: {summary['unique_biosamples_in_candidates']}",
        f"- Representative runs by BioSample: {summary['representative_runs']}",
        f"- Duplicate BioSample run rows: {summary['duplicate_biosample_run_rows']}",
        f"- Excluded runs: {summary['excluded_runs']}",
        "",
        "## Size Bins",
        "",
    ]
    for key, count in sorted(size_bins.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Production Before-Run Checklist",
            "",
            "- Confirm clinical question and grouping labels.",
            "- Confirm whether DNA and RNA libraries should remain separate.",
            "- Confirm BioSample duplicate handling; default candidate rule is largest run per BioSample.",
            "- Confirm whether all candidate DNA WGS runs or representative BioSample runs should be used.",
            "- Confirm final database/method choices before production conclusions.",
            "- Do not treat travel-mode pilot/focused results as final biological conclusions.",
            "",
            "## Output Files",
            "",
            "- `candidate_dna_wgs_runs.tsv`",
            "- `representative_runs_by_biosample.tsv`",
            "- `duplicate_biosample_runs.tsv`",
            "- `excluded_runs.tsv`",
            "- `production_candidate_summary.json`",
        ]
    )
    (out_dir / "production_planning_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
