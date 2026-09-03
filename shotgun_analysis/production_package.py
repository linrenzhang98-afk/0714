"""Fail-closed gate and deterministic production-package provenance helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import InputValidationError

GATE_JOB_ID = "20260904T060000Z-0714-zcompositions-1-6-2-isolated-czm-syntax-validation"
PINNED_GATE_ROOT = Path(__file__).resolve().parents[1] / "provenance" / "czm_gate"
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


def validate_czm_gate(snapshot_root: str | Path) -> Mapping[str, Any]:
    root = Path(snapshot_root)
    provenance_path = root / "czm_gate_provenance.json"
    validation_path = root / "r_czm_install_validation.json"
    summary_path = root / "r_czm_install_summary.md"
    if not all(path.is_file() for path in (provenance_path, validation_path, summary_path)):
        raise InputValidationError("pinned CZM gate provenance snapshot is incomplete")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if sha256_file(validation_path) != provenance.get("source_validation_sha256"):
        raise InputValidationError("pinned CZM validation evidence SHA256 mismatch")
    if sha256_file(summary_path) != provenance.get("source_summary_sha256"):
        raise InputValidationError("pinned CZM summary evidence SHA256 mismatch")
    evidence = json.loads(validation_path.read_text(encoding="utf-8"))
    expected = {
        "job_id": GATE_JOB_ID, "status": "CZM_ISOLATED_LIBRARY_READY", "reason": None,
        "network_acquisition_performed": False, "package_installation_performed": False,
        "system_library_modified": False,
    }
    provenance_keys = {"job_id": "authoritative_job_id", "status": "required_status",
                       "network_acquisition_performed": "required_network_acquisition",
                       "package_installation_performed": "required_package_installation",
                       "system_library_modified": "required_system_library_modified",
                       "biological_analysis_executed": "required_biological_analysis"}
    for key, value in expected.items():
        provenance_value = provenance.get(provenance_keys.get(key, ""), value)
        if evidence.get(key) != value or provenance_value != value:
            raise InputValidationError(f"authoritative CZM gate mismatch: {key}")
    probe = evidence.get("czm_probe", {})
    if not all(probe.get(key) is True for key in ("attempted", "passed", "finite", "strictly_positive", "deterministic", "row_sums_equal_one")) or probe.get("output_shape") != [4, 5] or probe.get("output_sha256") != probe.get("repeat_output_sha256"):
        raise InputValidationError("authoritative CZM synthetic probe did not pass")
    if not str(evidence.get("r_version", "")).startswith("R version 4.5.3"):
        raise InputValidationError("authoritative CZM gate R version mismatch")
    dependencies = evidence.get("dependencies", {})
    if evidence.get("system_library", {}).get("package_set_changed") or evidence.get("system_library", {}).get("package_versions_changed"):
        raise InputValidationError("authoritative CZM gate system library changed")
    if evidence.get("r_path") != "/home/suma/anaconda3/envs/mgshotgun/bin/R" or evidence.get("rscript_path") != "/home/suma/anaconda3/envs/mgshotgun/bin/Rscript":
        raise InputValidationError("authoritative CZM gate runtime path mismatch")
    if evidence.get("isolated_library_path") != "/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3" or any(dependencies.get(pkg, {}).get("version") != version for pkg, version in {"zCompositions": "1.6.2", "NADA": "1.6-1.2", "truncnorm": "1.0-9"}.items()):
        raise InputValidationError("authoritative CZM gate zCompositions version mismatch")
    evidence["source_validation_sha256"] = provenance["source_validation_sha256"]
    evidence["source_summary_sha256"] = provenance["source_summary_sha256"]
    return evidence


def validate_pinned_czm_gate() -> Mapping[str, Any]:
    return validate_czm_gate(PINNED_GATE_ROOT)


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
