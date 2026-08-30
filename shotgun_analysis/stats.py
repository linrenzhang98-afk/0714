"""Dependency-free statistical tests used by the frozen analysis contract."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Sequence

from .core import validate_distance_matrix
from .errors import DegenerateDesignError, InputValidationError
from .permutation import restricted_permutations


@dataclass(frozen=True)
class PermutationTest:
    statistic: float
    effect_size: float
    p_value: float
    permutations: int
    seed: int
    df_between: int
    df_within: int
    group_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _validate_groups(groups: Sequence[str], n: int) -> list[str]:
    if len(groups) != n or any(not str(group) for group in groups):
        raise InputValidationError("groups must be non-blank and match sample count")
    labels = [str(group) for group in groups]
    counts = Counter(labels)
    if len(counts) < 2:
        raise DegenerateDesignError("at least two groups are required")
    if any(count < 2 for count in counts.values()):
        raise DegenerateDesignError("each group must contain at least two samples")
    if len(labels) <= len(counts):
        raise DegenerateDesignError("no within-group residual degrees of freedom")
    return labels


def _permanova_components(distance: list[list[float]], groups: Sequence[str]) -> tuple[float, float, float]:
    n = len(distance)
    counts = Counter(groups)
    total_ss = sum(distance[i][j] ** 2 for i in range(n) for j in range(i)) / n
    within_ss = 0.0
    for group, count in counts.items():
        indices = [i for i, label in enumerate(groups) if label == group]
        within_ss += sum(distance[i][j] ** 2 for offset, i in enumerate(indices) for j in indices[:offset]) / count
    between_ss = max(0.0, total_ss - within_ss)
    df_between = len(counts) - 1
    df_within = n - len(counts)
    if total_ss <= 0 or within_ss <= 0:
        raise DegenerateDesignError("distance variation is degenerate")
    pseudo_f = (between_ss / df_between) / (within_ss / df_within)
    return pseudo_f, between_ss / total_ss, total_ss


def permanova(
    distance: Sequence[Sequence[float]],
    groups: Sequence[str],
    *,
    permutations: int = 9999,
    seed: int,
    strata: Sequence[str] | None = None,
) -> PermutationTest:
    values = validate_distance_matrix(distance)
    labels = _validate_groups(groups, len(values))
    observed, r_squared, _ = _permanova_components(values, labels)
    index_maps = restricted_permutations(len(values), permutations, seed, strata)
    exceedances = 0
    for index_map in index_maps:
        statistic, _, _ = _permanova_components(values, [labels[index] for index in index_map])
        exceedances += statistic >= observed - 1e-12
    counts = Counter(labels)
    return PermutationTest(
        statistic=observed,
        effect_size=r_squared,
        p_value=(exceedances + 1) / (permutations + 1),
        permutations=permutations,
        seed=seed,
        df_between=len(counts) - 1,
        df_within=len(values) - len(counts),
        group_counts=dict(counts),
    )


def distances_to_group_centroid(distance: Sequence[Sequence[float]], groups: Sequence[str]) -> list[float]:
    values = validate_distance_matrix(distance)
    labels = _validate_groups(groups, len(values))
    result = [0.0] * len(values)
    for group in dict.fromkeys(labels):
        indices = [i for i, label in enumerate(labels) if label == group]
        count = len(indices)
        pair_sum = sum(values[j][k] ** 2 for j in indices for k in indices)
        centroid_term = pair_sum / (2.0 * count * count)
        for i in indices:
            squared = sum(values[i][j] ** 2 for j in indices) / count - centroid_term
            if squared < -1e-8:
                raise InputValidationError("distance is non-Euclidean; negative squared centroid distance")
            result[i] = math.sqrt(max(0.0, squared))
    return result


def _one_way_anova(values: Sequence[float], groups: Sequence[str]) -> tuple[float, float]:
    labels = _validate_groups(groups, len(values))
    overall = sum(values) / len(values)
    levels = list(dict.fromkeys(labels))
    between = 0.0
    within = 0.0
    for group in levels:
        selected = [value for value, label in zip(values, labels) if label == group]
        mean = sum(selected) / len(selected)
        between += len(selected) * (mean - overall) ** 2
        within += sum((value - mean) ** 2 for value in selected)
    total = between + within
    if within <= 0 or total <= 0:
        raise DegenerateDesignError("dispersion values are degenerate")
    statistic = (between / (len(levels) - 1)) / (within / (len(values) - len(levels)))
    return statistic, between / total


def permdisp(
    distance: Sequence[Sequence[float]],
    groups: Sequence[str],
    *,
    permutations: int = 9999,
    seed: int,
    strata: Sequence[str] | None = None,
) -> PermutationTest:
    values = validate_distance_matrix(distance)
    labels = _validate_groups(groups, len(values))
    observed_distances = distances_to_group_centroid(values, labels)
    observed, r_squared = _one_way_anova(observed_distances, labels)
    exceedances = 0
    for index_map in restricted_permutations(len(values), permutations, seed, strata):
        permuted_labels = [labels[index] for index in index_map]
        candidate_distances = distances_to_group_centroid(values, permuted_labels)
        statistic, _ = _one_way_anova(candidate_distances, permuted_labels)
        exceedances += statistic >= observed - 1e-12
    counts = Counter(labels)
    return PermutationTest(
        statistic=observed,
        effect_size=r_squared,
        p_value=(exceedances + 1) / (permutations + 1),
        permutations=permutations,
        seed=seed,
        df_between=len(counts) - 1,
        df_within=len(values) - len(counts),
        group_counts=dict(counts),
    )


def _average_ranks(values: Sequence[float]) -> list[float]:
    if any(not math.isfinite(float(value)) for value in values):
        raise InputValidationError("rank test values contain NaN/Inf")
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        average = (start + 1 + end) / 2.0
        for position in range(start, end):
            ranks[ordered[position]] = average
        start = end
    return ranks


def _regularized_gamma_q(a: float, x: float) -> float:
    """Upper regularized gamma, sufficient for chi-square tail probabilities."""
    if a <= 0 or x < 0:
        raise InputValidationError("invalid incomplete-gamma arguments")
    if x == 0:
        return 1.0
    epsilon = 3e-14
    if x < a + 1:
        term = 1.0 / a
        total = term
        ap = a
        for _ in range(1000):
            ap += 1
            term *= x / ap
            total += term
            if abs(term) < abs(total) * epsilon:
                break
        p = total * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - p))
    b = x + 1 - a
    c = 1 / 1e-300
    d = 1 / b
    h = d
    for i in range(1, 1001):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < epsilon:
            break
    q = math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    return max(0.0, min(1.0, q))


def kruskal_wallis(values: Sequence[float], groups: Sequence[str]) -> dict[str, float | int]:
    labels = _validate_groups(groups, len(values))
    n = len(values)
    levels = list(dict.fromkeys(labels))
    ranks = _average_ranks(values)
    rank_sums = {group: sum(rank for rank, label in zip(ranks, labels) if label == group) for group in levels}
    counts = Counter(labels)
    raw_h = 12 / (n * (n + 1)) * sum(rank_sums[g] ** 2 / counts[g] for g in levels) - 3 * (n + 1)
    tie_counts = Counter(values)
    correction = 1 - sum(count ** 3 - count for count in tie_counts.values()) / (n ** 3 - n)
    if correction <= 0:
        raise DegenerateDesignError("all rank-test values are tied")
    h = raw_h / correction
    epsilon_squared = max(0.0, (h - len(levels) + 1) / (n - len(levels)))
    degrees = len(levels) - 1
    return {
        "statistic": h,
        "df": degrees,
        "p_value": _regularized_gamma_q(degrees / 2, h / 2),
        "epsilon_squared": epsilon_squared,
    }


def mann_whitney(values: Sequence[float], groups: Sequence[str]) -> dict[str, float | int]:
    labels = _validate_groups(groups, len(values))
    levels = list(dict.fromkeys(labels))
    if len(levels) != 2:
        raise DegenerateDesignError("Mann-Whitney requires exactly two groups")
    ranks = _average_ranks(values)
    n1 = labels.count(levels[0])
    n2 = labels.count(levels[1])
    u1 = sum(rank for rank, label in zip(ranks, labels) if label == levels[0]) - n1 * (n1 + 1) / 2
    rank_biserial = 2 * u1 / (n1 * n2) - 1
    tie_counts = Counter(values)
    tie_term = sum(count ** 3 - count for count in tie_counts.values())
    n = n1 + n2
    variance = n1 * n2 / 12 * ((n + 1) - tie_term / (n * (n - 1)))
    if variance <= 0:
        raise DegenerateDesignError("all Mann-Whitney values are tied")
    continuity = 0.5 if u1 > n1 * n2 / 2 else (-0.5 if u1 < n1 * n2 / 2 else 0.0)
    z = (u1 - n1 * n2 / 2 - continuity) / math.sqrt(variance)
    p_value = math.erfc(abs(z) / math.sqrt(2))
    return {"u": u1, "n1": n1, "n2": n2, "z": z, "p_value": p_value, "rank_biserial": rank_biserial}


def adjust_pvalues(p_values: Sequence[float], method: str) -> list[float]:
    values = [float(value) for value in p_values]
    if not values or any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise InputValidationError("p-values must be finite values in [0, 1]")
    n = len(values)
    order = sorted(range(n), key=lambda index: values[index])
    adjusted = [0.0] * n
    normalized = method.lower().replace("-", "_")
    if normalized in {"bh", "benjamini_hochberg", "fdr"}:
        running = 1.0
        for reverse_rank in range(n - 1, -1, -1):
            index = order[reverse_rank]
            running = min(running, values[index] * n / (reverse_rank + 1))
            adjusted[index] = min(1.0, running)
    elif normalized == "holm":
        running = 0.0
        for rank, index in enumerate(order):
            running = max(running, (n - rank) * values[index])
            adjusted[index] = min(1.0, running)
    else:
        raise InputValidationError(f"unsupported multiplicity method: {method}")
    return adjusted
