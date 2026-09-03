#!/usr/bin/env python3
"""Descriptive read-threshold audit for the frozen 11-taxon BALF panel."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_530_pathogen_landscape import EXPECTED, quantiles, read_matrix

PANEL_SHA256 = "4e9339deadef7535620bd61901a0f61eb6c9114c83acb01df21a3a54aef3f0a2"
EXPECTED_PANEL = {
    "470": ("Acinetobacter baumannii", "plausible_opportunist"),
    "5207": ("Cryptococcus neoformans", "confirmed_known_respiratory_pathogen"),
    "562": ("Escherichia coli", "plausible_opportunist"),
    "727": ("Haemophilus influenzae", "confirmed_known_respiratory_pathogen"),
    "573": ("Klebsiella pneumoniae", "confirmed_known_respiratory_pathogen"),
    "480": ("Moraxella catarrhalis", "confirmed_known_respiratory_pathogen"),
    "1773": ("Mycobacterium tuberculosis", "confirmed_known_respiratory_pathogen"),
    "287": ("Pseudomonas aeruginosa", "confirmed_known_respiratory_pathogen"),
    "1280": ("Staphylococcus aureus", "confirmed_known_respiratory_pathogen"),
    "40324": ("Stenotrophomonas maltophilia", "plausible_opportunist"),
    "1313": ("Streptococcus pneumoniae", "confirmed_known_respiratory_pathogen"),
}
RETENTION_THRESHOLDS = (1, 2, 5, 10, 20, 50)
BURDEN_THRESHOLDS = (1, 2, 5, 10)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_table(output_dir: Path, stem: str, rows: list[dict[str, Any]]) -> None:
    write_tsv(output_dir / f"{stem}.tsv", rows)
    (output_dir / f"{stem}.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_panel(path: Path) -> list[dict[str, Any]]:
    if digest(path) != PANEL_SHA256:
        raise ValueError("candidate panel snapshot SHA256 mismatch")
    panel = json.loads(path.read_text(encoding="utf-8"))
    observed = {str(row["taxid"]): (row["scientific_name"], row["clinical_pathogen_relevance_flag"]) for row in panel}
    if len(panel) != 11 or observed != EXPECTED_PANEL:
        raise ValueError("exact 11-taxon panel identity/label contract failed")
    return panel


def count_bins(values: list[int]) -> dict[str, dict[str, float | int]]:
    bins = {
        "exactly_1": sum(value == 1 for value in values),
        "2_to_5": sum(2 <= value <= 5 for value in values),
        "6_to_10": sum(6 <= value <= 10 for value in values),
        "11_to_50": sum(11 <= value <= 50 for value in values),
        "51_to_100": sum(51 <= value <= 100 for value in values),
        "greater_than_100": sum(value > 100 for value in values),
    }
    n = len(values)
    return {key: {"n": count, "proportion": count / n if n else None} for key, count in bins.items()} | {
        "greater_than_1000_flag": {"n": sum(value > 1000 for value in values), "proportion": sum(value > 1000 for value in values) / n if n else None}
    }


def fraction_bins(values: list[float]) -> dict[str, dict[str, float | int]]:
    counts = {
        "less_than_0.1_percent": sum(value < 0.001 for value in values),
        "0.1_to_less_than_1_percent": sum(0.001 <= value < 0.01 for value in values),
        "1_to_less_than_10_percent": sum(0.01 <= value < 0.10 for value in values),
        "10_to_50_percent": sum(0.10 <= value <= 0.50 for value in values),
        "greater_than_50_percent": sum(value > 0.50 for value in values),
    }
    return {key: {"n": count, "proportion": count / len(values) if values else None} for key, count in counts.items()}


def shape_label(values: list[int]) -> dict[str, Any]:
    n = len(values)
    at_most_2 = sum(value <= 2 for value in values) / n
    at_most_5 = sum(value <= 5 for value in values) / n
    q = quantiles([float(value) for value in values])
    if at_most_2 >= 0.70:
        label = "strongly_concentrated_at_1_to_2_reads"
    elif at_most_5 >= 0.70:
        label = "low_read_dominated"
    elif q["q3"] is not None and q["q3"] <= 10 and q["maximum"] > 100:
        label = "clearly_right_skewed_with_high_signal_tail"
    else:
        label = "broadly_continuous_or_right_skewed"
    return {"descriptive_shape": label, "proportion_at_most_2": at_most_2,
            "proportion_at_most_5": at_most_5,
            "bimodality": "NOT_CLEARLY_SUPPORTED_BY_DESCRIPTIVE_AUDIT"}


def deterministic_ranks(matrix: dict[str, Any]) -> tuple[list[int], list[dict[str, int]]]:
    taxa, sample_ids = matrix["taxa"], matrix["sample_ids"]
    totals = [sum(taxon["counts"][i] for taxon in taxa) for i in range(len(sample_ids))]
    ranks = []
    for i in range(len(sample_ids)):
        ordered = sorted(
            ((taxon["taxid"], taxon["counts"][i]) for taxon in taxa if taxon["counts"][i] > 0),
            key=lambda item: (-item[1], int(item[0]) if item[0].isdigit() else item[0]),
        )
        ranks.append({taxid: rank for rank, (taxid, _value) in enumerate(ordered, 1)})
    return totals, ranks


def audit_cohort(cohort: str, matrix: dict[str, Any], panel: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    n = EXPECTED[cohort]["samples"]
    by_taxid = {taxon["taxid"]: taxon for taxon in matrix["taxa"]}
    totals, ranks = deterministic_ranks(matrix)
    audit_rows, retention_rows, signal_rows, dominance_rows, stability_rows = [], [], [], [], []
    panel_counts = {str(row["taxid"]): by_taxid[str(row["taxid"])] for row in panel}
    for panel_row in panel:
        taxid = str(panel_row["taxid"])
        taxon = panel_counts[taxid]
        if taxon["scientific_name"] != panel_row["scientific_name"]:
            raise ValueError(f"{cohort} panel taxid/name mismatch: {taxid}")
        positive_indices = [i for i, value in enumerate(taxon["counts"]) if value > 0]
        positive = [taxon["counts"][i] for i in positive_indices]
        fractions = [taxon["counts"][i] / totals[i] for i in positive_indices]
        positive_ranks = [ranks[i][taxid] for i in positive_indices]
        q = quantiles([float(value) for value in positive])
        bins = count_bins(positive)
        shape = shape_label(positive)
        current_category = "B" if panel_row["clinical_pathogen_relevance_flag"] == "plausible_opportunist" else "A"
        audit_rows.append({
            "cohort": cohort, "taxid": taxid, "scientific_name": taxon["scientific_name"],
            "current_relevance_label": panel_row["clinical_pathogen_relevance_flag"],
            "current_provisional_category": current_category, "n_positive_ge1": len(positive),
            "prevalence_ge1": len(positive) / n, **q, "mean": statistics.mean(positive),
            **{f"{key}_n": value["n"] for key, value in bins.items()},
            **{f"{key}_proportion": value["proportion"] for key, value in bins.items()},
            **shape,
        })
        for threshold in RETENTION_THRESHOLDS:
            count = sum(value >= threshold for value in taxon["counts"])
            retention_rows.append({"cohort": cohort, "taxid": taxid, "scientific_name": taxon["scientific_name"],
                                   "threshold_reads_greater_or_equal": threshold, "positive_n": count,
                                   "positive_proportion_all_samples": count / n})
        fq = quantiles(fractions)
        fb = fraction_bins(fractions)
        signal_rows.append({
            "cohort": cohort, "taxid": taxid, "scientific_name": taxon["scientific_name"],
            "n_positive": len(positive), "fraction_minimum": fq["minimum"], "fraction_q1": fq["q1"],
            "fraction_median": fq["median"], "fraction_q3": fq["q3"], "fraction_maximum": fq["maximum"],
            **{f"{key}_n": value["n"] for key, value in fb.items()},
            **{f"{key}_proportion": value["proportion"] for key, value in fb.items()},
        })
        for label, predicate in (
            ("1", lambda value: value == 1), ("2_to_5", lambda value: 2 <= value <= 5),
            ("6_to_10", lambda value: 6 <= value <= 10), ("greater_than_10", lambda value: value > 10),
        ):
            selected = [(value, rank) for value, rank in zip(positive, positive_ranks) if predicate(value)]
            dominance_rows.append({
                "cohort": cohort, "taxid": taxid, "scientific_name": taxon["scientific_name"],
                "read_bin": label, "n": len(selected), "top1_n": sum(rank == 1 for _, rank in selected),
                "top1_proportion": sum(rank == 1 for _, rank in selected) / len(selected) if selected else None,
                "top3_n": sum(rank <= 3 for _, rank in selected),
                "top3_proportion": sum(rank <= 3 for _, rank in selected) / len(selected) if selected else None,
                "median_rank_among_detected_species": statistics.median(rank for _, rank in selected) if selected else None,
                "rank_tie_rule": "descending direct reads then ascending numeric taxid",
            })
        base = len(positive)
        stability = {threshold: sum(value >= threshold for value in taxon["counts"]) for threshold in (2, 5, 10)}
        row = {"cohort": cohort, "taxid": taxid, "scientific_name": taxon["scientific_name"], "positive_ge1": base}
        for threshold, count in stability.items():
            relative = (base - count) / base if base else None
            row[f"ge1_to_ge{threshold}_percentage_point_reduction"] = (base - count) / n * 100
            row[f"ge1_to_ge{threshold}_relative_reduction"] = relative
        row["flag_gt25pct_disappear_at_ge2"] = row["ge1_to_ge2_relative_reduction"] > 0.25
        row["flag_gt50pct_disappear_at_ge5"] = row["ge1_to_ge5_relative_reduction"] > 0.50
        row["flag_gt75pct_disappear_at_ge10"] = row["ge1_to_ge10_relative_reduction"] > 0.75
        stability_rows.append(row)

    burden_rows = []
    for threshold in BURDEN_THRESHOLDS:
        burdens = [sum(taxon["counts"][i] >= threshold for taxon in panel_counts.values()) for i in range(n)]
        counts = Counter("0" if value == 0 else "1" if value == 1 else "2" if value == 2 else "greater_or_equal_3" for value in burdens)
        for category in ("0", "1", "2", "greater_or_equal_3"):
            burden_rows.append({"cohort": cohort, "threshold_reads_greater_or_equal": threshold,
                                "panel_pathogen_count_category": category, "sample_n": counts[category],
                                "sample_proportion": counts[category] / n})
    return {"audit": audit_rows, "retention": retention_rows, "signal": signal_rows,
            "dominance": dominance_rows, "burden": burden_rows, "stability": stability_rows}


def proposal(panel: list[dict[str, Any]], results: dict[str, dict[str, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    rows = []
    for panel_row in panel:
        taxid, name = str(panel_row["taxid"]), panel_row["scientific_name"]
        cells = [next(row for row in results[cohort]["audit"] if row["taxid"] == taxid) for cohort in ("anchor", "external")]
        dom = [row for cohort in ("anchor", "external") for row in results[cohort]["dominance"] if row["taxid"] == taxid]
        top1 = sum(row["top1_n"] for row in dom)
        positives = sum(row["n_positive_ge1"] for row in cells)
        low5 = sum(row["exactly_1_n"] + row["2_to_5_n"] for row in cells)
        if name == "Mycobacterium tuberculosis":
            category, special = "S", "STUDY_DEFINING_PATHOGEN_in_external_TB_cohort"
        elif name == "Cryptococcus neoformans" or panel_row["clinical_pathogen_relevance_flag"] == "plausible_opportunist":
            category, special = "B", "context_dependent_or_opportunistic"
        else:
            category, special = "A", "core_clinically_interpretable_candidate"
        rows.append({
            "taxid": taxid, "scientific_name": name, "proposed_category": category,
            "special_handling": special, "combined_positive_n": positives,
            "combined_low_read_1_to_5_proportion": low5 / positives,
            "combined_top1_when_positive_proportion": top1 / positives,
            "reason": "descriptive proposal only; identity/context plus observed prevalence, low-read fraction, and deterministic top-1 behavior; no group test or threshold optimization",
        })
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--external-counts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists():
        raise RuntimeError("audit output already exists")
    args.output_dir.mkdir(parents=True)
    panel = load_panel(args.panel)
    matrices = {"anchor": read_matrix(args.anchor_counts, "anchor"),
                "external": read_matrix(args.external_counts, "external")}
    results = {cohort: audit_cohort(cohort, matrices[cohort], panel) for cohort in ("anchor", "external")}
    tables = {
        "pathogen_read_threshold_audit": results["anchor"]["audit"] + results["external"]["audit"],
        "pathogen_threshold_retention": results["anchor"]["retention"] + results["external"]["retention"],
        "pathogen_signal_fraction": results["anchor"]["signal"] + results["external"]["signal"],
        "pathogen_dominance_by_read_bin": results["anchor"]["dominance"] + results["external"]["dominance"],
        "sample_panel_burden_by_threshold": results["anchor"]["burden"] + results["external"]["burden"],
        "pathogen_threshold_stability": results["anchor"]["stability"] + results["external"]["stability"],
    }
    for stem, rows in tables.items():
        write_table(args.output_dir, stem, rows)
    proposals = proposal(panel, results)
    (args.output_dir / "pathogen_panel_proposals.json").write_text(json.dumps(proposals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    review = ["# Pathogen read-threshold audit", "",
              "Descriptive audit only. No final positivity threshold or panel change was selected.", "",
              "The exact prior 11-taxon panel was recovered by SHA256. Mycobacterium tuberculosis is marked as a study-defining pathogen for the external TB cohort; Cryptococcus neoformans remains low-prevalence/context-dependent; Stenotrophomonas maltophilia remains opportunistic/context-dependent.", "",
              "Positive-read distributions, candidate-threshold retention, within-sample species-read fractions, deterministic dominance ranks, panel burden, and instability flags are available in the paired TSV/JSON tables. Fractions are classifier-signal proportions, not absolute pathogen load. Apparent co-detection is not called coinfection.", ""]
    (args.output_dir / "pathogen_panel_review_v2.md").write_text("\n".join(review), encoding="utf-8")
    summary = {
        "status": "PASS", "panel_size": 11, "panel_sha256": PANEL_SHA256,
        "cohorts": {"anchor": 400, "external": 130}, "proposals": proposals,
        "hypothesis_testing_executed": False, "fisher_executed": False,
        "fdr_executed": False, "jaccard_executed": False, "da_executed": False,
        "czm_executed": False, "clr_executed": False, "panel_changed": False,
        "final_positivity_threshold_selected": False, "network_acquisition_performed": False,
        "package_installation_performed": False, "kraken2_rerun": False,
        "bracken_executed": False, "deepseek_invoked": False,
    }
    (args.output_dir / "pathogen_read_threshold_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
