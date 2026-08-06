#!/usr/bin/env python3
"""Diagnosis-group pathogen differential summaries for PRJNA1056765."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_PRIORITY = {
    "Pseudomonas aeruginosa": ("Bacterial infection", "qPCR/ddPCR", "oprL or ecfX"),
    "Klebsiella pneumoniae": ("Bacterial infection", "qPCR/ddPCR", "khe or rpoB"),
    "Acinetobacter baumannii": ("Bacterial infection", "qPCR/ddPCR", "blaOXA-51-like or recA"),
    "Staphylococcus aureus": ("Bacterial infection", "qPCR/ddPCR", "nuc"),
    "Stenotrophomonas maltophilia": ("Bacterial infection", "qPCR/ddPCR", "smeD or 23S marker"),
    "Haemophilus influenzae": ("Bacterial infection", "qPCR/ddPCR", "hpd"),
    "Streptococcus pneumoniae": ("Bacterial infection", "qPCR/ddPCR", "lytA"),
    "Mycobacterium tuberculosis": ("Pulmonary tuberculosis", "qPCR/ddPCR", "IS6110"),
    "Candida albicans": ("Fungal infection", "qPCR/ddPCR", "ITS or ACT1"),
    "Cryptococcus neoformans": ("Fungal infection", "qPCR/ddPCR", "ITS"),
    "Aspergillus fumigatus": ("Fungal infection", "qPCR/ddPCR", "ITS or 28S"),
}

BACKGROUND_OR_LOW_SPECIFICITY = {
    "Homo sapiens",
    "Toxoplasma gondii",
    "Arabidopsis thaliana",
    "Benincasa hispida",
    "Camelina sativa",
    "Cucurbita pepo",
}

COMMENSAL_CONTEXT = {
    "Prevotella melaninogenica",
    "Prevotella intermedia",
    "Prevotella jejuni",
    "Rothia mucilaginosa",
    "Streptococcus mitis",
    "Streptococcus oralis",
    "Veillonella parvula",
    "Fusobacterium nucleatum",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for [[a,b],[c,d]]."""

    row1 = a + b
    row2 = c + d
    col1 = a + c
    n = row1 + row2
    if n == 0:
        return 1.0

    def log_choose(nn: int, kk: int) -> float:
        if kk < 0 or kk > nn:
            return float("-inf")
        return math.lgamma(nn + 1) - math.lgamma(kk + 1) - math.lgamma(nn - kk + 1)

    def prob(x: int) -> float:
        return math.exp(log_choose(col1, x) + log_choose(n - col1, row1 - x) - log_choose(n, row1))

    observed = prob(a)
    lo = max(0, row1 - (n - col1))
    hi = min(row1, col1)
    p = 0.0
    for x in range(lo, hi + 1):
        px = prob(x)
        if px <= observed + 1e-12:
            p += px
    return min(1.0, p)


def bh_fdr(pvalues: list[float]) -> list[float]:
    n = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda x: x[1])
    q = [1.0] * n
    running = 1.0
    for rank, (idx, p) in reversed(list(enumerate(indexed, start=1))):
        running = min(running, p * n / rank)
        q[idx] = min(1.0, running)
    return q


def load_fraction_matrix(path: Path) -> tuple[list[str], dict[str, dict[str, float]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        run_columns = [field for field in (reader.fieldnames or []) if field not in {"species", "detected_runs"}]
        matrix: dict[str, dict[str, float]] = {}
        for row in reader:
            species = row["species"]
            matrix[species] = {run: safe_float(row.get(run)) for run in run_columns}
    return run_columns, matrix


def species_context(species: str) -> str:
    if species in TARGET_PRIORITY:
        return "wetlab_priority_pathogen"
    if species in BACKGROUND_OR_LOW_SPECIFICITY:
        return "background_or_low_specificity"
    if species in COMMENSAL_CONTEXT:
        return "oral_respiratory_commensal_context"
    return "other_taxon"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clinical-mapping", type=Path, default=Path("reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv"))
    parser.add_argument("--bracken-matrix", type=Path, default=Path("reports_public/metagenome_production/bracken_species_fraction_matrix.tsv"))
    parser.add_argument("--deep-review", type=Path, default=Path("reports_public/prjna1056765_clinical_groups/deep_review_by_diagnosis.tsv"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports_public/prjna1056765_group_differentials"))
    parser.add_argument("--min-detected-total", type=int, default=3)
    args = parser.parse_args()

    mapping = read_tsv(args.clinical_mapping)
    run_to_diag = {row["run"]: row["diagnosis"] for row in mapping}
    diagnoses = sorted(set(run_to_diag.values()))
    run_columns, matrix = load_fraction_matrix(args.bracken_matrix)
    usable_runs = [run for run in run_columns if run in run_to_diag]
    diag_runs = {diag: [run for run in usable_runs if run_to_diag[run] == diag] for diag in diagnoses}

    diff_rows: list[dict[str, Any]] = []
    raw_pvalues: list[float] = []
    for species, values_by_run in matrix.items():
        detected_total = sum(1 for run in usable_runs if values_by_run.get(run, 0.0) > 0)
        if detected_total < args.min_detected_total:
            continue
        for diag in diagnoses:
            group_runs = diag_runs[diag]
            rest_runs = [run for run in usable_runs if run_to_diag[run] != diag]
            group_vals = [values_by_run.get(run, 0.0) for run in group_runs]
            rest_vals = [values_by_run.get(run, 0.0) for run in rest_runs]
            a = sum(1 for v in group_vals if v > 0)
            b = len(group_vals) - a
            c = sum(1 for v in rest_vals if v > 0)
            d = len(rest_vals) - c
            p = fisher_two_sided(a, b, c, d)
            raw_pvalues.append(p)
            group_rate = a / len(group_vals) if group_vals else 0.0
            rest_rate = c / len(rest_vals) if rest_vals else 0.0
            group_median = median(group_vals)
            rest_median = median(rest_vals)
            row = {
                "diagnosis": diag,
                "species": species,
                "context": species_context(species),
                "group_detected": a,
                "group_total": len(group_vals),
                "group_detect_rate": f"{group_rate:.5f}",
                "rest_detected": c,
                "rest_total": len(rest_vals),
                "rest_detect_rate": f"{rest_rate:.5f}",
                "detect_rate_delta": f"{(group_rate - rest_rate):.5f}",
                "group_median_fraction": f"{group_median:.8f}",
                "rest_median_fraction": f"{rest_median:.8f}",
                "median_fraction_delta": f"{(group_median - rest_median):.8f}",
                "fisher_p": f"{p:.6g}",
            }
            diff_rows.append(row)

    fdrs = bh_fdr(raw_pvalues)
    for row, q in zip(diff_rows, fdrs):
        row["bh_fdr"] = f"{q:.6g}"
        # Ranking favors clinically interpretable, enriched, and significant signals.
        context_boost = 2 if row["context"] == "wetlab_priority_pathogen" else 0
        row["priority_score"] = f"{float(row['detect_rate_delta']) * 10 + float(row['group_median_fraction']) * 100 + context_boost:.5f}"

    diff_rows.sort(
        key=lambda row: (
            row["diagnosis"],
            row["context"] != "wetlab_priority_pathogen",
            float(row["bh_fdr"]),
            -float(row["detect_rate_delta"]),
            -float(row["group_median_fraction"]),
        )
    )

    target_rows: list[dict[str, Any]] = []
    by_pair = {(row["diagnosis"], row["species"]): row for row in diff_rows}
    deep_rows = read_tsv(args.deep_review) if args.deep_review.exists() else []
    deep_stable = Counter(row["confirm_top_pathogen"] for row in deep_rows if row.get("consistency") == "stable_same_top")
    for species, (expected_diag, assay, marker) in TARGET_PRIORITY.items():
        best_candidates = [row for row in diff_rows if row["species"] == species]
        if not best_candidates:
            continue
        expected = by_pair.get((expected_diag, species))
        best = max(best_candidates, key=lambda row: float(row["priority_score"]))
        chosen = expected or best
        rationale = []
        if chosen["diagnosis"] == expected_diag:
            rationale.append("matches_expected_clinical_group")
        if deep_stable.get(species, 0):
            rationale.append(f"deep_review_stable_n={deep_stable[species]}")
        if float(chosen["detect_rate_delta"]) > 0:
            rationale.append("higher_detection_than_other_groups")
        if float(chosen["group_median_fraction"]) > 0:
            rationale.append("nonzero_group_median_fraction")
        q_value = float(chosen["bh_fdr"])
        if q_value < 0.05 and chosen["diagnosis"] == expected_diag:
            evidence_tier = "tier1_group_enriched"
        elif q_value < 0.20 and chosen["diagnosis"] == expected_diag:
            evidence_tier = "tier2_suggestive_group_enrichment"
        elif deep_stable.get(species, 0):
            evidence_tier = "tier3_deep_review_case_confirmation"
        else:
            evidence_tier = "tier4_exploratory"
        target_rows.append(
            {
                "species": species,
                "evidence_tier": evidence_tier,
                "recommended_validation_group": chosen["diagnosis"],
                "expected_biology_group": expected_diag,
                "assay": assay,
                "suggested_marker": marker,
                "group_detected": chosen["group_detected"],
                "group_total": chosen["group_total"],
                "group_detect_rate": chosen["group_detect_rate"],
                "rest_detect_rate": chosen["rest_detect_rate"],
                "detect_rate_delta": chosen["detect_rate_delta"],
                "group_median_fraction": chosen["group_median_fraction"],
                "fisher_p": chosen["fisher_p"],
                "bh_fdr": chosen["bh_fdr"],
                "rationale": ";".join(rationale) if rationale else "exploratory_only",
            }
        )
    target_rows.sort(
        key=lambda row: (
            row["evidence_tier"],
            row["recommended_validation_group"] != row["expected_biology_group"],
            float(row["bh_fdr"]),
            -float(row["detect_rate_delta"]),
        )
    )

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(out_dir / "group_species_differential.tsv", diff_rows, list(diff_rows[0].keys()))
    write_tsv(out_dir / "wetlab_validation_candidates.tsv", target_rows, list(target_rows[0].keys()))

    group_top_rows: list[dict[str, Any]] = []
    for diag in diagnoses:
        subset = [
            row
            for row in diff_rows
            if row["diagnosis"] == diag
            and row["context"] != "background_or_low_specificity"
            and float(row["detect_rate_delta"]) > 0
        ]
        subset.sort(key=lambda row: (row["context"] != "wetlab_priority_pathogen", float(row["bh_fdr"]), -float(row["detect_rate_delta"])))
        for rank, row in enumerate(subset[:20], start=1):
            out = {"rank": rank}
            out.update(row)
            group_top_rows.append(out)
    write_tsv(out_dir / "top_group_enriched_species.tsv", group_top_rows, list(group_top_rows[0].keys()))

    summary = {
        "runs": len(usable_runs),
        "diagnosis_counts": {diag: len(runs) for diag, runs in diag_runs.items()},
        "species_tested": len(matrix),
        "differential_rows": len(diff_rows),
        "wetlab_candidates": len(target_rows),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# PRJNA1056765 Group Differential Summary",
        "",
        "## Scope",
        "",
        f"- Runs analyzed: {len(usable_runs)}",
        "- Groups: " + ", ".join(f"{diag}={len(runs)}" for diag, runs in diag_runs.items()),
        "- Test: species detection in one diagnosis group versus all other groups by two-sided Fisher exact test; BH-FDR reported.",
        "- Abundance metric: Bracken species fraction; medians include zero values.",
        "",
        "## Wet-Lab Candidate Targets",
        "",
    ]
    for row in target_rows[:10]:
        lines.append(
            f"- {row['species']} ({row['recommended_validation_group']}): "
            f"detect {row['group_detected']}/{row['group_total']} vs rest rate {row['rest_detect_rate']}, "
            f"FDR {row['bh_fdr']}, {row['evidence_tier']}, marker {row['suggested_marker']}"
        )
    lines.extend(
        [
            "",
            "## Practical Short-Project Recommendation",
            "",
            "- For the shortest publishable wet-lab module, prioritize tier1/tier2 targets: P. aeruginosa, M. tuberculosis, Aspergillus fumigatus, and Cryptococcus neoformans.",
            "- Treat K. pneumoniae, A. baumannii, S. aureus, and Candida albicans as deep-review/case-confirmation targets unless new local samples show stronger group-level separation.",
            "- M. tuberculosis should only be used if the available lab workflow and biosafety approvals are already in place; otherwise keep it as a bioinformatic validation endpoint.",
            "- Use Lung cancer BALF samples as disease controls rather than healthy controls; the public dataset does not provide true healthy BALF controls.",
            "- Report background/low-specificity taxa separately; do not use recurring Homo sapiens, Toxoplasma gondii, or plant taxa as biological findings.",
            "",
            "## Output Files",
            "",
            "- `group_species_differential.tsv`",
            "- `top_group_enriched_species.tsv`",
            "- `wetlab_validation_candidates.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
