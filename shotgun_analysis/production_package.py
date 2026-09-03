"""Fail-closed gate and deterministic production-package provenance helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import InputValidationError

GATE_JOB_ID = "20260904T060000Z-0714-zcompositions-1-6-2-isolated-czm-syntax-validation"
REQUIRED_ARTIFACTS = (
    "sample_manifest.tsv", "exclusions.tsv", "feature_filter_summary.json",
    "czm_provenance.json", "clr_provenance.json", "permanova_results.json",
    "permanova_results.tsv", "permdisp_results.json", "permdisp_results.tsv",
    "sensitivity_summary.json", "warnings.json", "session_versions.json",
    "output_hashes.json", "analysis_manifest.json",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_czm_gate(path: str | Path, expected_sha256: str) -> Mapping[str, Any]:
    source = Path(path)
    if not source.is_file() or sha256_file(source) != expected_sha256:
        raise InputValidationError("authoritative CZM gate evidence is missing or has a SHA256 mismatch")
    evidence = json.loads(source.read_text(encoding="utf-8"))
    expected = {
        "job_id": GATE_JOB_ID, "status": "CZM_ISOLATED_LIBRARY_READY",
        "network_acquisition_performed": False, "package_installation_performed": False,
        "system_library_modified": False,
    }
    for key, value in expected.items():
        if evidence.get(key) != value:
            raise InputValidationError(f"authoritative CZM gate mismatch: {key}")
    probe = evidence.get("czm_probe", {})
    if not probe.get("passed"):
        raise InputValidationError("authoritative CZM synthetic probe did not pass")
    if evidence.get("r_version") not in {"R version 4.5.3", "4.5.3"}:
        raise InputValidationError("authoritative CZM gate R version mismatch")
    versions = evidence.get("isolated_library_after", evidence.get("isolated_inventory_after", {}))
    if versions.get("zCompositions") != "1.6.2":
        raise InputValidationError("authoritative CZM gate zCompositions version mismatch")
    return evidence


def output_hashes(root: str | Path, names: Sequence[str]) -> dict[str, str]:
    return {name: sha256_file(Path(root) / name) for name in sorted(names)}


def analysis_manifest(payload: Mapping[str, Any], hashes: Mapping[str, str]) -> dict[str, Any]:
    if "analysis_manifest.json" in hashes or "output_hashes.json" in hashes:
        raise InputValidationError("recursive manifest/hash reference is forbidden")
    required = {name for name in REQUIRED_ARTIFACTS if name not in {"analysis_manifest.json", "output_hashes.json"}}
    if required - set(hashes):
        raise InputValidationError(f"production package is missing required artifacts: {sorted(required-set(hashes))}")
    return {**dict(payload), "output_hashes": dict(sorted(hashes.items())),
            "hash_policy": "analysis_manifest.json and output_hashes.json are excluded from their own hash set"}
