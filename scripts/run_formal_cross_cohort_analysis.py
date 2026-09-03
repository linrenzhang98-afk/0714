#!/usr/bin/env python3
"""Production entry point for one frozen cohort at a time.

This command does not discover inputs and never pools cohorts. It is prepared
for later ETYY use but must not be run against biological matrices until the
runtime gate and analysis authorization are complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shotgun_analysis.czm import exact_czm
from shotgun_analysis.errors import InputValidationError
from shotgun_analysis.contracts import (
    COHORT_CONTRACTS, PRODUCTION_PERMUTATIONS, analysis_role, expected_production_seeds,
    validate_expected_czm_library,
    normalize_anchor_strata,
)
from shotgun_analysis.io import (
    load_common_layer_direct_species_counts, load_tsv, unique_row_index,
    validate_cohort_manifest, validate_sample_alignment,
)
from shotgun_analysis.pipeline import analyze_cohort, pseudocount_backend
from shotgun_analysis.results import write_compact_tsv, write_json
from shotgun_analysis.production_package import analysis_manifest, output_hashes, validate_pinned_czm_gate


COHORTS = {
    "anchor": {
        "project": COHORT_CONTRACTS["anchor"]["project"],
        "groups": COHORT_CONTRACTS["anchor"]["groups"],
        "manifest_columns": {"sample": "run", "run": "run", "group": "diagnosis", "stratum": "cohort"},
        "secondary_contrasts": [
            ("Lung cancer", "Bacterial infection"),
            ("Lung cancer", "Fungal infection"),
            ("Lung cancer", "Pulmonary tuberculosis"),
        ],
    },
    "external": {
        "project": COHORT_CONTRACTS["external"]["project"],
        "groups": COHORT_CONTRACTS["external"]["groups"],
        "manifest_columns": {"sample": "run_accession", "run": "run_accession", "group": "group_raw", "stratum": None},
        "binary_orientation": ("Drug_Resistance", "Drug_Sensitive"),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=sorted(COHORTS), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--sample-qc", type=Path, required=True)
    parser.add_argument("--r-library", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--prevalence", type=float, choices=(0.05, 0.10, 0.20), default=0.10)
    parser.add_argument("--zero-method", choices=("czm", "additive_pseudocount", "none"), default="czm")
    parser.add_argument("--geometry", choices=("Aitchison", "Bray-Curtis"), default="Aitchison")
    parser.add_argument("--permutations", type=int, choices=(PRODUCTION_PERMUTATIONS,), default=PRODUCTION_PERMUTATIONS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(timezone.utc).isoformat()
    # Reject an out-of-grid method combination before any input file is opened.
    analysis_role(args.prevalence, args.zero_method, args.geometry)
    gate = validate_pinned_czm_gate()
    czm_runtime: dict[str, object] = {}
    if args.zero_method == "czm":
        if args.r_library is None:
            raise SystemExit("--r-library is required for exact CZM")
        args.r_library = validate_expected_czm_library(args.r_library)
        # Runtime/package/path conformance is verified on synthetic values
        # before any biological manifest or count table is opened.
        exact_czm(
            [[1.0, 0.0], [0.0, 1.0]], r_library=args.r_library,
            runtime_provenance=czm_runtime,
        )
    contract = COHORTS[args.cohort]
    manifest = load_tsv(args.manifest)
    columns = contract["manifest_columns"]
    required = [columns["stratum"]] if columns["stratum"] else []
    validate_cohort_manifest(
        manifest, contract["groups"], sample_column=columns["sample"], run_column=columns["run"],
        group_column=columns["group"], required_columns=required,
    )
    manifest_ids = [row[columns["sample"]] for row in manifest]
    count_table = load_common_layer_direct_species_counts(args.counts, sorted(manifest_ids))
    validate_sample_alignment(manifest_ids, count_table.sample_ids)
    qc_rows = load_tsv(args.sample_qc)
    missing_qc_columns = {"run", "total_input_reads", "classified_reads"} - set(qc_rows[0])
    if missing_qc_columns:
        raise InputValidationError(f"sample-QC table is missing columns: {sorted(missing_qc_columns)}")
    qc_lookup = unique_row_index(qc_rows, "run", record_label="sample-QC run")
    validate_sample_alignment(manifest_ids, list(qc_lookup))
    manifest_by_id = {row[columns["sample"]]: row for row in manifest}
    manifest = [manifest_by_id[sample_id] for sample_id in count_table.sample_ids]
    manifest_ids = count_table.sample_ids
    matrix = count_table.matrix
    groups = [row[columns["group"]] for row in manifest]
    strata = [row[columns["stratum"]] for row in manifest] if columns["stratum"] else None
    if args.cohort == "anchor":
        strata = normalize_anchor_strata(strata or [])
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    if args.zero_method == "czm":
        replacement = lambda x: exact_czm(x, r_library=args.r_library, runtime_provenance=czm_runtime)
    elif args.zero_method == "additive_pseudocount":
        replacement = pseudocount_backend(0.5)
    else:
        replacement = None
    permanova_seed, permdisp_seed = expected_production_seeds(
        args.cohort, args.prevalence, args.zero_method, args.geometry,
    )
    try:
        implementation_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot resolve immutable implementation commit") from exc
    result = analyze_cohort(
        cohort_id=contract["project"], sample_ids=manifest_ids, groups=groups, counts=matrix,
        feature_names=count_table.feature_names,
        total_reads=[float(qc_lookup[sample_id]["total_input_reads"]) for sample_id in manifest_ids],
        classified_reads=[float(qc_lookup[sample_id]["classified_reads"]) for sample_id in manifest_ids],
        prevalence=args.prevalence, zero_method=args.zero_method,
        zero_replacement=replacement,
        permanova_seed=permanova_seed, permdisp_seed=permdisp_seed,
        permutations=args.permutations, strata=strata,
        secondary_contrasts=contract.get("secondary_contrasts", []),
        binary_orientation=contract.get("binary_orientation"),
        geometry=args.geometry, execution_mode="production", cohort_key=args.cohort,
        provenance={
            "python": platform.python_version(), "manifest_sha256": sha256(args.manifest),
            "counts_sha256": sha256(args.counts), "sample_qc_sha256": sha256(args.sample_qc),
            "czm_adapter_sha256": sha256(Path(__file__).resolve().parents[1] / "shotgun_analysis/run_czm.R"),
            "implementation_commit": implementation_commit,
            "method_runtime": czm_runtime if args.zero_method == "czm" else {
                "python": platform.python_version(), "R_required": False,
            },
        },
    )
    if result["analysis_status"] != "BIOLOGICAL":
        raise RuntimeError("production entry point received synthetic IDs")
    partial_output = args.output.with_name(args.output.name + ".partial")
    if args.output.exists() or partial_output.exists():
        raise RuntimeError("output and partial-output paths must not already exist")
    partial_output.mkdir(parents=True)
    schema = Path(__file__).resolve().parents[1] / "reports_public/formal_cross_cohort_analysis/result_schema.json"
    write_json(partial_output / "result.json", result, schema)
    fields = [
        "sample_id", "group", "richness", "shannon", "gini_simpson", "dominance",
        "classified_fraction", "total_input_reads", "classified_reads",
        "direct_species_assigned_reads", "centroid_distance", "zero_fraction_retained",
        "replacement_perturbation_total_variation",
    ]
    write_compact_tsv(partial_output / "sample_metrics.tsv", result["sample_metrics"], fields)
    beta_rows = []
    for test_name in ("permanova", "permdisp"):
        test = result["beta_diversity"][test_name]
        beta_rows.append({"cohort": result["cohort"], "test": test_name.upper(), **{key: test[key] for key in ("statistic", "effect_size", "p_value", "permutations", "seed", "df_between", "df_within")}})
    write_compact_tsv(partial_output / "beta_statistics.tsv", beta_rows, ["cohort", "test", "statistic", "effect_size", "p_value", "permutations", "seed", "df_between", "df_within"])
    write_compact_tsv(partial_output / "feature_filter.tsv", [{"cohort": result["cohort"], **{key: result["feature_filter"][key] for key in ("threshold", "input_features", "retained_features")}}], ["cohort", "threshold", "input_features", "retained_features"])
    secondary_rows = [{"cohort": result["cohort"], "endpoint": endpoint, **values} for endpoint, values in result["secondary_endpoints"].items()]
    secondary_fields = sorted({key for row in secondary_rows for key in row}, key=lambda key: (key not in {"cohort", "endpoint", "test"}, key))
    for row in secondary_rows:
        for field in secondary_fields:
            row.setdefault(field, "")
    write_compact_tsv(partial_output / "secondary_statistics.tsv", secondary_rows, secondary_fields)
    if result["secondary_contrasts"]:
        contrast_fields = sorted({key for row in result["secondary_contrasts"] for key in row}, key=lambda key: (key not in {"endpoint", "contrast", "test"}, key))
        write_compact_tsv(partial_output / "secondary_contrasts.tsv", result["secondary_contrasts"], contrast_fields)
    ordination = result["beta_diversity"]["ordination"]
    if ordination is not None:
        ordination_fields = ["sample_id", "group", *ordination["axis_labels"]]
        write_compact_tsv(partial_output / "ordination.tsv", ordination["sample_coordinates"], ordination_fields)
    taxon_zero_rows = result["zero_replacement_diagnostics"]["zero_fraction_per_taxon"]
    write_compact_tsv(partial_output / "taxon_zero_diagnostics.tsv", taxon_zero_rows, ["feature_id", "zero_fraction"])
    (partial_output / "execution_parameters.json").write_text(json.dumps(vars(args), default=str, indent=2) + "\n")
    sample_rows = [{"cohort": args.cohort, "sample_id": sample_id, "run_id": sample_id,
                    "status": "included", "clinical_group": groups[index],
                    "permutation_stratum": strata[index] if strata else "",
                    "input_source_sha256": result["provenance"]["counts_sha256"]}
                   for index, sample_id in enumerate(manifest_ids)]
    write_compact_tsv(partial_output / "sample_manifest.tsv", sample_rows,
                      ["cohort", "sample_id", "run_id", "status", "clinical_group", "permutation_stratum", "input_source_sha256"])
    (partial_output / "exclusions.tsv").write_text("cohort\tsample_id\treason\n", encoding="utf-8")
    write_json(partial_output / "feature_filter_summary.json", {"cohort": args.cohort, "resolution": "species", **result["feature_filter"]})
    write_json(partial_output / "czm_provenance.json", {"gate_job_id": gate["job_id"], "gate_evidence_sha256": gate.get("source_validation_sha256"),
               "isolated_library": str(args.r_library), "transformation": result["zero_handling"],
               "runtime": czm_runtime, "warnings": []})
    write_json(partial_output / "clr_provenance.json", result["composition_provenance"])
    for name in ("permanova", "permdisp"):
        write_json(partial_output / f"{name}_results.json", result["beta_diversity"][name])
        write_compact_tsv(partial_output / f"{name}_results.tsv", [{"cohort": args.cohort, **result["beta_diversity"][name]}],
                          ["cohort", "statistic", "effect_size", "p_value", "permutations", "seed", "df_between", "df_within", "group_counts", "algorithm"])
    write_json(partial_output / "sensitivity_summary.json", {"cell": result["analysis_role"], "prevalence": args.prevalence,
               "zero_method": args.zero_method, "geometry": args.geometry})
    write_json(partial_output / "warnings.json", {"warnings": []})
    write_json(partial_output / "session_versions.json", {"python": platform.python_version(), "R": czm_runtime.get("R_version"),
               "packages": {key: value for key, value in czm_runtime.items() if key.endswith("_version")}})
    hash_names = ["sample_manifest.tsv", "exclusions.tsv", "feature_filter_summary.json", "czm_provenance.json",
                  "clr_provenance.json", "permanova_results.json", "permanova_results.tsv", "permdisp_results.json",
                  "permdisp_results.tsv", "sensitivity_summary.json", "warnings.json", "session_versions.json"]
    hashes = output_hashes(partial_output, hash_names)
    write_json(partial_output / "output_hashes.json", hashes)
    manifest_payload = {"analysis_id": args.analysis_id, "execution_commit": implementation_commit,
        "input_hashes": {key: result["provenance"][key] for key in ("manifest_sha256", "counts_sha256", "sample_qc_sha256")},
        "code_version": result["analysis_version"], "czm_gate": {"job_id": gate["job_id"]},
        "seeds": {name: result["beta_diversity"][name]["seed"] for name in ("permanova", "permdisp")},
        "parameters": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}, "warnings": [], "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(), "network_acquisition_performed": False,
        "package_installation_performed": False}
    write_json(partial_output / "analysis_manifest.json", analysis_manifest(manifest_payload, hashes))
    write_json(partial_output / "COMPLETE.json", {
        "status": "COMPLETE", "analysis_version": result["analysis_version"],
        "cohort": result["cohort"], "result_sha256": sha256(partial_output / "result.json"),
    })
    partial_output.rename(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
