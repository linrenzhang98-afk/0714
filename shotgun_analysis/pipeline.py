"""Cohort-specific orchestration for the frozen formal analysis.

Production mode is deliberately inflexible and is validated against
``contracts.py``. Development mode accepts small synthetic cohorts for tests.
"""

from __future__ import annotations

from collections import Counter
from typing import Callable, Mapping, Sequence

from .contracts import (
    ANALYSIS_VERSION, COHORT_CONTRACTS, validate_production_contract,
    validate_production_strata,
)
from .core import (
    additive_pseudocount,
    aitchison_distance,
    bray_curtis_distance,
    classified_fraction,
    close_composition,
    clr_transform,
    deterministic_pca,
    diversity_metrics,
    prevalence_filter,
    relative_abundance,
    zero_replacement_diagnostics,
)
from .errors import InputValidationError
from .permutation import validate_block_exchangeability
from .stats import (
    adjust_pvalues,
    centroid_distance_summaries,
    kruskal_wallis,
    mann_whitney,
    permanova,
    permdisp,
)


Replacement = Callable[[Sequence[Sequence[float]]], list[list[float]]]


def _zero_metadata(zero_method: str) -> dict[str, object]:
    if zero_method == "czm":
        return {
            "zero_method": "CZM",
            "implementation": "zCompositions::cmultRepl",
            "version": "1.6.2",
            "parameters": {
                "label": 0,
                "method": "CZM",
                "output": "prop",
                "frac": 0.65,
                "threshold": 0.5,
                "adjust": True,
            },
        }
    if zero_method == "additive_pseudocount":
        return {
            "zero_method": "additive_pseudocount",
            "pseudocount": 0.5,
            "applied_to": "all_retained_features",
        }
    if zero_method == "none":
        return {"zero_method": "none", "pseudocount": None, "applied_to": "not_applicable"}
    raise InputValidationError(f"unknown zero method: {zero_method}")


def _development_orientation(groups: Sequence[str], binary_orientation: tuple[str, str] | None) -> dict[str, object]:
    levels = list(dict.fromkeys(groups))
    if len(levels) == 2:
        if binary_orientation is None:
            raise InputValidationError("binary analysis requires explicit positive/negative group orientation")
        positive, negative = binary_orientation
        if set(levels) != {positive, negative}:
            raise InputValidationError("binary orientation does not match observed groups")
        return {
            "type": "binary",
            "positive_group": positive,
            "negative_group": negative,
            "effect_sign": f"positive means {positive} exceeds {negative}",
        }
    return {"type": "omnibus", "levels": sorted(set(groups)), "signed_effect": False}


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
    zero_replacement: Replacement | None,
    permanova_seed: int,
    permdisp_seed: int,
    permutations: int = 9999,
    permdisp_permutations: int | None = None,
    strata: Sequence[str] | None = None,
    provenance: Mapping[str, object] | None = None,
    secondary_contrasts: Sequence[tuple[str, str]] = (),
    binary_orientation: tuple[str, str] | None = None,
    geometry: str = "Aitchison",
    execution_mode: str = "development",
    cohort_key: str | None = None,
) -> dict[str, object]:
    n = len(sample_ids)
    if execution_mode not in {"development", "production"}:
        raise InputValidationError("execution mode must be development or production")
    if len(set(sample_ids)) != n:
        raise InputValidationError("sample IDs must be unique")
    if any(len(values) != n for values in (groups, counts, total_reads, classified_reads)):
        raise InputValidationError("cohort inputs have inconsistent sample counts")
    classified_fractions = [
        classified_fraction(classified, total)
        for classified, total in zip(classified_reads, total_reads)
    ]
    dispersion_permutations = permutations if permdisp_permutations is None else permdisp_permutations
    if execution_mode == "production":
        if cohort_key is None:
            raise InputValidationError("production mode requires a frozen cohort key")
        role = validate_production_contract(
            cohort_key=cohort_key,
            cohort_id=cohort_id,
            sample_ids=sample_ids,
            groups=groups,
            prevalence=prevalence,
            zero_method=zero_method,
            geometry=geometry,
            permanova_permutations=permutations,
            permdisp_permutations=dispersion_permutations,
            permanova_seed=permanova_seed,
            permdisp_seed=permdisp_seed,
        )
        validate_production_strata(cohort_key, strata)
        orientation = dict(COHORT_CONTRACTS[cohort_key]["primary_orientation"])
    else:
        role = "SYNTHETIC_DEVELOPMENT"
        orientation = _development_orientation(groups, binary_orientation)

    block_table: dict[str, dict[str, int]] | None = None
    if strata is not None:
        block_table = validate_block_exchangeability(groups, strata)

    filtered = prevalence_filter(counts, feature_names, prevalence)
    for index, (row, classified) in enumerate(zip(counts, classified_reads)):
        if sum(float(value) for value in row) > float(classified):
            raise InputValidationError(
                f"direct-species assigned reads exceed all classified reads at sample row {index}"
            )
    zero_handling = _zero_metadata(zero_method)
    ordination: dict[str, object] | None = None
    if geometry == "Aitchison":
        if zero_replacement is None or zero_method not in {"czm", "additive_pseudocount"}:
            raise InputValidationError("Aitchison analysis requires the frozen CZM or additive-pseudocount interface")
        replaced = zero_replacement(filtered.matrix)
        diagnostics = zero_replacement_diagnostics(filtered.matrix, replaced, filtered.feature_names)
        closed = close_composition(replaced)
        clr = clr_transform(closed)
        distance = aitchison_distance(closed)
        ordination = deterministic_pca(clr, axes=5)
        require_euclidean = True
    elif geometry == "Bray-Curtis":
        if zero_method != "none" or zero_replacement is not None or prevalence != 0.10:
            raise InputValidationError("Bray-Curtis is frozen at 10% with no zero replacement")
        diagnostics = zero_replacement_diagnostics(filtered.matrix, None, filtered.feature_names)
        distance = bray_curtis_distance(relative_abundance(filtered.matrix))
        require_euclidean = False
    else:
        raise InputValidationError(f"unsupported geometry: {geometry}")

    beta = permanova(distance, groups, permutations=permutations, seed=permanova_seed, strata=strata)
    dispersion = permdisp(
        distance, groups, permutations=dispersion_permutations, seed=permdisp_seed,
        strata=strata, require_euclidean=require_euclidean,
    )
    centroid = centroid_distance_summaries(distance, groups, require_euclidean=require_euclidean)

    alpha = [diversity_metrics(row) for row in counts]
    metrics = {
        "richness": [item.richness for item in alpha],
        "shannon": [item.shannon for item in alpha],
        "gini_simpson": [item.gini_simpson for item in alpha],
        "dominance": [item.dominance for item in alpha],
        "classified_fraction": classified_fractions,
    }
    secondary: dict[str, dict[str, object]] = {}
    for name, values in metrics.items():
        if len(set(groups)) == 2:
            positive = str(orientation["positive_group"])
            negative = str(orientation["negative_group"])
            secondary[name] = {
                "test": "Mann-Whitney",
                **mann_whitney(values, groups, positive_group=positive, negative_group=negative),
            }
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
            test = mann_whitney(
                [values[index] for index in selected_indices], selected_groups,
                positive_group=positive, negative_group=negative,
            )
            contrasts.append({
                "endpoint": endpoint, "contrast": f"{positive} vs {negative}",
                "test": "Mann-Whitney", **test,
            })
    if contrasts:
        adjusted_values = adjust_pvalues([float(row["p_value"]) for row in contrasts], "holm")
        for row, adjusted in zip(contrasts, adjusted_values):
            endpoint = str(row["endpoint"])
            row["p_adjusted_holm"] = adjusted
            row["omnibus_p_adjusted_holm"] = secondary[endpoint]["p_adjusted_holm"]
            row["confirmatory_interpretation_eligible"] = secondary[endpoint]["p_adjusted_holm"] <= 0.05
            row["post_omnibus_rule"] = (
                "computed as fixed family; confirmatory interpretation only when the corresponding "
                "five-endpoint-Holm-adjusted omnibus P is <=0.05"
            )

    if ordination is not None:
        ordination_rows: list[dict[str, object]] = []
        for index, sample_id in enumerate(sample_ids):
            row: dict[str, object] = {"sample_id": sample_id, "group": groups[index]}
            for axis, value in zip(ordination["axis_labels"], ordination["coordinates"][index]):
                row[str(axis)] = value
            ordination_rows.append(row)
        ordination = {key: value for key, value in ordination.items() if key != "coordinates"}
        ordination["sample_coordinates"] = ordination_rows

    sample_table = [
        {
            "sample_id": sample_id, "group": group,
            "richness": alpha[index].richness, "shannon": alpha[index].shannon,
            "gini_simpson": alpha[index].gini_simpson, "dominance": alpha[index].dominance,
            "classified_fraction": metrics["classified_fraction"][index],
            "total_input_reads": float(total_reads[index]),
            "classified_reads": float(classified_reads[index]),
            "direct_species_assigned_reads": sum(float(value) for value in counts[index]),
            "centroid_distance": centroid["sample_distances"][index],
            "zero_fraction_retained": diagnostics["zero_fraction_per_sample"][index],
            "replacement_perturbation_total_variation": (
                diagnostics["replacement_perturbation_total_variation_per_sample"][index]
                if diagnostics["replacement_applied"] else None
            ),
        }
        for index, (sample_id, group) in enumerate(zip(sample_ids, groups))
    ]
    centroid = {key: value for key, value in centroid.items() if key != "sample_distances"}

    return {
        "schema_version": "2.0.0", "analysis_version": ANALYSIS_VERSION,
        "execution_mode": execution_mode,
        "analysis_status": "SYNTHETIC" if execution_mode == "development" else "BIOLOGICAL",
        "analysis_role": role, "cohort": cohort_id, "n": n,
        "qc_exclusions_before_analysis": 0, "group_counts": dict(Counter(groups)),
        "contrast_orientation": orientation,
        "permutation_design": {
            "restriction": "within declared strata" if strata is not None else "unrestricted",
            "block_cross_tabulation": block_table,
            "blocking_adjusts_split_or_batch_effect": False,
        },
        "feature_filter": {
            "threshold": prevalence, "input_features": len(feature_names),
            "retained_features": len(filtered.feature_names),
            "retained_feature_ids": filtered.feature_names,
        },
        "zero_handling": zero_handling,
        "zero_replacement_diagnostics": diagnostics,
        "beta_diversity": {
            "distance": geometry,
            "input_representation": (
                "Euclidean distance in CLR space" if geometry == "Aitchison"
                else "Bray-Curtis on sample-wise proportions of retained direct-species counts"
            ),
            "permanova": beta.to_dict(), "permdisp": dispersion.to_dict(),
            "centroid_distances": centroid, "ordination": ordination,
        },
        "uncertainty_contract": {
            "permanova_effect": "point R2 with full prespecified representation grid; no confidence interval",
            "permdisp_effect": "point eta-squared with group centroid-distance summaries; no confidence interval",
            "secondary_effects": "point effects with raw and multiplicity-adjusted P values; no confidence intervals",
            "confidence_intervals_generated": False,
        },
        "secondary_endpoints": secondary, "secondary_contrasts": contrasts,
        "sample_metrics": sample_table,
        "interpretation_boundary": {
            "classified_fraction_is_bacterial_biomass": False,
            "classified_fraction_resolves_direct_species_depth_dependence": False,
            "richness_is_sequencing_effort_sensitive": True,
            "alpha_diversity_is_secondary": True,
            "direct_species_is_classifier_defined_subcomposition": True,
        },
        "provenance": dict(provenance or {"fixture": "synthetic_unspecified"}),
    }


def pseudocount_backend(value: float = 0.5) -> Replacement:
    if value != 0.5:
        raise InputValidationError("the frozen additive pseudocount is exactly 0.5")
    return lambda matrix: additive_pseudocount(matrix, value)
