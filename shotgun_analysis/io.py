"""Strict tabular loaders and frozen cohort-manifest validation."""

from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .errors import InputValidationError


@dataclass(frozen=True)
class CountTable:
    sample_ids: list[str]
    feature_names: list[str]
    matrix: list[list[float]]


def load_tsv(path: str | Path) -> list[dict[str, str]]:
    source = Path(path)
    if not source.is_file():
        raise InputValidationError(f"missing TSV: {source}")
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or any(not name for name in reader.fieldnames):
            raise InputValidationError(f"missing or malformed header: {source}")
        rows = list(reader)
    if not rows:
        raise InputValidationError(f"TSV has no data rows: {source}")
    return rows


def validate_cohort_manifest(
    rows: Sequence[Mapping[str, str]],
    expected_groups: Mapping[str, int],
    *,
    sample_column: str = "sample_id",
    group_column: str = "group",
    run_column: str = "run_id",
    required_columns: Sequence[str] = (),
) -> None:
    if not rows:
        raise InputValidationError("cohort manifest is empty")
    required = {sample_column, group_column, run_column, *required_columns}
    missing_columns = required - set(rows[0])
    if missing_columns:
        raise InputValidationError(f"cohort manifest missing columns: {sorted(missing_columns)}")
    sample_ids = [str(row[sample_column]).strip() for row in rows]
    run_ids = [str(row[run_column]).strip() for row in rows]
    if any(not value for value in sample_ids + run_ids):
        raise InputValidationError("blank sample or run identifier")
    duplicate_samples = sorted(value for value, count in Counter(sample_ids).items() if count > 1)
    duplicate_runs = sorted(value for value, count in Counter(run_ids).items() if count > 1)
    if duplicate_samples:
        raise InputValidationError(f"duplicate sample IDs: {duplicate_samples}")
    if duplicate_runs:
        raise InputValidationError(f"duplicate run IDs: {duplicate_runs}")
    observed = Counter(str(row[group_column]).strip() for row in rows)
    if dict(observed) != dict(expected_groups):
        raise InputValidationError(f"group counts differ: expected {dict(expected_groups)}, observed {dict(observed)}")
    for index, row in enumerate(rows):
        for column in required_columns:
            if not str(row[column]).strip():
                raise InputValidationError(f"blank required value in row {index + 2}, column {column}")


def load_direct_species_counts(path: str | Path, *, sample_column: str = "sample_id") -> CountTable:
    rows = load_tsv(path)
    columns = list(rows[0])
    if sample_column not in columns:
        raise InputValidationError(f"count table missing {sample_column}")
    features = [name for name in columns if name != sample_column]
    if not features or len(set(features)) != len(features):
        raise InputValidationError("taxon columns must be non-empty and unique")
    sample_ids: list[str] = []
    matrix: list[list[float]] = []
    for row_number, row in enumerate(rows, start=2):
        sample_id = str(row[sample_column]).strip()
        if not sample_id:
            raise InputValidationError(f"blank sample ID at row {row_number}")
        sample_ids.append(sample_id)
        converted: list[float] = []
        for feature in features:
            try:
                value = float(row[feature])
            except (TypeError, ValueError) as exc:
                raise InputValidationError(f"non-numeric count at row {row_number}, feature {feature}") from exc
            if not math.isfinite(value) or value < 0 or not value.is_integer():
                raise InputValidationError(f"direct counts must be finite non-negative integers at row {row_number}, feature {feature}")
            converted.append(value)
        if sum(converted) <= 0:
            raise InputValidationError(f"all-zero sample at row {row_number}")
        matrix.append(converted)
    duplicates = sorted(value for value, count in Counter(sample_ids).items() if count > 1)
    if duplicates:
        raise InputValidationError(f"duplicate samples in count table: {duplicates}")
    return CountTable(sample_ids, features, matrix)


def load_common_layer_direct_species_counts(
    path: str | Path,
    expected_sample_ids: Sequence[str],
) -> CountTable:
    """Load the verified common-layer taxon-major direct-count artifact."""
    rows = load_tsv(path)
    metadata = {"taxid", "rank", "scientific_name", "prevalence", "present_5pct", "present_10pct", "present_20pct"}
    columns = list(rows[0])
    sample_columns = [column for column in columns if column not in metadata]
    if sample_columns != list(expected_sample_ids):
        raise InputValidationError("taxon-major count columns do not exactly match the expected ordered samples")
    feature_names: list[str] = []
    taxon_rows: list[list[float]] = []
    for row_number, row in enumerate(rows, start=2):
        if row.get("rank") != "S":
            raise InputValidationError(f"non-species row in species count table at row {row_number}")
        feature = str(row.get("taxid", "")).strip()
        if not feature:
            raise InputValidationError(f"blank taxid at row {row_number}")
        feature_names.append(feature)
        values: list[float] = []
        for sample_id in sample_columns:
            try:
                value = float(row[sample_id])
            except (TypeError, ValueError) as exc:
                raise InputValidationError(f"non-numeric count at row {row_number}, sample {sample_id}") from exc
            if not math.isfinite(value) or value < 0 or not value.is_integer():
                raise InputValidationError(f"invalid direct count at row {row_number}, sample {sample_id}")
            values.append(value)
        taxon_rows.append(values)
    if len(set(feature_names)) != len(feature_names):
        raise InputValidationError("duplicate taxid rows in common-layer count table")
    matrix = [[taxon_rows[j][i] for j in range(len(taxon_rows))] for i in range(len(sample_columns))]
    for index, row in enumerate(matrix):
        if sum(row) <= 0:
            raise InputValidationError(f"all-zero sample in common-layer counts: {sample_columns[index]}")
    return CountTable(sample_columns, feature_names, matrix)


def validate_sample_alignment(manifest_ids: Sequence[str], count_ids: Sequence[str]) -> None:
    manifest = set(manifest_ids)
    counts = set(count_ids)
    if len(manifest) != len(manifest_ids) or len(counts) != len(count_ids):
        raise InputValidationError("sample alignment inputs contain duplicates")
    missing = sorted(manifest - counts)
    unexpected = sorted(counts - manifest)
    if missing or unexpected:
        raise InputValidationError(f"sample mismatch: missing={missing}, unexpected={unexpected}")
