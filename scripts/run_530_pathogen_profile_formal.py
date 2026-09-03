#!/usr/bin/env python3
"""Frozen cohort-specific pathogen-profile analysis for 530 BALF samples."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_530_pathogen_landscape import EXPECTED, read_groups, read_matrix

PRIMARY_THRESHOLD = 5
THRESHOLDS = (1, 5, 10)
R_BIN = Path("/home/suma/anaconda3/envs/mgshotgun/bin/Rscript")
MGSHOTGUN_BIN = "/home/suma/anaconda3/envs/mgshotgun/bin"
CONTRACT = ROOT / "provenance/pathogen_profile/pathogen_panel_threshold_v1.json"
CORE = "A"
CONTEXT = "B"
STUDY = "S"
GROUP_ORDER = {
    "anchor": ("Bacterial infection", "Fungal infection", "Lung cancer", "Pulmonary tuberculosis"),
    "external": ("Drug_Resistance", "Drug_Sensitive"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else ["empty"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_table(root: Path, stem: str, rows: list[dict[str, Any]]) -> None:
    write_tsv(root / f"{stem}.tsv", rows)
    (root / f"{stem}.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def adjust_bh(values: list[float]) -> list[float]:
    n = len(values)
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [1.0] * n
    running = 1.0
    for rank, (index, value) in reversed(list(enumerate(ordered, 1))):
        running = min(running, value * n / rank)
        adjusted[index] = min(1.0, running)
    return adjusted


def adjust_holm(values: list[float]) -> list[float]:
    n = len(values)
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [1.0] * n
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, (n - rank) * value)
        adjusted[index] = min(1.0, running)
    return adjusted


def load_contract() -> tuple[dict[str, Any], list[dict[str, str]]]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    panel = contract["panel"]
    if contract["decision_status"] != "FROZEN_BEFORE_HYPOTHESIS_TESTING":
        raise ValueError("pathogen method decision is not frozen")
    if contract["primary_threshold_direct_assigned_reads_greater_or_equal"] != 5 or contract["sensitivity_thresholds_direct_assigned_reads_greater_or_equal"] != [1, 10]:
        raise ValueError("threshold contract mismatch")
    if Counter(row["category"] for row in panel) != Counter({"A": 6, "B": 4, "S": 1}) or len(panel) != 11:
        raise ValueError("panel category contract mismatch")
    if {row["taxid"] for row in panel} != {"470", "5207", "562", "727", "573", "480", "1773", "287", "1280", "40324", "1313"}:
        raise ValueError("panel identity contract mismatch")
    return contract, panel


def r_environment() -> dict[str, str]:
    env = dict(os.environ)
    remainder = [part for part in env.get("PATH", "").split(os.pathsep) if part and part != MGSHOTGUN_BIN]
    env["PATH"] = os.pathsep.join([MGSHOTGUN_BIN, *remainder])
    return env


def run_r_specs(root: Path, specs: list[dict[str, Any]], stem: str) -> dict[str, dict[str, Any]]:
    if not specs:
        return {}
    input_path, output_path = root / f".{stem}_input.tsv", root / f".{stem}_output.tsv"
    write_tsv(input_path, specs, ["test_id", "type", "counts", "nrow", "ncol", "seed"])
    completed = subprocess.run([str(R_BIN), "--vanilla", str(ROOT / "scripts/pathogen_profile_stats.R"), str(input_path), str(output_path)],
                               env=r_environment(), text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError("base-R statistical helper failed: " + " ".join(completed.stderr.split())[:1000])
    with output_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != len(specs) or {row["test_id"] for row in rows} != {row["test_id"] for row in specs}:
        raise RuntimeError("base-R statistical result identity mismatch")
    for path in (input_path, output_path):
        path.unlink()
    numeric = ("statistic", "df", "p_value", "estimate", "ci_low", "ci_high")
    for row in rows:
        for key in numeric:
            row[key] = float(row[key]) if row[key] else None
    return {row["test_id"]: row for row in rows}


def layer(category: str) -> str:
    return "CORE_A;FULL_PANEL" if category == CORE else "FULL_PANEL" if category == CONTEXT else "STUDY_DEFINING"


def classify_robustness(*, primary_positive_n: int, retention: float, same_direction: bool, similar_magnitude: bool) -> str:
    if primary_positive_n < 10 or retention < 0.5:
        return "LOW_COUNT_UNSTABLE"
    return "ROBUST" if same_direction and similar_magnitude else "THRESHOLD_SENSITIVE"


def prepare_data(panel: list[dict[str, str]], count_paths: dict[str, Path], metadata_paths: dict[str, Path]):
    data = {}
    for cohort in ("anchor", "external"):
        matrix = read_matrix(count_paths[cohort], cohort)
        groups = read_groups(metadata_paths[cohort], cohort)
        if set(matrix["sample_ids"]) != set(groups):
            raise ValueError(f"{cohort} matrix/metadata sample mismatch")
        taxa = {row["taxid"]: row for row in matrix["taxa"]}
        for item in panel:
            if item["taxid"] not in taxa or taxa[item["taxid"]]["scientific_name"] != item["scientific_name"]:
                raise ValueError(f"{cohort} frozen panel taxid/name missing: {item['taxid']}")
        data[cohort] = {"matrix": matrix, "groups": groups, "taxa": taxa}
    if set(data["anchor"]["matrix"]["sample_ids"]) & set(data["external"]["matrix"]["sample_ids"]):
        raise ValueError("cohort sample overlap")
    return data


def prevalence_and_tests(root: Path, panel: list[dict[str, str]], data: dict[str, Any]):
    prevalence_rows, anchor_rows, external_rows, specs = [], [], [], []
    for cohort in ("anchor", "external"):
        sample_ids, groups = data[cohort]["matrix"]["sample_ids"], data[cohort]["groups"]
        for threshold in THRESHOLDS:
            for item in panel:
                values = data[cohort]["taxa"][item["taxid"]]["counts"]
                group_counts = []
                for group in GROUP_ORDER[cohort]:
                    indices = [index for index, sample in enumerate(sample_ids) if groups[sample] == group]
                    positive = sum(values[index] >= threshold for index in indices)
                    ci_id = f"ci|{cohort}|{threshold}|{item['taxid']}|{group}"
                    specs.append({"test_id": ci_id, "type": "prevalence_ci", "counts": f"{positive},{len(indices)}", "nrow": 1, "ncol": 2, "seed": 1})
                    prevalence_rows.append({
                        "cohort": cohort, "threshold": threshold, "analysis_role": "PRIMARY" if threshold == 5 else "SENSITIVITY",
                        "result_layer": layer(item["category"]), "category": item["category"], "taxid": item["taxid"],
                        "scientific_name": item["scientific_name"], "clinical_group": group,
                        "positive_n": positive, "group_n": len(indices), "prevalence": positive / len(indices), "ci_test_id": ci_id,
                    })
                    group_counts.extend([positive, len(indices) - positive])
                if cohort == "anchor":
                    test_id = f"anchor_global|{threshold}|{item['taxid']}"
                    specs.append({"test_id": test_id, "type": "global", "counts": ",".join(map(str, group_counts)), "nrow": 4, "ncol": 2,
                                  "seed": 530000 + threshold * 100 + int(item["taxid"]) % 997})
                    anchor_rows.append({"threshold": threshold, "analysis_role": "PRIMARY" if threshold == 5 else "SENSITIVITY",
                                        "result_layer": layer(item["category"]), **item, "test_id": test_id})
                else:
                    test_id = f"external_assoc|{threshold}|{item['taxid']}"
                    specs.append({"test_id": test_id, "type": "fisher_2x2", "counts": ",".join(map(str, group_counts)), "nrow": 2, "ncol": 2, "seed": 1})
                    external_rows.append({"threshold": threshold, "analysis_role": "PRIMARY" if threshold == 5 else "SENSITIVITY",
                                          "result_layer": layer(item["category"]), **item, "test_id": test_id,
                                          "orientation": "odds_ratio_Drug_Resistance_vs_Drug_Sensitive"})
    r = run_r_specs(root, specs, "stage1")
    for row in prevalence_rows:
        result = r[row.pop("ci_test_id")]
        row["prevalence_ci95_low"] = result["ci_low"]
        row["prevalence_ci95_high"] = result["ci_high"]
        row["ci_method"] = result["method"]
    for rows in (anchor_rows, external_rows):
        for row in rows:
            result = r[row.pop("test_id")]
            row.update({key: result[key] for key in ("method", "statistic", "df", "p_value")})
            if rows is external_rows:
                row.update({"odds_ratio": result["estimate"], "odds_ratio_ci95_low": result["ci_low"], "odds_ratio_ci95_high": result["ci_high"]})
    for rows in (anchor_rows, external_rows):
        for threshold in THRESHOLDS:
            cells = [row for row in rows if row["threshold"] == threshold]
            full = [row for row in cells if row["category"] in (CORE, CONTEXT)]
            core = [row for row in cells if row["category"] == CORE]
            for subset, key in ((full, "bh_fdr_full_panel"), (core, "bh_fdr_core_a")):
                for row, value in zip(subset, adjust_bh([row["p_value"] for row in subset])):
                    row[key] = value
            for row in cells:
                row.setdefault("bh_fdr_full_panel", None)
                row.setdefault("bh_fdr_core_a", None)
                row["multiplicity_scope_for_interpretation"] = "CORE_A" if row["category"] == CORE else "FULL_PANEL" if row["category"] == CONTEXT else "STUDY_DEFINING_SINGLETON"
                row["gate_q_or_p"] = row["bh_fdr_core_a"] if row["category"] == CORE else row["bh_fdr_full_panel"] if row["category"] == CONTEXT else row["p_value"]
    return prevalence_rows, anchor_rows, external_rows


def gated_anchor_pairwise(root: Path, panel: list[dict[str, str]], data: dict[str, Any], anchor_rows: list[dict[str, Any]]):
    specs, rows = [], []
    sample_ids, groups = data["anchor"]["matrix"]["sample_ids"], data["anchor"]["groups"]
    for global_row in anchor_rows:
        if global_row["gate_q_or_p"] >= 0.05:
            continue
        item = next(item for item in panel if item["taxid"] == global_row["taxid"])
        values = data["anchor"]["taxa"][item["taxid"]]["counts"]
        for first, second in combinations(GROUP_ORDER["anchor"], 2):
            counts = []
            prevalences = []
            for group in (first, second):
                indices = [i for i, sample in enumerate(sample_ids) if groups[sample] == group]
                positive = sum(values[i] >= global_row["threshold"] for i in indices)
                counts.extend([positive, len(indices) - positive])
                prevalences.append(positive / len(indices))
            test_id = f"anchor_pair|{global_row['threshold']}|{item['taxid']}|{first}|{second}"
            specs.append({"test_id": test_id, "type": "fisher_2x2", "counts": ",".join(map(str, counts)), "nrow": 2, "ncol": 2, "seed": 1})
            rows.append({"threshold": global_row["threshold"], "analysis_role": global_row["analysis_role"],
                         "result_layer": global_row["result_layer"], **item, "group_1": first, "group_2": second,
                         "prevalence_group_1": prevalences[0], "prevalence_group_2": prevalences[1],
                         "absolute_prevalence_difference": prevalences[0] - prevalences[1], "test_id": test_id,
                         "omnibus_gate_value": global_row["gate_q_or_p"]})
    r = run_r_specs(root, specs, "pairwise")
    for row in rows:
        result = r[row.pop("test_id")]
        row.update({"method": result["method"], "odds_ratio": result["estimate"], "odds_ratio_ci95_low": result["ci_low"],
                    "odds_ratio_ci95_high": result["ci_high"], "p_value": result["p_value"]})
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["threshold"], row["taxid"])].append(row)
    for cells in grouped.values():
        for row, value in zip(cells, adjust_holm([row["p_value"] for row in cells])):
            row["holm_adjusted_p_within_gated_pathogen"] = value
    return rows


def burden(root: Path, panel: list[dict[str, str]], data: dict[str, Any]):
    rows, specs = [], []
    sets = {"CORE_A": {item["taxid"] for item in panel if item["category"] == CORE},
            "FULL_PANEL": {item["taxid"] for item in panel if item["category"] in (CORE, CONTEXT)}}
    for cohort in ("anchor", "external"):
        sample_ids, groups = data[cohort]["matrix"]["sample_ids"], data[cohort]["groups"]
        for panel_layer, taxids in sets.items():
            table_counts = []
            for group in GROUP_ORDER[cohort]:
                indices = [i for i, sample in enumerate(sample_ids) if groups[sample] == group]
                burdens = [sum(data[cohort]["taxa"][taxid]["counts"][i] >= 5 for taxid in taxids) for i in indices]
                category_counts = Counter("0" if value == 0 else "1" if value == 1 else "2" if value == 2 else "greater_or_equal_3" for value in burdens)
                for category in ("0", "1", "2", "greater_or_equal_3"):
                    rows.append({"cohort": cohort, "panel_layer": panel_layer, "threshold": 5, "clinical_group": group,
                                 "burden_category": category, "sample_n": category_counts[category],
                                 "group_n": len(indices), "proportion": category_counts[category] / len(indices)})
                    table_counts.append(category_counts[category])
            test_id = f"burden|{cohort}|{panel_layer}"
            specs.append({"test_id": test_id, "type": "global", "counts": ",".join(map(str, table_counts)),
                          "nrow": len(GROUP_ORDER[cohort]), "ncol": 4, "seed": 531000 + len(taxids)})
    r = run_r_specs(root, specs, "burden")
    tests = [{"cohort": test_id.split("|")[1], "panel_layer": test_id.split("|")[2], "threshold": 5,
              **{key: value for key, value in result.items() if key != "test_id"}} for test_id, result in sorted(r.items())]
    return rows, tests


def dominant_and_codetection(panel: list[dict[str, str]], data: dict[str, Any]):
    dominant_rows, codetection_rows = [], []
    sets = {"CORE_A": [item for item in panel if item["category"] == CORE],
            "FULL_PANEL": [item for item in panel if item["category"] in (CORE, CONTEXT)]}
    for cohort in ("anchor", "external"):
        sample_ids, groups = data[cohort]["matrix"]["sample_ids"], data[cohort]["groups"]
        core = sets["CORE_A"]
        group_dominant: dict[str, Counter[str]] = defaultdict(Counter)
        group_ties: Counter[str] = Counter()
        group_eligible: Counter[str] = Counter()
        for i, sample in enumerate(sample_ids):
            positive = [(item, data[cohort]["taxa"][item["taxid"]]["counts"][i]) for item in core if data[cohort]["taxa"][item["taxid"]]["counts"][i] >= 5]
            if not positive:
                continue
            group, maximum = groups[sample], max(value for _, value in positive)
            leaders = sorted((item for item, value in positive if value == maximum), key=lambda item: int(item["taxid"]))
            selected = leaders[0]
            group_eligible[group] += 1
            group_ties[group] += len(leaders) > 1
            group_dominant[group][selected["scientific_name"]] += 1
        for group in GROUP_ORDER[cohort]:
            for item in core:
                count = group_dominant[group][item["scientific_name"]]
                dominant_rows.append({"cohort": cohort, "clinical_group": group, "taxid": item["taxid"],
                                      "scientific_name": item["scientific_name"], "dominant_n": count,
                                      "eligible_sample_n": group_eligible[group],
                                      "dominant_proportion": count / group_eligible[group] if group_eligible[group] else None,
                                      "group_tie_sample_n": group_ties[group],
                                      "tie_rule": "highest direct reads then ascending numeric taxid"})
        for panel_layer, items in sets.items():
            for first, second in combinations(items, 2):
                selected = [i for i in range(len(sample_ids)) if data[cohort]["taxa"][first["taxid"]]["counts"][i] >= 5 and data[cohort]["taxa"][second["taxid"]]["counts"][i] >= 5]
                if len(selected) < 5:
                    continue
                by_group = Counter(groups[sample_ids[i]] for i in selected)
                codetection_rows.append({"cohort": cohort, "panel_layer": panel_layer, "threshold": 5,
                                         "taxid_1": first["taxid"], "pathogen_1": first["scientific_name"],
                                         "taxid_2": second["taxid"], "pathogen_2": second["scientific_name"],
                                         "co_detection_n": len(selected), "co_detection_prevalence": len(selected) / len(sample_ids),
                                         "clinical_group_counts": json.dumps(dict(by_group), sort_keys=True, separators=(",", ":")),
                                         "interpretation": "co-detection only; no interaction or synergy inference"})
    return dominant_rows, codetection_rows


def robustness(panel: list[dict[str, str]], data: dict[str, Any], anchor: list[dict[str, Any]], external: list[dict[str, Any]]):
    rows = []
    test_map = {("anchor", row["threshold"], row["taxid"]): row for row in anchor} | {("external", row["threshold"], row["taxid"]): row for row in external}
    for cohort in ("anchor", "external"):
        sample_ids, groups = data[cohort]["matrix"]["sample_ids"], data[cohort]["groups"]
        for item in panel:
            values = data[cohort]["taxa"][item["taxid"]]["counts"]
            effects, directions, positive_counts = {}, {}, {}
            for threshold in THRESHOLDS:
                rates = {}
                for group in GROUP_ORDER[cohort]:
                    indices = [i for i, sample in enumerate(sample_ids) if groups[sample] == group]
                    rates[group] = sum(values[i] >= threshold for i in indices) / len(indices)
                positive_counts[threshold] = sum(value >= threshold for value in values)
                if cohort == "external":
                    effects[threshold] = rates["Drug_Resistance"] - rates["Drug_Sensitive"]
                    directions[threshold] = "Drug_Resistance_higher" if effects[threshold] > 0 else "Drug_Sensitive_higher" if effects[threshold] < 0 else "equal"
                else:
                    highest = sorted(rates, key=lambda group: (-rates[group], group))[0]
                    effects[threshold] = rates[highest] - statistics.mean(value for group, value in rates.items() if group != highest)
                    directions[threshold] = highest
            retained = positive_counts[5] / positive_counts[1] if positive_counts[1] else 0
            same_direction = len(set(directions.values())) == 1 and "equal" not in directions.values()
            primary_magnitude = abs(effects[5])
            similar = primary_magnitude > 0 and all(0.5 <= abs(effects[t]) / primary_magnitude <= 2.0 for t in (1, 10))
            classification = classify_robustness(primary_positive_n=positive_counts[5], retention=retained,
                                                 same_direction=same_direction, similar_magnitude=similar)
            rows.append({
                "cohort": cohort, **item, "positive_n_ge1": positive_counts[1], "positive_n_ge5": positive_counts[5], "positive_n_ge10": positive_counts[10],
                "retention_ge5_vs_ge1": retained, "direction_ge1": directions[1], "direction_ge5": directions[5], "direction_ge10": directions[10],
                "effect_ge1": effects[1], "effect_ge5": effects[5], "effect_ge10": effects[10],
                "p_ge1": test_map[(cohort, 1, item["taxid"])]["p_value"], "p_ge5": test_map[(cohort, 5, item["taxid"])]["p_value"], "p_ge10": test_map[(cohort, 10, item["taxid"])]["p_value"],
                "q_scope_ge1": test_map[(cohort, 1, item["taxid"])]["gate_q_or_p"], "q_scope_ge5": test_map[(cohort, 5, item["taxid"])]["gate_q_or_p"], "q_scope_ge10": test_map[(cohort, 10, item["taxid"])]["gate_q_or_p"],
                "robustness": classification,
                "rule": "LOW_COUNT_UNSTABLE if primary ge5 positives <10 or <50% of ge1 detections remain at ge5; otherwise ROBUST requires same direction and sensitivity effect magnitudes 0.5x-2x primary; else THRESHOLD_SENSITIVE",
            })
    return rows


def jaccard_suitability(panel: list[dict[str, str]], data: dict[str, Any]):
    results = {}
    core = [item for item in panel if item["category"] == CORE]
    for cohort in ("anchor", "external"):
        sample_ids, groups = data[cohort]["matrix"]["sample_ids"], data[cohort]["groups"]
        profiles = [tuple(int(data[cohort]["taxa"][item["taxid"]]["counts"][i] >= 5) for item in core) for i in range(len(sample_ids))]
        all_zero = sum(not any(row) for row in profiles)
        max_identical = max(Counter(profiles).values())
        group_nonzero = {group: sum(any(profiles[i]) for i, sample in enumerate(sample_ids) if groups[sample] == group) for group in GROUP_ORDER[cohort]}
        suitable = len(set(profiles)) >= 8 and all_zero / len(profiles) <= 0.25 and max_identical / len(profiles) <= 0.25 and min(group_nonzero.values()) >= 10
        results[cohort] = {"status": "RUN" if suitable else "NOT_RUN", "unique_profiles": len(set(profiles)),
                           "all_zero_n": all_zero, "all_zero_proportion": all_zero / len(profiles),
                           "largest_identical_profile_n": max_identical, "largest_identical_profile_proportion": max_identical / len(profiles),
                           "nonzero_profiles_by_group": group_nonzero,
                           "criteria": "unique>=8; all-zero<=25%; largest identical profile<=25%; every group>=10 nonzero",
                           "reason": None if suitable else "NOT_RUN_WITH_REASON: prespecified binary-profile variation criteria failed"}
        if suitable:
            raise RuntimeError("Jaccard suitability unexpectedly passed; reviewed implementation is required before execution")
    return results


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--external-counts", type=Path, required=True)
    parser.add_argument("--anchor-metadata", type=Path, required=True)
    parser.add_argument("--external-metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists():
        raise RuntimeError("formal output directory already exists")
    args.output_dir.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    contract, panel = load_contract()
    count_paths = {"anchor": args.anchor_counts, "external": args.external_counts}
    metadata_paths = {"anchor": args.anchor_metadata, "external": args.external_metadata}
    data = prepare_data(panel, count_paths, metadata_paths)
    prevalence, anchor_tests, external_tests = prevalence_and_tests(args.output_dir, panel, data)
    pairwise = gated_anchor_pairwise(args.output_dir, panel, data, anchor_tests)
    burden_rows, burden_tests = burden(args.output_dir, panel, data)
    dominant, codetection = dominant_and_codetection(panel, data)
    robust = robustness(panel, data, anchor_tests, external_tests)
    jaccard = jaccard_suitability(panel, data)

    for threshold, stem in ((5, "pathogen_primary_ge5"), (1, "pathogen_sensitivity_ge1"), (10, "pathogen_sensitivity_ge10")):
        write_table(args.output_dir, stem, [row for row in prevalence if row["threshold"] == threshold])
    write_table(args.output_dir, "anchor_pathogen_global_tests", anchor_tests)
    write_table(args.output_dir, "anchor_pathogen_pairwise", pairwise)
    write_table(args.output_dir, "external_pathogen_associations", external_tests)
    write_table(args.output_dir, "threshold_robustness", robust)
    write_table(args.output_dir, "core_pathogen_burden", [row for row in burden_rows if row["panel_layer"] == "CORE_A"])
    write_table(args.output_dir, "full_panel_burden", [row for row in burden_rows if row["panel_layer"] == "FULL_PANEL"])
    write_table(args.output_dir, "pathogen_burden_global_tests", burden_tests)
    write_table(args.output_dir, "dominant_pathogen_by_group", dominant)
    write_table(args.output_dir, "pathogen_codetection_ge5", codetection)
    (args.output_dir / "jaccard_suitability.json").write_text(json.dumps(jaccard, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    primary_anchor = [row for row in anchor_tests if row["threshold"] == 5]
    primary_external = [row for row in external_tests if row["threshold"] == 5]
    sig_anchor_core = [row["scientific_name"] for row in primary_anchor if row["category"] == CORE and row["bh_fdr_core_a"] < 0.05]
    sig_external_core = [row["scientific_name"] for row in primary_external if row["category"] == CORE and row["bh_fdr_core_a"] < 0.05]
    robust_names = [f"{row['cohort']}:{row['scientific_name']}" for row in robust if row["robustness"] == "ROBUST"]
    sensitive_names = [f"{row['cohort']}:{row['scientific_name']}" for row in robust if row["robustness"] != "ROBUST"]
    summary = f"""# Formal cohort-specific pathogen-profile analysis

Primary operational detection was frozen at ≥5 direct-assigned Kraken2 species reads before hypothesis testing; ≥1 and ≥10 are sensitivity thresholds. This is not a clinically validated diagnostic threshold.

Anchor and external cohorts were analyzed independently. CORE_A, FULL_PANEL (A+B), and STUDY_DEFINING MTB results remain separated. External MTB is descriptive/study-defining and is excluded from non-MTB burden/profile endpoints.

Anchor significant CORE_A pathogens at primary BH-FDR: {', '.join(sig_anchor_core) if sig_anchor_core else 'none'}.
External significant non-MTB CORE_A pathogens at primary BH-FDR: {', '.join(sig_external_core) if sig_external_core else 'none'}.

Jaccard profile analysis was not run where the prespecified variation gate failed. Co-detection is not interpreted as interaction or coinfection. Direct-read fractions are not absolute pathogen load or etiologic certainty.

The prior CZM/CLR/Aitchison pathway was abandoned because real BALF profiles were highly sparse and inappropriate for the proposed default CZM replacement workflow.
"""
    (args.output_dir / "pathogen_analysis_summary.md").write_text(summary, encoding="utf-8")
    handoff_names = ["pathogen_primary_ge5.json", "pathogen_sensitivity_ge1.json", "pathogen_sensitivity_ge10.json",
                     "anchor_pathogen_global_tests.json", "anchor_pathogen_pairwise.json", "external_pathogen_associations.json",
                     "threshold_robustness.json", "core_pathogen_burden.json", "full_panel_burden.json",
                     "pathogen_burden_global_tests.json", "dominant_pathogen_by_group.json", "pathogen_codetection_ge5.json",
                     "jaccard_suitability.json", "pathogen_analysis_summary.md"]
    hashes = {name: sha256(args.output_dir / name) for name in handoff_names}
    (args.output_dir / "output_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    execution_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "job_id": args.job_id, "execution_commit": execution_commit, "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(), "method_contract_path": str(CONTRACT.relative_to(ROOT)),
        "method_contract_sha256": sha256(CONTRACT), "panel": panel, "primary_threshold_reads": 5,
        "sensitivity_thresholds": [1, 10], "selection_timing": contract["selection_timing"],
        "threshold_interpretation": contract["threshold_interpretation"], "abandoned_pathway": contract["abandoned_pathway"],
        "abandoned_pathway_reason": contract["abandoned_pathway_reason"],
        "input_hashes": {f"{cohort}_counts": sha256(count_paths[cohort]) for cohort in count_paths} |
                        {f"{cohort}_metadata": sha256(metadata_paths[cohort]) for cohort in metadata_paths},
        "sample_counts": {"anchor": 400, "external": 130}, "groups": {key: value["groups"] for key, value in EXPECTED.items()},
        "multiplicity": "BH separately within CORE_A(6) and FULL_PANEL(A+B,10); anchor pairwise Holm only after scope-adjusted omnibus gate",
        "robustness_rule": robust[0]["rule"], "jaccard_suitability": jaccard,
        "significant_anchor_core_fdr": sig_anchor_core, "significant_external_non_mtb_core_fdr": sig_external_core,
        "threshold_robust_associations": robust_names, "threshold_sensitive_or_low_count_associations": sensitive_names,
        "output_hashes": hashes, "analysis_manifest_and_output_hashes_exclude_themselves": True,
        "network_acquisition_performed": False, "package_installation_performed": False,
        "kraken2_rerun": False, "bracken_executed": False, "deepseek_invoked": False,
        "czm_executed": False, "clr_aitchison_executed": False, "pooled_530_model": False,
    }
    (args.output_dir / "pathogen_analysis_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
