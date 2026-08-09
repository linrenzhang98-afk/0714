#!/usr/bin/env python3
"""Build a standard shotgun-metagenome report from host-removed review results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clean_taxon(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()) or "Unclassified"


def bracken_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_tsv(path):
        name = clean_taxon(row.get("name", ""))
        level = row.get("taxonomy_lvl", "")
        if level and level != "S":
            continue
        rows.append(
            {
                "taxon": name,
                "reads": safe_float(row.get("new_est_reads", row.get("kraken_assigned_reads", 0))),
                "fraction": safe_float(row.get("fraction_total_reads", 0.0)),
            }
        )
    return rows


def shannon(values: list[float]) -> float:
    total = sum(v for v in values if v > 0)
    if total <= 0:
        return 0.0
    return -sum((v / total) * math.log(v / total) for v in values if v > 0)


def simpson(values: list[float]) -> float:
    total = sum(v for v in values if v > 0)
    if total <= 0:
        return 0.0
    return 1.0 - sum((v / total) ** 2 for v in values if v > 0)


def bray_curtis(a: dict[str, float], b: dict[str, float]) -> float:
    taxa = set(a) | set(b)
    numerator = sum(abs(a.get(t, 0.0) - b.get(t, 0.0)) for t in taxa)
    denominator = sum(a.get(t, 0.0) + b.get(t, 0.0) for t in taxa)
    return numerator / denominator if denominator > 0 else 0.0


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mann_whitney_p(x: list[float], y: list[float]) -> float:
    if not x or not y:
        return 1.0
    pooled = [(v, 0) for v in x] + [(v, 1) for v in y]
    pooled.sort(key=lambda item: item[0])
    ranks = [0.0] * len(pooled)
    i = 0
    while i < len(pooled):
        j = i
        while j < len(pooled) and pooled[j][0] == pooled[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    rank_x = sum(rank for rank, (_, group) in zip(ranks, pooled) if group == 0)
    n1, n2 = len(x), len(y)
    u1 = rank_x - n1 * (n1 + 1) / 2.0
    mean_u = n1 * n2 / 2.0
    sd_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    if sd_u == 0:
        return 1.0
    z = (u1 - mean_u) / sd_u
    return max(0.0, min(1.0, 2.0 * (1.0 - normal_cdf(abs(z)))))


def bh_adjust(rows: list[dict[str, Any]], p_field: str = "p_value", q_field: str = "q_value") -> None:
    indexed = [(idx, safe_float(row.get(p_field, 1.0), 1.0)) for idx, row in enumerate(rows)]
    indexed.sort(key=lambda item: item[1], reverse=True)
    m = len(indexed)
    running = 1.0
    for rank_from_end, (idx, pval) in enumerate(indexed, start=1):
        rank = m - rank_from_end + 1
        running = min(running, pval * m / max(rank, 1))
        rows[idx][q_field] = running


def load_fastp_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_bowtie_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    overall = re.search(r"([0-9.]+)% overall alignment rate", text)
    reads = re.search(r"(\d+) reads; of these:", text)
    return {
        "host_alignment_rate_pct": safe_float(overall.group(1), 0.0) if overall else "",
        "bowtie2_input_reads": safe_int(reads.group(1), 0) if reads else "",
    }


def infer_result_dir(row: dict[str, str]) -> Path:
    host_removed = row.get("host_removed_fastq", "")
    if host_removed:
        path = Path(host_removed)
        for parent in path.parents:
            if parent.name.startswith("20260807T000000Z-prjna1056765-host-amr-screen-"):
                return parent
    return Path("results") / row.get("job_id", "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize standard shotgun metagenome outputs")
    parser.add_argument("--run-status", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--min-prevalence", type=int, default=2)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_tsv(args.run_status)
    sample_to_group = {row.get("run", ""): row.get("pathogen_group", "unknown") for row in rows if row.get("run")}

    abundance: dict[str, dict[str, float]] = {}
    qc_rows: list[dict[str, Any]] = []
    parse_failures: list[str] = []

    for row in rows:
        run = row.get("run", "")
        if not run:
            continue
        result_dir = infer_result_dir(row)
        bracken_path = Path(row.get("bracken", ""))
        if not bracken_path.exists():
            bracken_path = result_dir / "kraken2_confirm" / f"{run}.bracken"
        taxa_rows = bracken_rows(bracken_path)
        if not taxa_rows:
            parse_failures.append(run)
        abundance[run] = {item["taxon"]: item["fraction"] for item in taxa_rows}

        fastp = load_fastp_json(result_dir / "qc" / f"{run}.fastp.json")
        summary = fastp.get("summary", {})
        before = summary.get("before_filtering", {})
        after = summary.get("after_filtering", {})
        bowtie = parse_bowtie_log(result_dir / "logs" / f"{run}.bowtie2_host_removal.log")
        qc_rows.append(
            {
                "run": run,
                "pathogen_group": sample_to_group.get(run, "unknown"),
                "status": row.get("status", ""),
                "raw_reads": before.get("total_reads", ""),
                "filtered_reads": after.get("total_reads", ""),
                "raw_q30_rate": before.get("q30_rate", ""),
                "filtered_q30_rate": after.get("q30_rate", ""),
                "filtered_gc_content": after.get("gc_content", ""),
                "host_alignment_rate_pct": bowtie.get("host_alignment_rate_pct", ""),
                "bowtie2_input_reads": bowtie.get("bowtie2_input_reads", ""),
                "amr_status": row.get("amr_status", ""),
                "amr_records": row.get("amr_records", ""),
            }
        )

    taxa = sorted({taxon for sample in abundance.values() for taxon in sample})
    samples = sorted(abundance)
    matrix_rows = []
    for run in samples:
        matrix_rows.append({"run": run, "pathogen_group": sample_to_group.get(run, "unknown"), **{t: abundance[run].get(t, 0.0) for t in taxa}})
    write_tsv(out_dir / "species_relative_abundance_matrix.tsv", matrix_rows, ["run", "pathogen_group", *taxa])

    alpha_rows = []
    for run in samples:
        values = list(abundance[run].values())
        alpha_rows.append(
            {
                "run": run,
                "pathogen_group": sample_to_group.get(run, "unknown"),
                "observed_species": sum(1 for v in values if v > 0),
                "shannon": shannon(values),
                "simpson": simpson(values),
            }
        )
    write_tsv(out_dir / "alpha_diversity.tsv", alpha_rows, ["run", "pathogen_group", "observed_species", "shannon", "simpson"])

    beta_rows = []
    for sample_a in samples:
        row = {"run": sample_a}
        for sample_b in samples:
            row[sample_b] = bray_curtis(abundance[sample_a], abundance[sample_b])
        beta_rows.append(row)
    write_tsv(out_dir / "bray_curtis_distance_matrix.tsv", beta_rows, ["run", *samples])

    taxon_totals = Counter()
    taxon_prevalence = Counter()
    for sample in abundance.values():
        for taxon, value in sample.items():
            taxon_totals[taxon] += value
            if value > 0:
                taxon_prevalence[taxon] += 1
    top_taxa = [taxon for taxon, _ in taxon_totals.most_common(args.top_n)]
    stacked_rows = []
    for run in samples:
        row = {"run": run, "pathogen_group": sample_to_group.get(run, "unknown")}
        subtotal = 0.0
        for taxon in top_taxa:
            value = abundance[run].get(taxon, 0.0)
            row[taxon] = value
            subtotal += value
        row["Other"] = max(0.0, 1.0 - subtotal)
        stacked_rows.append(row)
    write_tsv(out_dir / "top_species_stacked_relative.tsv", stacked_rows, ["run", "pathogen_group", *top_taxa, "Other"])

    differential_rows: list[dict[str, Any]] = []
    groups = sorted(set(sample_to_group.values()))
    for group in groups:
        group_samples = [s for s in samples if sample_to_group.get(s) == group]
        other_samples = [s for s in samples if sample_to_group.get(s) != group]
        if len(group_samples) < 2 or len(other_samples) < 2:
            continue
        for taxon in taxa:
            if taxon_prevalence[taxon] < args.min_prevalence:
                continue
            group_values = [abundance[s].get(taxon, 0.0) for s in group_samples]
            other_values = [abundance[s].get(taxon, 0.0) for s in other_samples]
            mean_group = sum(group_values) / len(group_values)
            mean_other = sum(other_values) / len(other_values)
            differential_rows.append(
                {
                    "contrast": f"{group}_vs_other",
                    "taxon": taxon,
                    "prevalence": taxon_prevalence[taxon],
                    "mean_group": mean_group,
                    "mean_other": mean_other,
                    "mean_delta_group_minus_other": mean_group - mean_other,
                    "median_group": median(group_values),
                    "median_other": median(other_values),
                    "p_value": mann_whitney_p(group_values, other_values),
                }
            )
    bh_adjust(differential_rows)
    differential_rows.sort(key=lambda row: (safe_float(row.get("q_value", 1.0), 1.0), -abs(safe_float(row.get("mean_delta_group_minus_other", 0.0)))))
    diff_fields = [
        "contrast",
        "taxon",
        "prevalence",
        "mean_group",
        "mean_other",
        "mean_delta_group_minus_other",
        "median_group",
        "median_other",
        "p_value",
        "q_value",
    ]
    write_tsv(out_dir / "species_group_differentials.tsv", differential_rows, diff_fields)
    write_tsv(out_dir / "qc_host_removal_summary.tsv", qc_rows, [
        "run",
        "pathogen_group",
        "status",
        "raw_reads",
        "filtered_reads",
        "raw_q30_rate",
        "filtered_q30_rate",
        "filtered_gc_content",
        "host_alignment_rate_pct",
        "bowtie2_input_reads",
        "amr_status",
        "amr_records",
    ])

    status_counts = Counter(row.get("status", "unknown") for row in qc_rows)
    amr_counts = Counter(row.get("amr_status", "unknown") for row in qc_rows)
    significant = [row for row in differential_rows if safe_float(row.get("q_value", 1.0), 1.0) < 0.05]
    trend = [row for row in differential_rows if safe_float(row.get("q_value", 1.0), 1.0) < 0.10]
    summary = {
        "generated_at": utc_now(),
        "samples": len(samples),
        "groups": dict(Counter(sample_to_group.values())),
        "status_counts": dict(status_counts),
        "amr_status_counts": dict(amr_counts),
        "taxa": len(taxa),
        "parse_failures": parse_failures,
        "differential_tests": len(differential_rows),
        "fdr_significant_species": len(significant),
        "q_lt_0_10_species": len(trend),
        "top_taxa": top_taxa,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# PRJNA1056765 Standard Shotgun Summary",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "## Scope",
        "",
        "- Standard reporting layer for the 30 deep-review mNGS/shotgun samples.",
        "- Inputs are existing host-removed QC outputs, Kraken2/Bracken species profiles, and AMRFinderPlus short-read subset screen results.",
        "- This is stronger than the previous first-pass Kraken2/Bracken screen, but functional pathway profiling remains a separate HUMAnN-style extension.",
        "",
        "## Completion",
        "",
        f"- Samples summarized: {len(samples)}",
        f"- Species/taxa in matrix: {len(taxa)}",
        f"- Bracken parse failures: {len(parse_failures)}",
        f"- Differential tests: {len(differential_rows)}",
        f"- FDR-significant species contrasts: {len(significant)}",
        f"- q<0.10 screening contrasts: {len(trend)}",
        "",
        "## Status Counts",
        "",
    ]
    for key, count in sorted(status_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## AMR Screen", ""])
    for key, count in sorted(amr_counts.items()):
        lines.append(f"- {key}: {count}")
    if trend[:10]:
        lines.extend(["", "## Top Differential Signals", ""])
        for row in trend[:10]:
            lines.append(
                f"- {row['contrast']} / {row['taxon']}: delta={safe_float(row['mean_delta_group_minus_other']):.4f}, "
                f"q={safe_float(row['q_value']):.4g}"
            )
    lines.extend(
        [
            "",
            "## Standard Outputs",
            "",
            "- `qc_host_removal_summary.tsv`",
            "- `species_relative_abundance_matrix.tsv`",
            "- `top_species_stacked_relative.tsv`",
            "- `alpha_diversity.tsv`",
            "- `bray_curtis_distance_matrix.tsv`",
            "- `species_group_differentials.tsv`",
            "",
            "## Interpretation Guardrails",
            "",
            "- Species calls are Kraken2/Bracken database-dependent and should be interpreted as metagenomic classification signals.",
            "- AMRFinderPlus used capped host-removed short-read subsets; negative AMR findings are not definitive absence calls.",
            "- Group contrasts are pathogen-group descriptive contrasts, not clinical outcome associations unless specimen/diagnosis metadata are expanded.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
