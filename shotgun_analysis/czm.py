"""Exact production adapter for zCompositions::cmultRepl(method='CZM')."""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path
from typing import Sequence

from .core import _validated_matrix
from .errors import DependencyError, InputValidationError


EXPECTED_ZCOMPOSITIONS_VERSION = "1.6.2"


def exact_czm(
    matrix: Sequence[Sequence[int | float]],
    *,
    r_library: str | Path,
    rscript: str = "Rscript",
    runner: str | Path | None = None,
) -> list[list[float]]:
    """Run the pinned R reference implementation; never approximate CZM."""
    values = _validated_matrix(matrix)
    if all(all(cell > 0 for cell in row) for row in values):
        # The production call is still used so package/version provenance is verified.
        pass
    library = Path(r_library)
    script = Path(runner) if runner else Path(__file__).with_name("run_czm.R")
    if not script.is_file():
        raise DependencyError(f"missing CZM R adapter: {script}")
    if not library.is_dir():
        raise DependencyError(f"zCompositions library is not available: {library}")
    with tempfile.TemporaryDirectory(prefix="shotgun-czm-") as temporary:
        input_path = Path(temporary) / "input.tsv"
        output_path = Path(temporary) / "output.tsv"
        with input_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerows(values)
        command = [rscript, "--vanilla", str(script), str(input_path), str(output_path), str(library)]
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DependencyError(f"CZM adapter could not execute: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown R failure"
            raise DependencyError(f"exact CZM failed closed: {detail}")
        try:
            with output_path.open(newline="", encoding="utf-8") as handle:
                output = [[float(value) for value in row] for row in csv.reader(handle, delimiter="\t")]
        except (OSError, ValueError) as exc:
            raise DependencyError("exact CZM produced malformed output") from exc
    if len(output) != len(values) or any(len(row) != len(values[0]) for row in output):
        raise DependencyError("exact CZM output dimensions differ from input")
    if any(cell <= 0 for row in output for cell in row):
        raise DependencyError("exact CZM output contains non-positive values")
    return output
