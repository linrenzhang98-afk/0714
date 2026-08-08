#!/usr/bin/env python3
"""Summarize PRJNA511633 amplicon results for manuscript-facing review."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ALPHA_ARTIFACTS = {
    "shannon": "core-metrics/shannon_vector.qza",
    "observed_features": "core-metrics/observed_features_vector.qza",
    "evenness": "core-metrics/evenness_vector.qza",
    "faith_pd": "core-metrics/faith_pd_vector.qza",
}


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


def qiime_command(qiime_bin: str, command: str) -> list[str]:
    qiime_path = Path(qiime_bin)
    env_path = str(qiime_path.parent) if qiime_path.is_absolute() else ""
    prefix = "unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH; "
    if env_path:
        prefix += f"export PATH='{env_path}':${{PATH:-}}; "
    return ["bash", "-lc", prefix + command]


def export_qza(qiime_bin: str, qza: Path, out_dir: Path, log_path: Path) -> bool:
    if not qza.exists():
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
        return True
    cmd = qiime_command(qiime_bin, f"'{qiime_bin}' tools export --input-path '{qza}' --output-path '{out_dir}'")
    return run_command(cmd, log_path) == 0


def biom_to_tsv(biom_path: Path, tsv_path: Path, log_path: Path) -> bool:
    if tsv_path.exists():
        return True
    if not biom_path.exists():
        return False
    cmd = ["bash", "-lc", f"biom convert -i '{biom_path}' -o '{tsv_path}' --to-tsv"]
    return run_command(cmd, log_path) == 0


def read_metadata(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        sample_col = "#SampleID" if "#SampleID" in (reader.fieldnames or []) else "sample-id"
        group_col = "analysis_group"
        return {row[sample_col]: row.get(group_col, "unknown") for row in reader if row.get(sample_col)}


def read_biom_tsv(path: Path) -> dict[str, dict[str, float]]:
    table: dict[str, dict[str, float]] = {}
    if not path.exists():
        return table
    header: list[str] | None = None
    with path.open("r", encoding="utf-8", newline="") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#OTU ID"):
                header = line.split("\t")
                continue
            if line.startswith("#") or header is None:
                continue
            parts = line.split("\t")
            taxon = parts[0]
            values: dict[str, float] = {}
            for sample, value in zip(header[1:], parts[1:]):
                try:
                    values[sample] = float(value)
                except ValueError:
                    values[sample] = 0.0
            table[taxon] = values
    return table


def read_alpha_export(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames or []
        sample_col = fields[0] if fields else ""
        value_col = fields[1] if len(fields) > 1 else ""
        values = {}
        for row in reader:
            try:
                values[row[sample_col]] = float(row[value_col])
            except (KeyError, ValueError):
                continue
        return values


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mann_whitney_p(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 1.0
    combined = [(v, 0) for v in a] + [(v, 1) for v in b]
    combined.sort(key=lambda item: item[0])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i + 1
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    rank_sum_a = sum(rank for rank, (_, group) in zip(ranks, combined) if group == 0)
    n1, n2 = len(a), len(b)
    u1 = rank_sum_a - n1 * (n1 + 1) / 2.0
    mean_u = n1 * n2 / 2.0
    var_u = n1 * n2 * (n1 + n2 + 1) / 12.0
    if var_u <= 0:
        return 1.0
    z = (abs(u1 - mean_u) - 0.5) / math.sqrt(var_u)
    return max(0.0, min(1.0, 2.0 * (1.0 - normal_cdf(z))))


def bh_fdr(rows: list[dict[str, object]], p_key: str = "p_value") -> None:
    sortable = [(i, float(row[p_key])) for i, row in enumerate(rows)]
    sortable.sort(key=lambda item: item[1])
    m = len(sortable)
    prev = 1.0
    for rank in range(m, 0, -1):
        idx, p = sortable[rank - 1]
        q = min(prev, p * m / rank)
        rows[idx]["q_value"] = f"{q:.6g}"
        prev = q


def group_values(values_by_sample: dict[str, float], group_by_sample: dict[str, str]) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for sample, group in group_by_sample.items():
        grouped[group].append(values_by_sample.get(sample, 0.0))
    return grouped


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def summarize_taxa(level: str, table: dict[str, dict[str, float]], group_by_sample: dict[str, str], out_dir: Path) -> list[dict[str, object]]:
    groups = sorted(set(group_by_sample.values()))
    if len(groups) != 2:
        return []
    g1, g2 = groups
    rows: list[dict[str, object]] = []
    for taxon, values in table.items():
        grouped = group_values(values, group_by_sample)
        vals1 = grouped[g1]
        vals2 = grouped[g2]
        detect1 = sum(1 for v in vals1 if v > 0)
        detect2 = sum(1 for v in vals2 if v > 0)
        row = {
            "taxonomic_level": level,
            "taxon": taxon,
            f"{g1}_mean": f"{mean(vals1):.8f}",
            f"{g2}_mean": f"{mean(vals2):.8f}",
            "mean_delta_g2_minus_g1": f"{mean(vals2) - mean(vals1):.8f}",
            f"{g1}_detected": detect1,
            f"{g2}_detected": detect2,
            "p_value": f"{mann_whitney_p(vals1, vals2):.6g}",
        }
        rows.append(row)
    bh_fdr(rows)
    rows.sort(key=lambda row: (float(row["q_value"]), -abs(float(row["mean_delta_g2_minus_g1"])), str(row["taxon"])))
    fields = ["taxonomic_level", "taxon", f"{g1}_mean", f"{g2}_mean", "mean_delta_g2_minus_g1", f"{g1}_detected", f"{g2}_detected", "p_value", "q_value"]
    write_tsv(out_dir / f"{level}_group_differentials.tsv", rows, fields)
    return rows


def summarize_alpha(alpha_tables: dict[str, dict[str, float]], group_by_sample: dict[str, str], out_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    groups = sorted(set(group_by_sample.values()))
    if len(groups) != 2:
        return rows
    g1, g2 = groups
    for metric, values in alpha_tables.items():
        grouped = group_values(values, group_by_sample)
        vals1, vals2 = grouped[g1], grouped[g2]
        rows.append({
            "metric": metric,
            f"{g1}_n": len(vals1),
            f"{g2}_n": len(vals2),
            f"{g1}_median": f"{statistics.median(vals1):.6g}" if vals1 else "0",
            f"{g2}_median": f"{statistics.median(vals2):.6g}" if vals2 else "0",
            "median_delta_g2_minus_g1": f"{(statistics.median(vals2) if vals2 else 0) - (statistics.median(vals1) if vals1 else 0):.6g}",
            "p_value": f"{mann_whitney_p(vals1, vals2):.6g}",
        })
    bh_fdr(rows)
    fields = ["metric", f"{g1}_n", f"{g2}_n", f"{g1}_median", f"{g2}_median", "median_delta_g2_minus_g1", "p_value", "q_value"]
    write_tsv(out_dir / "alpha_diversity_group_summary.tsv", rows, fields)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--qiime-bin", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "summary_command_log.jsonl"
    group_by_sample = read_metadata(args.metadata)

    exports = out_dir / "exports"
    genus_export = exports / "genus_relative"
    species_export = exports / "species_relative"
    export_qza(args.qiime_bin, args.result_dir / "qiime2" / "genus-relative-table.qza", genus_export, log_path)
    export_qza(args.qiime_bin, args.result_dir / "qiime2" / "species-relative-table.qza", species_export, log_path)
    biom_to_tsv(genus_export / "feature-table.biom", out_dir / "genus_relative_table.tsv", log_path)
    biom_to_tsv(species_export / "feature-table.biom", out_dir / "species_relative_table.tsv", log_path)

    alpha_tables: dict[str, dict[str, float]] = {}
    for metric, rel in ALPHA_ARTIFACTS.items():
        export_dir = exports / f"alpha_{metric}"
        if export_qza(args.qiime_bin, args.result_dir / "qiime2" / rel, export_dir, log_path):
            alpha_tables[metric] = read_alpha_export(export_dir / "alpha-diversity.tsv")

    genus = read_biom_tsv(out_dir / "genus_relative_table.tsv")
    species = read_biom_tsv(out_dir / "species_relative_table.tsv")
    genus_rows = summarize_taxa("genus", genus, group_by_sample, out_dir)
    species_rows = summarize_taxa("species", species, group_by_sample, out_dir)
    alpha_rows = summarize_alpha(alpha_tables, group_by_sample, out_dir)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result_dir": str(args.result_dir),
        "samples": len(group_by_sample),
        "groups": {group: sum(1 for g in group_by_sample.values() if g == group) for group in sorted(set(group_by_sample.values()))},
        "genus_tested": len(genus_rows),
        "species_tested": len(species_rows),
        "alpha_metrics": len(alpha_rows),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    top_genus = genus_rows[:10]
    top_species = species_rows[:10]
    lines = [
        "# PRJNA511633 Publication Summary",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "## Status",
        "",
        "- Reverse-read DADA2 result is the current analyzable result.",
        "- Depth QC supports formal diversity analysis after choosing a justified sampling depth.",
        "- Statistical rows below are screening-level summaries; final manuscript wording should verify QIIME2 visualizations and sensitivity to rarefaction depth.",
        "",
        "## Outputs",
        "",
        "- `alpha_diversity_group_summary.tsv`",
        "- `genus_group_differentials.tsv`",
        "- `species_group_differentials.tsv`",
        "- `genus_relative_table.tsv`",
        "- `species_relative_table.tsv`",
        "",
        "## Top Genus-Level Candidates",
        "",
    ]
    for row in top_genus:
        lines.append(f"- {row['taxon']}: delta={row['mean_delta_g2_minus_g1']}, q={row['q_value']}")
    lines.extend(["", "## Top Species-Level Candidates", ""])
    for row in top_species:
        lines.append(f"- {row['taxon']}: delta={row['mean_delta_g2_minus_g1']}, q={row['q_value']}")
    lines.extend(["", "## Suggested Manuscript Direction", ""])
    lines.extend([
        "- Frame this as a reproducible public 16S re-analysis of gut microbiota shifts in ICPP, not as a discovery of causality.",
        "- Prioritize robust genus-level patterns, alpha/beta diversity, and taxa suitable for qPCR validation in independent fecal samples.",
        "- Treat species-level labels from V3-V4 16S as hypothesis-generating unless confirmed by targeted assays.",
    ])
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
