"""Immutable production contracts for the formal two-cohort analysis."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

from .errors import InputValidationError


ANALYSIS_VERSION = "2.0.0"
PRODUCTION_PERMUTATIONS = 9999
PRIMARY_PREVALENCE = 0.10
SENSITIVITY_PREVALENCES = (0.05, 0.20)
EXPECTED_ISOLATED_R_LIBRARY = Path(
    "/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3"
)

COHORT_CONTRACTS = {
    "anchor": {
        "project": "PRJNA1056765",
        "n": 400,
        "groups": {
            "Bacterial infection": 114,
            "Fungal infection": 78,
            "Lung cancer": 122,
            "Pulmonary tuberculosis": 86,
        },
        "primary_orientation": {
            "type": "omnibus",
            "levels": [
                "Bacterial infection",
                "Fungal infection",
                "Lung cancer",
                "Pulmonary tuberculosis",
            ],
            "signed_effect": False,
        },
        "seeds": (105676510, 105676511),
    },
    "external": {
        "project": "PRJCA046985",
        "n": 130,
        "groups": {"Drug_Resistance": 49, "Drug_Sensitive": 81},
        "primary_orientation": {
            "type": "binary",
            "positive_group": "Drug_Resistance",
            "negative_group": "Drug_Sensitive",
            "effect_sign": "positive means Drug_Resistance exceeds Drug_Sensitive",
        },
        "seeds": (46985010, 46985011),
    },
}


def analysis_role(prevalence: float, zero_method: str, geometry: str) -> str:
    """Classify an allowed production cell or fail closed."""
    if geometry == "Aitchison" and zero_method == "czm":
        if prevalence == PRIMARY_PREVALENCE:
            return "PRIMARY"
        if prevalence in SENSITIVITY_PREVALENCES:
            return "FILTER_SENSITIVITY"
    if geometry == "Aitchison" and zero_method == "additive_pseudocount":
        if prevalence in (0.05, 0.10, 0.20):
            return "ZERO_METHOD_SENSITIVITY"
    if geometry == "Bray-Curtis" and zero_method == "none" and prevalence == PRIMARY_PREVALENCE:
        return "BRAY_CURTIS_SENSITIVITY"
    raise InputValidationError(
        "cell is outside the frozen production grid: "
        f"prevalence={prevalence}, zero_method={zero_method}, geometry={geometry}"
    )


def expected_production_seeds(
    cohort_key: str, prevalence: float, zero_method: str, geometry: str
) -> tuple[int, int]:
    """Return the immutable PERMANOVA/PERMDISP seeds for an allowed cell."""
    analysis_role(prevalence, zero_method, geometry)
    if cohort_key not in COHORT_CONTRACTS:
        raise InputValidationError(f"unknown production cohort: {cohort_key}")
    if geometry == "Bray-Curtis":
        offset = 200000
    elif zero_method == "additive_pseudocount":
        offset = 100000 + {0.05: 500, 0.10: 1000, 0.20: 2000}[prevalence]
    else:
        offset = {0.05: 500, 0.10: 0, 0.20: 2000}[prevalence]
    base_permanova, base_permdisp = COHORT_CONTRACTS[cohort_key]["seeds"]
    return int(base_permanova) + offset, int(base_permdisp) + offset


def validate_production_contract(
    *,
    cohort_key: str,
    cohort_id: str,
    sample_ids: Sequence[str],
    groups: Sequence[str],
    prevalence: float,
    zero_method: str,
    geometry: str,
    permanova_permutations: int,
    permdisp_permutations: int,
    permanova_seed: int,
    permdisp_seed: int,
) -> str:
    if cohort_key not in COHORT_CONTRACTS:
        raise InputValidationError(f"unknown production cohort: {cohort_key}")
    contract = COHORT_CONTRACTS[cohort_key]
    if cohort_id != contract["project"]:
        raise InputValidationError(f"production cohort identifier must be {contract['project']}")
    if len(sample_ids) != contract["n"] or len(set(sample_ids)) != contract["n"]:
        raise InputValidationError(f"production sample count must be exactly {contract['n']} with unique IDs")
    observed = dict(Counter(groups))
    if observed != contract["groups"]:
        raise InputValidationError(
            f"production group counts differ: expected {contract['groups']}, observed {observed}"
        )
    if permanova_permutations != PRODUCTION_PERMUTATIONS or permdisp_permutations != PRODUCTION_PERMUTATIONS:
        raise InputValidationError("production PERMANOVA and PERMDISP must each use exactly 9999 permutations")
    role = analysis_role(prevalence, zero_method, geometry)
    if (permanova_seed, permdisp_seed) != expected_production_seeds(
        cohort_key, prevalence, zero_method, geometry
    ):
        raise InputValidationError("production permutation seeds are not the frozen cell-specific seeds")
    return role


def expected_contract_for_project(project: str) -> tuple[str, Mapping[str, object]]:
    for key, contract in COHORT_CONTRACTS.items():
        if contract["project"] == project:
            return key, contract
    raise InputValidationError(f"unknown production project: {project}")


def validate_expected_czm_library(path: str | Path) -> Path:
    """Reject a production CZM library path other than the frozen isolated target."""
    observed = Path(path).resolve(strict=False)
    expected = EXPECTED_ISOLATED_R_LIBRARY.resolve(strict=False)
    if observed != expected:
        raise InputValidationError(
            f"production CZM library must be the frozen isolated path {expected}; observed {observed}"
        )
    return observed


def validate_production_strata(cohort_key: str, strata: Sequence[str] | None) -> None:
    """Enforce the frozen anchor Training/Test restriction and external design."""
    if cohort_key == "anchor":
        if strata is None or len(strata) != int(COHORT_CONTRACTS["anchor"]["n"]):
            raise InputValidationError("anchor production requires one Training/Test label per sample")
        observed = {str(value).strip() for value in strata}
        if observed != {"Training", "Test"}:
            raise InputValidationError(
                f"anchor production strata must be exactly Training/Test; observed {sorted(observed)}"
            )
    elif cohort_key == "external":
        if strata is not None:
            raise InputValidationError("external primary production permutations must be unrestricted")
    else:
        raise InputValidationError(f"unknown production cohort: {cohort_key}")
