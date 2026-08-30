"""Prospectively frozen, cohort-specific shotgun ecology analysis utilities.

This package contains no data and performs no work at import time.  The exact
CZM implementation remains delegated to zCompositions 1.6.2 through the
explicit adapter in :mod:`shotgun_analysis.czm`.
"""

from .core import (
    additive_pseudocount,
    aitchison_distance,
    classified_fraction,
    close_composition,
    clr_transform,
    diversity_metrics,
    prevalence_filter,
)
from .errors import AnalysisError, DegenerateDesignError, DependencyError, InputValidationError

__all__ = [
    "AnalysisError",
    "DegenerateDesignError",
    "DependencyError",
    "InputValidationError",
    "aitchison_distance",
    "additive_pseudocount",
    "classified_fraction",
    "close_composition",
    "clr_transform",
    "diversity_metrics",
    "prevalence_filter",
]
