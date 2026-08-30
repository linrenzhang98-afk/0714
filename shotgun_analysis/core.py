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


def additive_pseudocount(matrix: Sequence[Sequence[Number]], value: float = 0.5) -> list[list[float]]:
    """Add ``value`` to every retained component, including non-zero counts."""
    values = _validated_matrix(matrix)
    if not math.isfinite(value) or value <= 0:
        raise InputValidationError("pseudocount must be finite and positive")
    return [[cell + value for cell in row] for row in values]


def close_composition(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    values = _validated_matrix(matrix, positive=True)
    return [[cell / sum(row) for cell in row] for row in values]


def relative_abundance(matrix: Sequence[Sequence[Number]]) -> list[list[float]]:
    """Close non-negative counts while retaining observed zeros."""
    values = _validated_matrix(matrix)
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


def zero_replacement_diagnostics(
    original: Sequence[Sequence[Number]],
    replaced: Sequence[Sequence[Number]] | None,
    feature_names: Sequence[str],
) -> dict[str, object]:
    """Describe zero burden and representation perturbation without exclusions.

    Perturbation is total-variation distance between closure of the original
    retained counts (zeros allowed) and closure of the replacement output.
    It is a descriptive QC quantity, not an outcome or exclusion rule.
    """
    before = _validated_matrix(original)
    if len(feature_names) != len(before[0]):
        raise InputValidationError("replacement diagnostics feature names do not match matrix width")
    n_samples = len(before)
    n_taxa = len(before[0])
    sample_zero_fraction = [sum(cell == 0 for cell in row) / n_taxa for row in before]
    taxon_zero_fraction = [sum(row[j] == 0 for row in before) / n_samples for j in range(n_taxa)]
    total_variation: list[float] = []
    if replaced is not None:
        after = _validated_matrix(replaced, positive=True)
        if len(before) != len(after) or any(len(a) != len(b) for a, b in zip(before, after)):
            raise InputValidationError("replacement diagnostics require matching matrix dimensions")
        before_closed = relative_abundance(before)
        after_closed = close_composition(after)
        total_variation = [
            0.5 * sum(abs(left - right) for left, right in zip(raw, replacement))
            for raw, replacement in zip(before_closed, after_closed)
        ]
    return {
        "retained_taxa": n_taxa,
        "zero_cells": sum(cell == 0 for row in before for cell in row),
        "zero_fraction_overall": sum(cell == 0 for row in before for cell in row) / (n_samples * n_taxa),
        "zero_fraction_per_sample": sample_zero_fraction,
        "zero_fraction_per_taxon": [
            {"feature_id": str(feature), "zero_fraction": fraction}
            for feature, fraction in zip(feature_names, taxon_zero_fraction)
        ],
        "replacement_perturbation_total_variation_per_sample": total_variation,
        "replacement_applied": replaced is not None,
        "used_for_exclusion": False,
    }


def deterministic_pca(
    coordinates: Sequence[Sequence[Number]],
    *,
    axes: int = 5,
    tolerance: float = 1e-11,
    max_iterations: int = 2000,
) -> dict[str, object]:
    """Deterministic leading PCA axes for Euclidean CLR coordinates.

    PCA of sample-centred CLR coordinates is equivalent to principal
    coordinates analysis of their Euclidean (Aitchison) distances. A fixed
    power-iteration start and sign convention make the figure coordinates
    reproducible without a numerical-library dependency.
    """
    if not coordinates or not coordinates[0] or axes < 1:
        raise InputValidationError("ordination requires non-empty coordinates and at least one axis")
    width = len(coordinates[0])
    values = [[float(cell) for cell in row] for row in coordinates]
    if any(len(row) != width for row in values) or any(not math.isfinite(cell) for row in values for cell in row):
        raise InputValidationError("ordination coordinates must be finite and rectangular")
    n = len(values)
    means = [sum(row[j] for row in values) / n for j in range(width)]
    centred = [[row[j] - means[j] for j in range(width)] for row in values]
    total_inertia = sum(cell * cell for row in centred for cell in row)
    if total_inertia <= 0:
        raise InputValidationError("ordination is degenerate")

    def gram_multiply(vector: Sequence[float]) -> list[float]:
        feature_projection = [sum(centred[i][j] * vector[i] for i in range(n)) for j in range(width)]
        return [sum(centred[i][j] * feature_projection[j] for j in range(width)) for i in range(n)]

    eigenvectors: list[list[float]] = []
    eigenvalues: list[float] = []
    for axis in range(min(axes, n - 1, width)):
        vector = [math.sin((i + 1) * (axis + 1) * 0.731) + math.cos((i + 1) * 0.317) for i in range(n)]
        for prior in eigenvectors:
            projection = sum(a * b for a, b in zip(vector, prior))
            vector = [a - projection * b for a, b in zip(vector, prior)]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= tolerance:
            continue
        vector = [value / norm for value in vector]
        for _ in range(max_iterations):
            updated = gram_multiply(vector)
            for prior in eigenvectors:
                projection = sum(a * b for a, b in zip(updated, prior))
                updated = [a - projection * b for a, b in zip(updated, prior)]
            updated_norm = math.sqrt(sum(value * value for value in updated))
            if updated_norm <= tolerance:
                break
            updated = [value / updated_norm for value in updated]
            if sum(a * b for a, b in zip(updated, vector)) < 0:
                updated = [-value for value in updated]
            delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(updated, vector)))
            vector = updated
            if delta <= tolerance:
                break
        eigenvalue = sum(a * b for a, b in zip(vector, gram_multiply(vector)))
        if eigenvalue <= tolerance:
            continue
        max_index = max(range(n), key=lambda index: abs(vector[index]))
        if vector[max_index] < 0:
            vector = [-value for value in vector]
        eigenvectors.append(vector)
        eigenvalues.append(eigenvalue)
    if not eigenvalues:
        raise InputValidationError("ordination retained no positive axes")
    scores = [
        [math.sqrt(eigenvalue) * eigenvectors[axis][i] for axis, eigenvalue in enumerate(eigenvalues)]
        for i in range(n)
    ]
    return {
        "method": "PCA of sample-centred CLR coordinates (Aitchison PCoA equivalent)",
        "axis_labels": [f"PCoA{index + 1}" for index in range(len(eigenvalues))],
        "eigenvalues": eigenvalues,
        "explained_fraction": [value / total_inertia for value in eigenvalues],
        "coordinates": scores,
        "deterministic_sign_rule": "largest-absolute sample score is positive",
    }
