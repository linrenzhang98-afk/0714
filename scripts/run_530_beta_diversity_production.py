#!/usr/bin/env python3
"""Run the frozen two-cohort species beta-diversity grid and compact its audit handoff."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shotgun_analysis.production_package import GATE_JOB_ID, output_hashes, validate_pinned_czm_gate

EXPECTED = {
    "anchor": {"n": 400, "features": 5198, "groups": {"Bacterial infection": 114, "Fungal infection": 78, "Lung cancer": 122, "Pulmonary tuberculosis": 86}},
    "external": {"n": 130, "features": 4888, "groups": {"Drug_Resistance": 49, "Drug_Sensitive": 81}},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--anchor-manifest", type=Path, required=True)
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--anchor-sample-qc", type=Path, required=True)
    parser.add_argument("--external-manifest", type=Path, required=True)
    parser.add_argument("--external-counts", type=Path, required=True)
    parser.add_argument("--external-sample-qc", type=Path, required=True)
    parser.add_argument("--r-library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    started = datetime.now(timezone.utc).isoformat()
    gate = validate_pinned_czm_gate()
    if args.output_dir.exists():
        raise RuntimeError("production output directory already exists")
    args.output_dir.mkdir(parents=True)
    package_root = args.output_dir / "analysis_package"
    grid = Path(__file__).with_name("run_formal_cross_cohort_grid.py")
    inputs = {
        "anchor": (args.anchor_manifest, args.anchor_counts, args.anchor_sample_qc),
        "external": (args.external_manifest, args.external_counts, args.external_sample_qc),
    }
    for cohort, (manifest, counts, sample_qc) in inputs.items():
        command = [sys.executable, str(grid), "--cohort", cohort, "--manifest", str(manifest),
                   "--counts", str(counts), "--sample-qc", str(sample_qc),
                   "--r-library", str(args.r_library), "--output-root", str(package_root / cohort),
                   "--analysis-id", f"{args.job_id}:{cohort}", "--permutations", "9999"]
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            return completed.returncode

    cells = []
    sample_manifest = []
    feature_filters = []
    czm_provenance = []
    clr_provenance = []
    permanova = []
    permdisp = []
    session_versions = []
    for cohort in ("anchor", "external"):
        cohort_root = package_root / cohort
        for cell_dir in sorted(path for path in cohort_root.iterdir() if path.is_dir()):
            result = read_json(cell_dir / "result.json")
            cell = {"cohort": cohort, "cell": cell_dir.name, "analysis_role": result["analysis_role"],
                    "prevalence": result["feature_filter"]["threshold"],
                    "zero_method": result["zero_handling"]["zero_method"],
                    "distance": result["beta_diversity"]["distance"]}
            cells.append(cell)
            feature_filters.append({**cell, "prefilter_features": result["feature_filter"]["input_features"],
                                    "retained_features": result["feature_filter"]["retained_features"]})
            permanova.append({**cell, **result["beta_diversity"]["permanova"], "n": result["n"],
                              "retained_features": result["feature_filter"]["retained_features"]})
            permdisp.append({**cell, **result["beta_diversity"]["permdisp"], "n": result["n"],
                             "retained_features": result["feature_filter"]["retained_features"],
                             "dispersion_summary": result["beta_diversity"]["centroid_distances"]})
            if result["beta_diversity"]["distance"] == "Aitchison":
                clr_provenance.append({**cell, **read_json(cell_dir / "clr_provenance.json")})
            if result["zero_handling"]["zero_method"] == "CZM":
                czm_provenance.append({**cell, **read_json(cell_dir / "czm_provenance.json")})
                session_versions.append({**cell, **read_json(cell_dir / "session_versions.json")})
        primary = cohort_root / "aitchison_czm_prev10" / "sample_manifest.tsv"
        with primary.open(newline="", encoding="utf-8") as handle:
            sample_manifest.extend(csv.DictReader(handle, delimiter="\t"))

    anchor_ids = {row["sample_id"] for row in sample_manifest if row["cohort"] == "anchor"}
    external_ids = {row["sample_id"] for row in sample_manifest if row["cohort"] == "external"}
    if anchor_ids & external_ids or len(anchor_ids) != 400 or len(external_ids) != 130:
        raise RuntimeError("final sample identity/overlap contract failed")
    warnings = [{"code": "EXTERNAL_READ_LENGTH_SENSITIVITY_NOT_RUN",
                 "reason": "not implemented in the reviewed production grid; no categories inferred"}]
    outputs = {
        "sample_manifest.json": sample_manifest,
        "exclusions.json": [],
        "feature_filter_summary.json": feature_filters,
        "czm_provenance.json": czm_provenance,
        "clr_provenance.json": clr_provenance,
        "permanova_results.json": permanova,
        "permdisp_results.json": permdisp,
        "sensitivity_summary.json": {"authorized_cells": cells, "external_read_length_sensitivity": "NOT_RUN_WITH_REASON"},
        "warnings.json": warnings,
        "session_versions.json": {"python": platform.python_version(), "czm_cells": session_versions},
    }
    for name, payload in outputs.items():
        (args.output_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = (f"# Real 530-sample beta-diversity production\n\nJob: `{args.job_id}`\n\n"
               "Anchor and external cohorts were analyzed independently. Primary species CZM/CLR/Aitchison, "
               "PERMANOVA/PERMDISP, and frozen sensitivity cells are serialized in the JSON handoff. "
               "No pooled model, differential abundance, classifier rerun, download, or package installation was performed.\n")
    (args.output_dir / "production_summary.md").write_text(summary, encoding="utf-8")
    hash_names = sorted([*outputs, "production_summary.md"])
    hashes = output_hashes(args.output_dir, hash_names)
    (args.output_dir / "output_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    execution_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "job_id": args.job_id, "execution_commit": execution_commit,
        "input_hashes": {f"{cohort}_{kind}": digest(path) for cohort, paths in inputs.items()
                         for kind, path in zip(("metadata", "direct_species_counts", "sample_qc"), paths)},
        "sample_counts": {key: value["n"] for key, value in EXPECTED.items()},
        "group_counts": {key: value["groups"] for key, value in EXPECTED.items()},
        "prefilter_dimensions": {key: [value["n"], value["features"]] for key, value in EXPECTED.items()},
        "czm_gate": {"job_id": GATE_JOB_ID, "source_commit": "552826d5fdc7417bc35f867c0a4f63d996970733",
                     "validation_sha256": gate["source_validation_sha256"], "summary_sha256": gate["source_summary_sha256"]},
        "parameters": {"resolution": "species", "primary_prevalence": 0.10, "sensitivity_prevalence": [0.05, 0.20],
                       "pseudocount": 0.5, "permutations": 9999, "bray_curtis_prevalence": 0.10,
                       "pooled_model": False, "differential_abundance": False},
        "seeds": [{"cohort": row["cohort"], "cell": row["cell"], "permanova": row["seed"]} for row in permanova] +
                 [{"cohort": row["cohort"], "cell": row["cell"], "permdisp": row["seed"]} for row in permdisp],
        "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(), "warnings": warnings,
        "output_hashes": hashes, "hash_policy": "analysis_manifest.json and output_hashes.json exclude themselves",
        "network_acquisition_performed": False, "package_installation_performed": False,
        "classifier_rerun": False, "deepseek_invoked": False,
    }
    (args.output_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
