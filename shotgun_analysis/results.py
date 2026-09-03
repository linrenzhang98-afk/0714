"""Structured result validation, serialization, and compact-table writing."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import InputValidationError
from .contracts import (
    ANALYSIS_VERSION, COHORT_CONTRACTS, EXPECTED_ISOLATED_R_LIBRARY, PRODUCTION_PERMUTATIONS,
    analysis_role, expected_contract_for_project, expected_production_seeds,
)
from .stats import PERMANOVA_ALGORITHM, PERMDISP_ALGORITHM


def reject_nonfinite(value: Any, path: str = "result") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InputValidationError(f"non-finite number at {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            reject_nonfinite(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            reject_nonfinite(child, f"{path}[{index}]")
        return
    raise InputValidationError(f"unsupported result value at {path}: {type(value).__name__}")


def validate_result(result: Mapping[str, Any], schema_path: str | Path) -> None:
    reject_nonfinite(result)
    try:
        import jsonschema
    except ImportError as exc:
        raise InputValidationError("jsonschema is required for result validation") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(dict(result))
    except jsonschema.ValidationError as exc:
        raise InputValidationError(f"result schema validation failed: {exc.message}") from exc
    _validate_cross_field_invariants(result)


def _validate_cross_field_invariants(result: Mapping[str, Any]) -> None:
    """Enforce invariants that JSON Schema cannot express across fields."""
    n = int(result["n"])
    group_counts = {str(key): int(value) for key, value in result["group_counts"].items()}
    if sum(group_counts.values()) != n:
        raise InputValidationError("result group counts do not sum to n")
    samples = list(result["sample_metrics"])
    if len(samples) != n:
        raise InputValidationError("sample_metrics row count does not equal analyzed n")
    sample_ids = [str(row["sample_id"]) for row in samples]
    if len(set(sample_ids)) != n:
        raise InputValidationError("sample_metrics contains duplicate sample IDs")
    observed_groups = dict(Counter(str(row["group"]) for row in samples))
    if observed_groups != group_counts:
        raise InputValidationError("sample_metrics groups do not match group_counts")
    for row in samples:
        total = float(row["total_input_reads"])
        classified = float(row["classified_reads"])
        if classified > total or abs(float(row["classified_fraction"]) - classified / total) > 1e-12:
            raise InputValidationError("classified fraction is inconsistent with its serialized read denominator")
        if float(row["direct_species_assigned_reads"]) > classified:
            raise InputValidationError("direct-species assigned reads exceed all classified reads")
    feature_filter = result["feature_filter"]
    if feature_filter["retained_features"] > feature_filter["input_features"]:
        raise InputValidationError("retained feature count exceeds input feature count")
    if len(feature_filter["retained_feature_ids"]) != feature_filter["retained_features"]:
        raise InputValidationError("retained feature IDs do not match retained feature count")
    for test_name in ("permanova", "permdisp"):
        test = result["beta_diversity"][test_name]
        if test["group_counts"] != group_counts:
            raise InputValidationError(f"{test_name} group counts do not match result group counts")
    diagnostics = result["zero_replacement_diagnostics"]
    if diagnostics["retained_taxa"] != feature_filter["retained_features"]:
        raise InputValidationError("zero diagnostics retained-taxa count is inconsistent")
    if len(diagnostics["zero_fraction_per_sample"]) != n:
        raise InputValidationError("zero diagnostics sample count is inconsistent")
    if len(diagnostics["zero_fraction_per_taxon"]) != feature_filter["retained_features"]:
        raise InputValidationError("zero diagnostics taxon count is inconsistent")
    perturbations = diagnostics["replacement_perturbation_total_variation_per_sample"]
    zero_method = result["zero_handling"]["zero_method"]
    if diagnostics["replacement_applied"] != (zero_method != "none"):
        raise InputValidationError("zero-method metadata conflicts with replacement diagnostics")
    if diagnostics["replacement_applied"] and len(perturbations) != n:
        raise InputValidationError("replacement perturbation count is inconsistent")
    if not diagnostics["replacement_applied"] and perturbations:
        raise InputValidationError("no-replacement result cannot contain perturbation values")
    for row in samples:
        observed = row["replacement_perturbation_total_variation"]
        if diagnostics["replacement_applied"] and observed is None:
            raise InputValidationError("sample replacement perturbation is missing")
        if not diagnostics["replacement_applied"] and observed is not None:
            raise InputValidationError("no-replacement sample cannot have a perturbation value")
    ordination = result["beta_diversity"]["ordination"]
    distance_name = result["beta_diversity"]["distance"]
    if (distance_name == "Aitchison") != (ordination is not None):
        raise InputValidationError("ordination presence is inconsistent with the frozen distance design")
    if ordination is not None:
        coordinate_ids = [str(row["sample_id"]) for row in ordination["sample_coordinates"]]
        if coordinate_ids != sample_ids:
            raise InputValidationError("ordination sample order differs from sample_metrics")
    orientation = result["contrast_orientation"]
    if orientation["type"] == "binary":
        expected = {orientation["positive_group"], orientation["negative_group"]}
        if set(group_counts) != expected:
            raise InputValidationError("binary contrast orientation does not match clinical groups")
        for endpoint in result["secondary_endpoints"].values():
            if endpoint.get("positive_group") != orientation["positive_group"] or endpoint.get("negative_group") != orientation["negative_group"]:
                raise InputValidationError("secondary effect orientation differs from primary orientation")
    for contrast in result["secondary_contrasts"]:
        if contrast["contrast"] != f"{contrast['positive_group']} vs {contrast['negative_group']}":
            raise InputValidationError("secondary contrast label differs from its signed orientation")

    if result["execution_mode"] == "production":
        if result["analysis_version"] != ANALYSIS_VERSION or result["schema_version"] != "2.0.0":
            raise InputValidationError("production analysis/schema version mismatch")
        cohort_key, contract = expected_contract_for_project(str(result["cohort"]))
        if n != contract["n"] or group_counts != contract["groups"]:
            raise InputValidationError("production result violates the frozen cohort contract")
        if result["qc_exclusions_before_analysis"] != 0:
            raise InputValidationError("production result cannot silently exclude frozen cohort members")
        for test_name in ("permanova", "permdisp"):
            if result["beta_diversity"][test_name]["permutations"] != PRODUCTION_PERMUTATIONS:
                raise InputValidationError("production permutation count must be exactly 9999")
        if result["beta_diversity"]["permanova"]["algorithm"] != PERMANOVA_ALGORITHM:
            raise InputValidationError("production PERMANOVA algorithm provenance is not frozen")
        if result["beta_diversity"]["permdisp"]["algorithm"] != PERMDISP_ALGORITHM:
            raise InputValidationError("production PERMDISP algorithm provenance is not frozen")
        normalized_zero = "czm" if zero_method == "CZM" else zero_method
        expected_role = analysis_role(
            float(feature_filter["threshold"]), normalized_zero,
            str(result["beta_diversity"]["distance"]),
        )
        if result["analysis_role"] != expected_role:
            raise InputValidationError("production analysis role is inconsistent with method cell")
        expected_permanova_seed, expected_permdisp_seed = expected_production_seeds(
            cohort_key, float(feature_filter["threshold"]), normalized_zero,
            str(result["beta_diversity"]["distance"]),
        )
        observed_seeds = (
            result["beta_diversity"]["permanova"]["seed"],
            result["beta_diversity"]["permdisp"]["seed"],
        )
        if observed_seeds != (expected_permanova_seed, expected_permdisp_seed):
            raise InputValidationError("production permutation seeds are not the frozen cell-specific seeds")
        if orientation != contract["primary_orientation"]:
            raise InputValidationError(f"production contrast orientation is not frozen for {cohort_key}")
        permutation_design = result["permutation_design"]
        if cohort_key == "anchor":
            block_table = permutation_design["block_cross_tabulation"]
            if permutation_design["restriction"] != "within declared strata" or not isinstance(block_table, Mapping) or set(block_table) != {"Training", "Test"}:
                raise InputValidationError("production anchor permutation blocks are not exact Training/Test")
            if any(set(counts) != set(group_counts) for counts in block_table.values()):
                raise InputValidationError("anchor block table does not contain every frozen diagnosis")
            if any(int(value) < 2 for counts in block_table.values() for value in counts.values()):
                raise InputValidationError("anchor block table has inadequate diagnosis representation")
            block_totals = {
                group: sum(int(block_table[block][group]) for block in ("Training", "Test"))
                for group in group_counts
            }
            if block_totals != group_counts:
                raise InputValidationError("anchor block table does not sum to frozen group counts")
        elif permutation_design["restriction"] != "unrestricted" or permutation_design["block_cross_tabulation"] is not None:
            raise InputValidationError("production external permutations must be unrestricted")
        required_provenance = {
            "python", "manifest_sha256", "counts_sha256", "sample_qc_sha256",
            "czm_adapter_sha256", "implementation_commit", "method_runtime",
        }
        missing = required_provenance - set(result["provenance"])
        if missing:
            raise InputValidationError(f"production method provenance is incomplete: {sorted(missing)}")
        sha256_pattern = re.compile(r"[0-9a-f]{64}")
        for field in ("manifest_sha256", "counts_sha256", "sample_qc_sha256", "czm_adapter_sha256"):
            if not sha256_pattern.fullmatch(str(result["provenance"][field])):
                raise InputValidationError(f"production provenance field {field} is not a SHA256")
        if not re.fullmatch(r"[0-9a-f]{40}", str(result["provenance"]["implementation_commit"])):
            raise InputValidationError("production implementation commit is not a full Git SHA")
        if not str(result["provenance"]["python"]).strip():
            raise InputValidationError("production Python version provenance is blank")
        if normalized_zero == "czm":
            required_runtime = {
                "R_version", "effective_libPaths", "isolated_library",
                "zCompositions_version", "zCompositions_path", "NADA_version", "NADA_path",
                "truncnorm_version", "truncnorm_path",
            }
            runtime = result["provenance"]["method_runtime"]
            if required_runtime - set(runtime):
                raise InputValidationError("production CZM runtime provenance is incomplete")
            if (runtime["R_version"] != "4.5.3" or runtime["zCompositions_version"] != "1.6.2"
                    or runtime["NADA_version"] != "1.6-1.2" or runtime["truncnorm_version"] != "1.0-9"):
                raise InputValidationError("production R/zCompositions version mismatch")
            isolated = str(runtime["isolated_library"]).rstrip("/")
            expected_isolated = str(EXPECTED_ISOLATED_R_LIBRARY.resolve(strict=False))
            if isolated != expected_isolated:
                raise InputValidationError("production CZM resolved an unexpected isolated library")
            effective_paths = str(runtime["effective_libPaths"]).split(";")
            if not effective_paths or effective_paths[0].rstrip("/") != isolated:
                raise InputValidationError("the frozen isolated library is not first in effective .libPaths()")
            for package in ("zCompositions", "NADA", "truncnorm"):
                package_path = str(runtime[f"{package}_path"])
                if not str(runtime[f"{package}_version"]).strip():
                    raise InputValidationError(f"{package} version provenance is blank")
                if not (package_path == isolated or package_path.startswith(isolated + "/")):
                    raise InputValidationError(f"{package} resolved outside the isolated library")


def write_json(path: str | Path, value: Mapping[str, Any], schema_path: str | Path | None = None) -> None:
    reject_nonfinite(value)
    if schema_path is not None:
        validate_result(value, schema_path)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_compact_tsv(path: str | Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    if not rows:
        raise InputValidationError("compact table has no rows")
    if not fields or len(set(fields)) != len(fields):
        raise InputValidationError("compact table fields must be non-empty and unique")
    reject_nonfinite(rows)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
