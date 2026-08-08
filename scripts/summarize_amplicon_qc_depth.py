#!/usr/bin/env python3
"""Summarize DADA2 depth and rarefaction suitability for PRJNA511633."""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEPTH_CANDIDATES = [10, 50, 100, 500, 1000, 2000, 5000, 10000, 20000]


def run_command(command: list[str], log_path: Path) -> int:
    result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "command": command,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }, ensure_ascii=False) + "\n")
    return result.returncode


def read_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        sample_col = "#SampleID" if "#SampleID" in (reader.fieldnames or []) else "sample-id"
        group_col = "analysis_group"
        return {row.get(sample_col, ""): row.get(group_col, "") for row in reader if row.get(sample_col)}


def to_int(value: str) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return 0


def read_denoising_stats(path: Path, group_by_sample: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader((line for line in f if not line.startswith("#")), delimiter="\t")
        for row in reader:
            sample_id = row.get("sample-id") or row.get("sampleid") or row.get("sample_id") or ""
            input_reads = to_int(row.get("input", "0"))
            filtered = to_int(row.get("filtered", "0"))
            denoised = to_int(row.get("denoised", "0"))
            merged = to_int(row.get("merged", "0"))
            non_chimeric = to_int(row.get("non-chimeric", row.get("non_chimeric", "0")))
            final_reads = non_chimeric or merged or denoised or filtered
            rows.append({
                "sample_id": sample_id,
                "group": group_by_sample.get(sample_id, "unknown"),
                "input": input_reads,
                "filtered": filtered,
                "denoised": denoised,
                "merged": merged,
                "non_chimeric": non_chimeric,
                "final_reads": final_reads,
                "final_fraction": (final_reads / input_reads) if input_reads else 0.0,
            })
    return rows


def percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return float(values[0])
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def recommendation(rows: list[dict[str, object]]) -> tuple[str, str]:
    final_reads = [int(row["final_reads"]) for row in rows]
    if not final_reads:
        return "qc_failed", "DADA2 denoising stats were not available; cannot judge rarefaction depth."
    median_depth = statistics.median(final_reads)
    q25 = percentile(final_reads, 0.25)
    if median_depth < 1000:
        return (
            "not_publication_ready",
            "Median post-DADA2 depth is below 1000 reads; diversity statistics should not be used as formal conclusions. Optimize DADA2 trimming/merging before final alpha/beta diversity analysis.",
        )
    if q25 < 1000:
        return (
            "limited_diversity_use",
            "Lower-quartile post-DADA2 depth is below 1000 reads; choose rarefaction depth cautiously and report sensitivity analyses.",
        )
    return (
        "candidate_depth_possible",
        "Post-DADA2 depth may support diversity analysis after selecting a depth that preserves most samples in both groups and checking rarefaction stability.",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--qiime-bin", default="")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "qc_command_log.jsonl"

    denoising_qza = result_dir / "qiime2" / "denoising-stats.qza"
    export_dir = out_dir / "denoising_stats_export" / result_dir.name
    stats_tsv = export_dir / "stats.tsv"
    if denoising_qza.exists() and not stats_tsv.exists() and args.qiime_bin:
        export_dir.mkdir(parents=True, exist_ok=True)
        qiime_bin = Path(args.qiime_bin)
        env = os.environ.copy()
        env_path = str(qiime_bin.parent) if qiime_bin.is_absolute() else ""
        command = [
            "bash",
            "-lc",
            (
                "unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; "
                + (f"export PATH='{env_path}':${{PATH:-}}; " if env_path else "")
                + f"'{args.qiime_bin}' tools export --input-path '{denoising_qza}' --output-path '{export_dir}'"
            ),
        ]
        run_command(command, log_path)

    group_by_sample = read_metadata(Path(args.metadata))
    rows = read_denoising_stats(stats_tsv, group_by_sample)
    final_reads = [int(row["final_reads"]) for row in rows]
    state, reason = recommendation(rows)

    depth_rows = []
    groups = sorted({str(row["group"]) for row in rows if row["group"]})
    for depth in DEPTH_CANDIDATES:
        retained = [row for row in rows if int(row["final_reads"]) >= depth]
        depth_row = {
            "depth": depth,
            "retained_samples": len(retained),
            "retained_fraction": (len(retained) / len(rows)) if rows else 0.0,
        }
        for group in groups:
            group_total = sum(1 for row in rows if row["group"] == group)
            group_retained = sum(1 for row in retained if row["group"] == group)
            depth_row[f"{group}_retained"] = group_retained
            depth_row[f"{group}_total"] = group_total
        depth_rows.append(depth_row)

    with (out_dir / "denoising_depth_summary.tsv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["sample_id", "group", "input", "filtered", "denoised", "merged", "non_chimeric", "final_reads", "final_fraction"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    depth_fields = sorted({key for row in depth_rows for key in row.keys()}, key=lambda key: (key != "depth", key))
    with (out_dir / "sampling_depth_recommendations.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=depth_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(depth_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result_dir": str(result_dir),
        "sample_count": len(rows),
        "qc_state": state,
        "reason": reason,
        "min_final_reads": min(final_reads) if final_reads else 0,
        "q25_final_reads": percentile(final_reads, 0.25),
        "median_final_reads": statistics.median(final_reads) if final_reads else 0,
        "q75_final_reads": percentile(final_reads, 0.75),
        "max_final_reads": max(final_reads) if final_reads else 0,
        "depth_candidates": depth_rows,
    }
    (out_dir / "qc_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# PRJNA511633 Amplicon Depth QC",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        f"QC state: `{state}`",
        "",
        "## Interpretation",
        "",
        f"- {reason}",
        "- The `depth=10` retry is treated as an engineering fallback, not a publication-grade diversity depth.",
        "- Formal alpha/beta diversity requires an independently justified rarefaction depth and sensitivity analysis.",
        "",
        "## Post-DADA2 Depth Distribution",
        "",
        f"- Samples summarized: {len(rows)}",
        f"- Min final reads: {summary['min_final_reads']}",
        f"- Q25 final reads: {summary['q25_final_reads']:.1f}",
        f"- Median final reads: {summary['median_final_reads']}",
        f"- Q75 final reads: {summary['q75_final_reads']:.1f}",
        f"- Max final reads: {summary['max_final_reads']}",
        "",
        "## Files",
        "",
        "- `denoising_depth_summary.tsv`",
        "- `sampling_depth_recommendations.tsv`",
        "- `qc_summary.json`",
    ]
    (out_dir / "depth_qc.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
