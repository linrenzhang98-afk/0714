"""Dependency-free compositional and ecological primitives.

All matrices are sample-major sequences.  These functions intentionally do
not implement CZM; see ``czm.py`` for the exact zCompositions adapter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from .errors import InputValidationError


Number = int | float


def _validated_matrix(matrix: Sequence[Sequence[Number]], *, positive: bool = False) -> list[list[float]]:
    if not matrix:
        raise InputValidationError("matrix has no samples")
    width = len(matrix[0])
    if width == 0:
        raise InputValidationError("matrix has no taxa")
    out: list[list[float]] = []
    for row_index, row in enumerate(matrix):
        if len(row) != width:
            raise InputValidationError(f"ragged matrix at row {row_index}")
        converted: list[float] = []
        for column_index, value in enumerate(row):
            if isinstance(value, bool):
                raise InputValidationError(f"boolean value at row {row_index}, column {column_index}")
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise InputValidationError(f"non-numeric value at row {row_index}, column {column_index}") from exc
            if not math.isfinite(number):
                raise InputValidationError(f"NaN/Inf at row {row_index}, column {column_index}")
            if number < 0 or (positive and number <= 0):
                qualifier = "positive" if positive else "non-negative"
                raise InputValidationError(f"value must be {qualifier} at row {row_index}, column {column_index}")
            converted.append(number)
        if sum(converted) <= 0:
            raise InputValidationError(f"all-zero sample at row {row_index}")
        out.append(converted)
    return out


@dataclass(frozen=True)
class FilteredMatrix:
    matrix: list[list[float]]
    feature_names: list[str]
    detected_counts: list[int]
    prevalence: list[float]
    retained_indices: list[int]


def prevalence_filter(
    matrix: Sequence[Sequence[Number]],
    feature_names: Sequence[str],
    threshold: float,
) -> FilteredMatrix:
    """Retain taxa with direct count >0 in at least ``threshold`` of samples.

    The boundary is inclusive, so exactly 10/100 detections passes a 10%
    threshold.  Taxa with no detections are removed at every threshold.
    """
    values = _validated_matrix(matrix)
    if not 0 < threshold <= 1:
        raise InputValidationError("prevalence threshold must be in (0, 1]")
    if len(feature_names) != len(values[0]) or len(set(feature_names)) != len(feature_names):
        raise InputValidationError("feature names must be unique and match matrix width")
    n = len(values)
    detected = [sum(row[j] > 0 for row in values) for j in range(len(feature_names))]
    keep = [j for j, count in enumerate(detected) if count > 0 and count / n >= threshold]
    if not keep:
        raise InputValidationError("prevalence filter retained no taxa")
    filtered = [[row[j] for j in keep] for row in values]
    for i, row in enumerate(filtered):
        if sum(row) <= 0:
            raise InputValidationError(f"all-zero sample after prevalence filtering at row {i}")
    return FilteredMatrix(
        matrix=filtered,
        feature_names=[str(feature_names[j]) for j in keep],
        detected_counts=[detected[j] for j in keep],
        prevalence=[detected[j] / n for j in keep],
        retained_indices=keep,
    )


def pseudocount_replace(matrix: Sequence[Sequence[Number]], value: float = 0.5) -> list[list[float]]:
    values = _validated_matrix(matrix)
    if not math.isfinite(value) or value <= 0:
        raise InputValidationError("pseudocount must be finite and positive")
    return [[value if cell == 0 else cell for cell in row] for row in values]


def close_composition(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    values = _validated_matrix(matrix, positive=True)
    return [[cell / sum(row) for cell in row] for row in values]


def clr_transform(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    values = _validated_matrix(matrix, positive=True)
    transformed: list[list[float]] = []
    for row in values:
        logs = [math.log(cell) for cell in row]
        mean_log = sum(logs) / len(logs)
        transformed.append([value - mean_log for value in logs])
    return transformed


def euclidean_distance(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    if not matrix or not matrix[0]:
        raise InputValidationError("coordinate matrix is empty")
    width = len(matrix[0])
    values: list[list[float]] = []
    for row_index, row in enumerate(matrix):
        if len(row) != width:
            raise InputValidationError(f"ragged coordinate matrix at row {row_index}")
        converted = [float(value) for value in row]
        if any(not math.isfinite(value) for value in converted):
            raise InputValidationError(f"non-finite coordinate at row {row_index}")
        values.append(converted)
    n = len(values)
    distance = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            value = math.sqrt(sum((a - b) ** 2 for a, b in zip(values[i], values[j])))
            distance[i][j] = distance[j][i] = value
    return distance


def aitchison_distance(closed_positive_matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    return euclidean_distance(clr_transform(closed_positive_matrix))


def bray_curtis_distance(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    values = _validated_matrix(matrix)
    n = len(values)
    distance = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            denominator = sum(a + b for a, b in zip(values[i], values[j]))
            if denominator <= 0:
                raise InputValidationError("Bray-Curtis denominator is zero")
            value = sum(abs(a - b) for a, b in zip(values[i], values[j])) / denominator
            distance[i][j] = distance[j][i] = value
    return distance


@dataclass(frozen=True)
class Diversity:
    richness: int
    shannon: float
    gini_simpson: float
    dominance: float


def diversity_metrics(counts: Sequence[Number]) -> Diversity:
    matrix = _validated_matrix([counts])
    row = matrix[0]
    total = sum(row)
    proportions = [value / total for value in row if value > 0]
    return Diversity(
        richness=len(proportions),
        shannon=-sum(p * math.log(p) for p in proportions),
        gini_simpson=1.0 - sum(p * p for p in proportions),
        dominance=max(proportions),
    )


def classified_fraction(classified_reads: Number, total_reads: Number) -> float:
    try:
        numerator = float(classified_reads)
        denominator = float(total_reads)
    except (TypeError, ValueError) as exc:
        raise InputValidationError("classified and total reads must be numeric") from exc
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        raise InputValidationError("classified and total reads must be finite")
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise InputValidationError("require 0 <= classified_reads <= total_reads and total_reads > 0")
    return numerator / denominator


def validate_distance_matrix(distance: Sequence[Sequence[Number]], tolerance: float = 1e-10) -> list[list[float]]:
    if not distance:
        raise InputValidationError("distance matrix is empty")
    n = len(distance)
    values: list[list[float]] = []
    for i, row in enumerate(distance):
        if len(row) != n:
            raise InputValidationError("distance matrix must be square")
        converted = [float(x) for x in row]
        if any(not math.isfinite(x) or x < 0 for x in converted):
            raise InputValidationError("distance matrix contains invalid values")
        values.append(converted)
        if abs(converted[i]) > tolerance:
            raise InputValidationError("distance diagonal must be zero")
    for i in range(n):
        for j in range(i):
            if abs(values[i][j] - values[j][i]) > tolerance:
                raise InputValidationError("distance matrix must be symmetric")
    return values
