"""Fail-closed exception types for the formal shotgun analysis."""


class AnalysisError(RuntimeError):
    """Base class for analysis failures that must stop result production."""


class InputValidationError(AnalysisError):
    """Input data or metadata violate the frozen contract."""


class DependencyError(AnalysisError):
    """A version-pinned production dependency is missing or incompatible."""


class DegenerateDesignError(AnalysisError):
    """A statistical design cannot support the requested test."""
