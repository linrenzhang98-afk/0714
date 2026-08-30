"""Structured result validation, serialization, and compact-table writing."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import InputValidationError


def reject_nonfinite(value: Any, path: str = "result") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InputValidationError(f"non-finite number at {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            reject_nonfinite(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            reject_nonfinite(child, f"{path}[{index}]")
        return
    raise InputValidationError(f"unsupported result value at {path}: {type(value).__name__}")


def validate_result(result: Mapping[str, Any], schema_path: str | Path) -> None:
    reject_nonfinite(result)
    try:
        import jsonschema
    except ImportError as exc:
        raise InputValidationError("jsonschema is required for result validation") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(dict(result))
    except jsonschema.ValidationError as exc:
        raise InputValidationError(f"result schema validation failed: {exc.message}") from exc


def write_json(path: str | Path, value: Mapping[str, Any], schema_path: str | Path | None = None) -> None:
    reject_nonfinite(value)
    if schema_path is not None:
        validate_result(value, schema_path)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_compact_tsv(path: str | Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    if not rows:
        raise InputValidationError("compact table has no rows")
    if not fields or len(set(fields)) != len(fields):
        raise InputValidationError("compact table fields must be non-empty and unique")
    reject_nonfinite(rows)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
