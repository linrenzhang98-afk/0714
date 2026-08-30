"""Cohort-specific formal-analysis orchestration.

The orchestration accepts an injected zero-replacement callable for synthetic
tests. Production callers must pass ``exact_czm``; the output records the named
method so a sensitivity backend cannot masquerade as primary CZM.
"""

from __future__ import annotations

from collections import Counter
from typing import Callable, Mapping, Sequence

from .core import (
    aitchison_distance,
    classified_fraction,
    close_composition,
    diversity_metrics,
    prevalence_filter,
    pseudocount_replace,
)
from .errors import InputValidationError
from .stats import adjust_pvalues, kruskal_wallis, mann_whitney, permanova, permdisp


Replacement = Callable[[Sequence[Sequence[float]]], list[list[float]]]


def analyze_cohort(
    *,
    cohort_id: str,
    sample_ids: Sequence[str],
    groups: Sequence[str],
    counts: Sequence[Sequence[float]],
    feature_names: Sequence[str],
    total_reads: Sequence[float],
    classified_reads: Sequence[float],
    prevalence: float,
    zero_method: str,
    zero_replacement: Replacement,
    permanova_seed: int,
    permdisp_seed: int,
    permutations: int = 9999,
    strata: Sequence[str] | None = None,
    provenance: Mapping[str, object] | None = None,
    secondary_contrasts: Sequence[tuple[str, str]] = (),
) -> dict[str, object]:
    n = len(sample_ids)
    if len(set(sample_ids)) != n:
        raise InputValidationError("sample IDs must be unique")
    if any(len(values) != n for values in (groups, counts, total_reads, classified_reads)):
        raise InputValidationError("cohort inputs have inconsistent sample counts")
    filtered = prevalence_filter(counts, feature_names, prevalence)
    replaced = zero_replacement(filtered.matrix)
    closed = close_composition(replaced)
    distance = aitchison_distance(closed)
    beta = permanova(distance, groups, permutations=permutations, seed=permanova_seed, strata=strata)
    dispersion = permdisp(distance, groups, permutations=permutations, seed=permdisp_seed, strata=strata)
    alpha = [diversity_metrics(row) for row in counts]
    metrics = {
        "richness": [item.richness for item in alpha],
        "shannon": [item.shannon for item in alpha],
        "gini_simpson": [item.gini_simpson for item in alpha],
        "dominance": [item.dominance for item in alpha],
        "classified_fraction": [classified_fraction(c, t) for c, t in zip(classified_reads, total_reads)],
    }
    secondary: dict[str, object] = {}
    for name, values in metrics.items():
        if len(set(groups)) == 2:
            secondary[name] = {"test": "Mann-Whitney", **mann_whitney(values, groups)}
        else:
            secondary[name] = {"test": "Kruskal-Wallis", **kruskal_wallis(values, groups)}
    secondary_p = [float(secondary[name]["p_value"]) for name in metrics]
    for name, adjusted in zip(metrics, adjust_pvalues(secondary_p, "holm")):
        secondary[name]["p_adjusted_holm"] = adjusted
    contrasts: list[dict[str, object]] = []
    for positive, negative in secondary_contrasts:
        if positive not in set(groups) or negative not in set(groups) or positive == negative:
            raise InputValidationError(f"invalid secondary contrast: {positive} vs {negative}")
        selected_indices = [index for index, group in enumerate(groups) if group in {positive, negative}]
        selected_groups = [groups[index] for index in selected_indices]
        for endpoint, values in metrics.items():
            test = mann_whitney([values[index] for index in selected_indices], selected_groups)
            contrasts.append({"endpoint": endpoint, "contrast": f"{positive} vs {negative}", "test": "Mann-Whitney", **test})
    if contrasts:
        adjusted_values = adjust_pvalues([float(row["p_value"]) for row in contrasts], "holm")
        for row, adjusted in zip(contrasts, adjusted_values):
            row["p_adjusted_holm"] = adjusted
    sample_table = [
        {
            "sample_id": sample_id,
            "group": group,
            "richness": alpha[index].richness,
            "shannon": alpha[index].shannon,
            "gini_simpson": alpha[index].gini_simpson,
            "dominance": alpha[index].dominance,
            "classified_fraction": metrics["classified_fraction"][index],
        }
        for index, (sample_id, group) in enumerate(zip(sample_ids, groups))
    ]
    return {
        "schema_version": "1.0.0",
        "analysis_status": "SYNTHETIC" if all(str(x).startswith("SYN_") for x in sample_ids) else "BIOLOGICAL",
        "cohort": cohort_id,
        "n": n,
        "group_counts": dict(Counter(groups)),
        "feature_filter": {
            "threshold": prevalence,
            "input_features": len(feature_names),
            "retained_features": len(filtered.feature_names),
            "retained_feature_ids": filtered.feature_names,
        },
        "zero_handling": {"method": zero_method},
        "beta_diversity": {
            "distance": "Aitchison",
            "permanova": beta.to_dict(),
            "permdisp": dispersion.to_dict(),
        },
        "secondary_endpoints": secondary,
        "secondary_contrasts": contrasts,
        "sample_metrics": sample_table,
        "interpretation_boundary": {
            "classified_fraction_is_bacterial_biomass": False,
            "direct_species_is_classifier_defined_subcomposition": True,
        },
        "provenance": dict(provenance or {"fixture": "synthetic_unspecified"}),
    }


def pseudocount_backend(value: float = 0.5) -> Replacement:
    return lambda matrix: pseudocount_replace(matrix, value)
