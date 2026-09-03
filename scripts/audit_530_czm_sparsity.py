#!/usr/bin/env python3
"""Aggregate-only real-count sparsity audit; performs no transformation or inference."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

THRESHOLDS = (0.05, 0.10, 0.20)
CUTS = (0.50, 0.70, 0.80, 0.85, 0.90, 0.95)
EXPECTED = {"anchor": (400, 5198), "external": (130, 4888)}
METADATA = {"taxid", "rank", "scientific_name", "prevalence", "present_5pct", "present_10pct", "present_20pct"}


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    def q(probability: float) -> float:
        position = (len(ordered) - 1) * probability
        lower = math.floor(position); upper = math.ceil(position)
        return ordered[lower] if lower == upper else ordered[lower] * (upper - position) + ordered[upper] * (position - lower)
    return {"minimum": ordered[0], "q1": q(0.25), "median": q(0.5), "q3": q(0.75), "maximum": ordered[-1]}


def distribution(values: list[float]) -> dict:
    return {"quantiles": quantiles(values),
            "strictly_greater": {str(cut): {"count": sum(value > cut for value in values),
                                             "proportion": sum(value > cut for value in values) / len(values)} for cut in CUTS},
            "greater_or_equal_0.80": {"count": sum(value >= 0.80 for value in values),
                                       "proportion": sum(value >= 0.80 for value in values) / len(values)}}


def read_matrix(path: Path, cohort: str) -> tuple[list[str], list[str], list[list[int]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("missing or duplicate count-table header")
        sample_ids = [name for name in reader.fieldnames if name not in METADATA]
        features = []
        rows = []
        for row_number, row in enumerate(reader, 2):
            if row.get("rank") != "S":
                raise ValueError(f"non-species row at {row_number}")
            taxid = str(row.get("taxid", "")).strip()
            if not taxid or taxid in features:
                raise ValueError(f"blank or duplicate deterministic taxid at {row_number}")
            features.append(taxid)
            values = []
            for sample in sample_ids:
                raw = row[sample]
                value = int(raw)
                if str(value) != raw.strip() or value < 0:
                    raise ValueError(f"invalid direct count at row {row_number}")
                values.append(value)
            rows.append(values)
    expected_samples, expected_features = EXPECTED[cohort]
    if len(sample_ids) != expected_samples or len(set(sample_ids)) != expected_samples or len(features) != expected_features:
        raise ValueError(f"{cohort} frozen dimensions/identities failed")
    return sample_ids, features, rows


def audit(path: Path, cohort: str) -> dict:
    sample_ids, features, feature_rows = read_matrix(path, cohort)
    sample_count = len(sample_ids)
    results = {}
    for threshold in THRESHOLDS:
        retained = [row for row in feature_rows if sum(value > 0 for value in row) / sample_count >= threshold]
        feature_zero = [sum(value == 0 for value in row) / sample_count for row in retained]
        sample_rows = [[row[index] for row in retained] for index in range(sample_count)]
        sample_zero = [sum(value == 0 for value in row) / len(retained) for row in sample_rows]
        totals = [sum(row) for row in sample_rows]
        nonzero = [value for row in sample_rows for value in row if value > 0]
        duplicate_groups = [count for count in Counter(tuple(row) for row in sample_rows).values() if count > 1]
        feature_dist = distribution(feature_zero)
        sample_dist = distribution(sample_zero)
        feature_gt80 = feature_dist["strictly_greater"]["0.8"]["count"]
        sample_gt80 = sample_dist["strictly_greater"]["0.8"]["count"]
        results[str(threshold)] = {
            "retained_species": len(retained),
            "feature_zero_fraction": feature_dist,
            "sample_zero_fraction": sample_dist,
            "sample_ids_strictly_gt_0.80_zero": [sample_ids[i] for i, value in enumerate(sample_zero) if value > 0.80],
            "default_cmultRepl_z_warning_0.8": {
                "violating_features": feature_gt80, "violating_samples": sample_gt80,
                "feature_proportion": feature_gt80 / len(retained), "sample_proportion": sample_gt80 / sample_count,
                "z_delete_true_would_change_dimensions": bool(feature_gt80 or sample_gt80),
                "compatible": not (feature_gt80 or sample_gt80),
                "boundary": "strictly greater than 0.80; equality is reported separately and is not counted as a violation",
            },
            "zero_total_samples": sum(total == 0 for total in totals),
            "zero_total_retained_species": sum(sum(row) == 0 for row in retained),
            "duplicate_sample_row_groups": len(duplicate_groups),
            "samples_in_duplicate_row_groups": sum(duplicate_groups),
            "minimum_nonzero_count": min(nonzero) if nonzero else None,
            "sample_total_direct_assigned_retained_counts": quantiles([float(value) for value in totals]),
        }
    return {
        "cohort": cohort,
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "artifact_orientation_before_filter": {"rows": "species", "columns": "samples", "dimensions": [len(features), len(sample_ids)]},
        "transformation_orientation_after_filter": {"rows": "samples", "columns": "retained_species"},
        "cmultRepl_required_orientation": {"rows": "observations/compositions (samples)", "columns": "components (species)"},
        "orientation_contract": "PASS",
        "thresholds": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--external-counts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise RuntimeError("audit output already exists")
    args.output_dir.mkdir(parents=True)
    summary = {"schema_version": 1, "analysis": "REAL_530_CZM_SPARSITY_COMPATIBILITY_AUDIT",
               "presence_definition": "count > 0", "cmultRepl_executed": False,
               "biological_inference_executed": False,
               "cohorts": {name: audit(path, name) for name, path in (("anchor", args.anchor_counts), ("external", args.external_counts))}}
    (args.output_dir / "sparsity_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Real 530-sample CZM sparsity compatibility audit", "",
             "No CZM replacement, CLR, distance, permutation test, differential abundance, or biological inference was executed.", ""]
    for cohort in ("anchor", "external"):
        data = summary["cohorts"][cohort]
        lines += [f"## {cohort.title()}", "", f"Input artifact: species rows × sample columns = {data['artifact_orientation_before_filter']['dimensions']}.",
                  "Transformation view: sample rows × retained-species columns.", ""]
        for threshold in THRESHOLDS:
            cell = data["thresholds"][str(threshold)]
            lines.append(f"- prevalence {threshold:.0%}: retained={cell['retained_species']}; features >80% zero={cell['default_cmultRepl_z_warning_0.8']['violating_features']}; samples >80% zero={cell['default_cmultRepl_z_warning_0.8']['violating_samples']}; compatible={cell['default_cmultRepl_z_warning_0.8']['compatible']}")
        lines.append("")
    lines += ["## Options for method review (not selected or implemented)", "",
              "- A — Keep 10% prevalence and raise `z.warning` enough to avoid deletion with `z.delete=TRUE`. Changes the frozen CZM parameterization; retains the prespecified feature/sample set and estimand, but weakens a diagnostic guard and requires an explicit justified bound recorded for reproducibility.",
              "- B — Use a prevalence threshold intrinsically compatible with the 80% rule. Changes the frozen primary prevalence and feature set; the cohort-specific compositional estimand remains related but not identical, with reduced sparse-feature burden and a threshold-selection/reproducibility concern.",
              "- C — Promote additive 0.5 CLR and demote CZM. Changes the frozen primary method while retaining samples/features and broad estimand; results can depend on arbitrary additive scale, though implementation is already authorized as sensitivity and reproducible.",
              "- D — No additional reviewed solution is currently implemented; any alternative requires separate method review and authorization.", "",
              "Classified/direct-assigned totals are technical count summaries, not biomass.", ""]
    (args.output_dir / "sparsity_audit.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
