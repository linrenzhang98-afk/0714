#!/usr/bin/env python3
"""Install a CRAN-locked CZM stack into an isolated ETYY R library only.

All source archives must already have been acquired by etty_bounded_job.  This
script has no network code and uses only absolute R/Rscript paths.  It always
writes a compact validation report; an unsuccessful package installation is a
method verdict, not a reason to hide the evidence from the handoff.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


R_PATH = "/home/suma/anaconda3/envs/mgshotgun/bin/R"
RSCRIPT_PATH = "/home/suma/anaconda3/envs/mgshotgun/bin/Rscript"
SYSTEM_LIBRARY = Path("/home/suma/anaconda3/envs/mgshotgun/lib/R/library")
ISOLATED_PARENT = Path("/mnt/disk1/0714_control/r_libs")
EXPECTED_R_VERSION = "4.5.3"
MGSHOTGUN_BIN = "/home/suma/anaconda3/envs/mgshotgun/bin"
R_REQUIRED_EXECUTABLES = ("x86_64-conda-linux-gnu-cc", "x86_64-conda-linux-gnu-c++", "x86_64-conda-linux-gnu-gfortran", "sh", "uname", "make")
MAKECONF_COMPILERS = R_REQUIRED_EXECUTABLES[:3]
SYNTHETIC_INPUT = [[10, 0, 2, 0, 8], [0, 5, 1, 4, 0], [3, 7, 0, 2, 1], [0, 2, 8, 0, 6]]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def q(value: str) -> str:
    return json.dumps(value)


def execution_environment() -> dict[str, str]:
    environment = os.environ.copy()
    path_components = [MGSHOTGUN_BIN]
    for component in (environment.get("PATH", "").split(os.pathsep) + os.defpath.split(os.pathsep)):
        if component and component not in path_components:
            path_components.append(component)
    environment["PATH"] = os.pathsep.join(path_components)
    return environment


def compiler_probe() -> tuple[dict[str, str], str | None]:
    environment = execution_environment()
    resolved = {name: shutil.which(name, path=environment["PATH"]) for name in R_REQUIRED_EXECUTABLES}
    missing = next((name for name, path in resolved.items() if not path), None)
    return {name: path for name, path in resolved.items() if path}, missing


def run_r(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [RSCRIPT_PATH, "--vanilla", "--slave", "-e", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        shell=False,
        env=execution_environment(),
    )


def parse_protocol(text: str) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    malformed: list[str] = []
    for line in text.splitlines():
        fields = line.split("\t", 2)
        if len(fields) == 3 and fields[0] == "KV":
            values[fields[1]] = fields[2]
        elif line.strip():
            malformed.append(line[:300])
    return values, malformed


def inventory_code(library: Path) -> str:
    return f'''ip <- installed.packages(lib.loc={q(str(library))})
for (pkg in rownames(ip)) cat("KV\\tPKG:" , pkg, "\\t", ip[pkg, "Version"], "\\n", sep="")
'''


def r_inventory(library: Path) -> tuple[dict[str, str], str | None]:
    if not library.is_dir():
        return {}, f"library missing: {library}"
    try:
        completed = run_r(inventory_code(library))
    except (OSError, subprocess.SubprocessError) as exc:
        return {}, str(exc)
    values, malformed = parse_protocol(completed.stdout)
    if completed.returncode != 0 or malformed:
        return {}, (completed.stderr or "malformed R inventory output")[-1000:]
    return {key[4:]: value for key, value in values.items() if key.startswith("PKG:")}, None


def r_runtime_info() -> tuple[str | None, str | None]:
    try:
        completed = run_r('cat("KV\\tr_version\\t", R.version.string, "\\n", sep="")')
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    values, malformed = parse_protocol(completed.stdout)
    if completed.returncode or malformed or not values.get("r_version"):
        return None, (completed.stderr or "malformed R version output")[-1000:]
    return values["r_version"], None


def confined_isolated_path(target: Path) -> bool:
    if not target.is_absolute() or ".." in target.parts:
        return False
    return target.resolve(strict=False).parent == ISOLATED_PARENT.resolve(strict=False)


def system_library_unchanged(before: dict[str, str], after: dict[str, str]) -> tuple[bool, bool]:
    return set(before) == set(after), before == after


def lock_new_packages(lock: dict[str, Any]) -> list[dict[str, Any]]:
    packages = [item for item in lock["packages"] if item.get("install_new")]
    return sorted(packages, key=lambda item: item["installation_order"])


def validate_isolated_inventory(inventory: dict[str, str], lock: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    allowed_versions = {item["package"]: item["version"] for item in lock_new_packages(lock)}
    unexpected = sorted(set(inventory) - set(allowed_versions))
    mismatched = sorted(package for package, version in inventory.items() if package in allowed_versions and allowed_versions[package] != version)
    return not unexpected and not mismatched, unexpected, mismatched


def missing_locked_packages(lock: dict[str, Any], inventory: dict[str, str]) -> list[dict[str, Any]]:
    return [package for package in lock_new_packages(lock) if package["package"] not in inventory]


def validate_tarballs(lock: dict[str, Any], source_dir: Path) -> tuple[list[dict[str, Any]], str | None]:
    verified: list[dict[str, Any]] = []
    for package in lock_new_packages(lock):
        tarball = source_dir / package["source_filename"]
        if not tarball.is_file():
            return verified, f"SOURCE_TARBALL_MISSING:{package['package']}"
        if tarball.stat().st_size != package["expected_bytes"]:
            return verified, f"SOURCE_BYTES_MISMATCH:{package['package']}"
        actual = digest(tarball)
        if actual != package["expected_sha256"]:
            return verified, f"SOURCE_CHECKSUM_MISMATCH:{package['package']}"
        verified.append({**package, "tarball_path": str(tarball), "actual_sha256": actual})
    return verified, None


def install_package(package: dict[str, Any], target: Path) -> tuple[bool, str | None]:
    completed = subprocess.run(
        [R_PATH, "CMD", "INSTALL", f"--library={target}", package["tarball_path"]],
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
        shell=False,
        env=execution_environment(),
    )
    if completed.returncode:
        return False, (completed.stderr or completed.stdout)[-2000:]
    return True, None


def validation_code(isolated: Path) -> str:
    return f'''emit <- function(k,v) {{
  v <- gsub("[\\t\\r\\n]", " ", as.character(v)); cat("KV\\t", k, "\\t", v, "\\n", sep="")
}}
describe <- function(value, label) {{
  emit(paste0(label, "_class"), paste(class(value), collapse="|"))
  emit(paste0(label, "_typeof"), typeof(value))
  emit(paste0(label, "_names"), paste(names(value) %||% character(), collapse="|"))
  dims <- dim(value); emit(paste0(label, "_dim"), if (is.null(dims)) "" else paste(dims, collapse="x"))
  emit(paste0(label, "_is_matrix"), is.matrix(value))
  emit(paste0(label, "_is_data_frame"), is.data.frame(value))
  emit(paste0(label, "_is_list"), is.list(value))
  structure <- paste(capture.output(str(value, max.level=2, vec.len=6)), collapse=" ")
  emit(paste0(label, "_str"), substr(structure, 1, 1000))
}}
`%||%` <- function(x, y) if (is.null(x)) y else x
numeric_component <- function(value, path="result") {{
  candidates <- list()
  visit <- function(candidate, candidate_path) {{
    dims <- dim(candidate)
    matrix_like <- (is.matrix(candidate) || is.data.frame(candidate)) && is.numeric(as.matrix(candidate)) && !is.null(dims) && identical(as.integer(dims), c(4L, 5L))
    if (matrix_like) candidates[[length(candidates) + 1L]] <<- list(path=candidate_path, value=as.matrix(candidate))
    else if (is.list(candidate) && !is.data.frame(candidate)) for (i in seq_along(candidate)) visit(candidate[[i]], paste0(candidate_path, "[[", i, "]]"))
  }}
  visit(value, path)
  if (length(candidates) != 1L) stop(sprintf("expected exactly one numeric 4x5 component, found %d", length(candidates)))
  candidates[[1L]]
}}
.libPaths(c({q(str(isolated))}, {q(str(SYSTEM_LIBRARY))}))
emit("r_version", R.version.string)
emit("libpaths", paste(.libPaths(), collapse="|"))
for (pkg in c("MASS", "survival", "NADA", "truncnorm", "zCompositions")) {{
  present <- requireNamespace(pkg, quietly=TRUE)
  emit(paste0("present:", pkg), present)
  if (present) {{ emit(paste0("version:", pkg), as.character(packageVersion(pkg))); emit(paste0("path:", pkg), find.package(pkg)) }}
}}
x <- matrix(c(10,0,2,0,8, 0,5,1,4,0, 3,7,0,2,1, 0,2,8,0,6), nrow=4, byrow=TRUE)
run_once <- function() zCompositions::cmultRepl(x, label=0, method="CZM", output="prop", frac=0.65, threshold=0.5, adjust=TRUE, suppress.print=TRUE)
first <- tryCatch(run_once(), error=function(e) e)
if (inherits(first, "error")) {{ emit("czm_error", conditionMessage(first)) }} else {{
  describe(first, "first")
  first_component <- tryCatch(numeric_component(first, "first"), error=function(e) e)
  if (inherits(first_component, "error")) {{ emit("czm_error", conditionMessage(first_component)) }} else {{
  emit("selected_component_path", first_component$path)
  second <- tryCatch(run_once(), error=function(e) e)
  if (inherits(second, "error")) {{ emit("czm_error", conditionMessage(second)) }} else {{
    describe(second, "second")
    second_component <- tryCatch(numeric_component(second, "second"), error=function(e) e)
    if (inherits(second_component, "error")) {{ emit("czm_error", conditionMessage(second_component)) }} else {{
    emit("czm_rows", nrow(first_component$value)); emit("czm_cols", ncol(first_component$value))
    emit("czm_values", paste(format(as.numeric(first_component$value), digits=17, scientific=FALSE, trim=TRUE), collapse=","))
    emit("czm_repeat_values", paste(format(as.numeric(second_component$value), digits=17, scientific=FALSE, trim=TRUE), collapse=","))
    emit("czm_row_sums", paste(format(rowSums(first_component$value), digits=17, scientific=FALSE, trim=TRUE), collapse=","))
    emit("czm_loaded_namespaces", paste(sort(loadedNamespaces()), collapse="|"))
    }}
  }}
  }}
  }}
}}
'''


def validate_czm(isolated: Path) -> tuple[dict[str, Any], str | None]:
    result: dict[str, Any] = {
        "attempted": False,
        "passed": False,
        "function": "zCompositions::cmultRepl",
        "method": "CZM",
        "exact_call": "zCompositions::cmultRepl(x, label=0, method='CZM', output='prop', frac=0.65, threshold=0.5, adjust=TRUE, suppress.print=TRUE)",
        "input_shape": [4, 5],
        "output_shape": None,
        "finite": False,
        "strictly_positive": False,
        "deterministic": False,
        "input_sha256": hashlib.sha256(canonical(SYNTHETIC_INPUT)).hexdigest(),
        "output_sha256": None,
        "repeat_output_sha256": None,
        "error_if_any": None,
        "return_structure": {},
        "selected_component_path": None,
    }
    try:
        completed = run_r(validation_code(isolated))
    except (OSError, subprocess.SubprocessError) as exc:
        result["error_if_any"] = str(exc)
        return result, "RSCRIPT_VALIDATION_FAILED"
    values, malformed = parse_protocol(completed.stdout)
    if completed.returncode or malformed:
        result["error_if_any"] = (completed.stderr or "malformed R validation output")[-1000:]
        return result, "MALFORMED_R_OUTPUT"
    result["attempted"] = True
    result["return_structure"] = {key[6:]: values[key] for key in values if key.startswith("first_")}
    result["return_structure"]["second"] = {key[7:]: values[key] for key in values if key.startswith("second_")}
    result["selected_component_path"] = values.get("selected_component_path")
    if "czm_error" in values:
        result["error_if_any"] = values["czm_error"]
        return result, "CZM_FUNCTIONAL_TEST_FAILED"
    try:
        rows, cols = int(values["czm_rows"]), int(values["czm_cols"])
        first = [float(x) for x in values["czm_values"].split(",") if x]
        second = [float(x) for x in values["czm_repeat_values"].split(",") if x]
        sums = [float(x) for x in values["czm_row_sums"].split(",") if x]
    except (KeyError, ValueError) as exc:
        result["error_if_any"] = f"malformed R output: {exc}"
        return result, "MALFORMED_R_OUTPUT"
    first_payload = {"rows": rows, "cols": cols, "values": first, "row_sums": sums}
    second_payload = {"rows": rows, "cols": cols, "values": second, "row_sums": sums}
    result.update({
        "output_shape": [rows, cols],
        "finite": len(first) == rows * cols and all(math.isfinite(x) for x in first),
        "strictly_positive": bool(first) and all(x > 0 for x in first),
        "deterministic": first == second,
        "row_sum_behavior": sums,
        "row_sums_equal_one": len(sums) == rows and all(abs(x - 1.0) < 1e-10 for x in sums),
        "output_sha256": hashlib.sha256(canonical(first_payload)).hexdigest(),
        "repeat_output_sha256": hashlib.sha256(canonical(second_payload)).hexdigest(),
        "loaded_namespaces": (values.get("czm_loaded_namespaces") or "").split("|"),
    })
    result["passed"] = all((result["output_shape"] == [4, 5], result["finite"], result["strictly_positive"], result["deterministic"], result["row_sums_equal_one"], result["output_sha256"] == result["repeat_output_sha256"]))
    return result, None if result["passed"] else "CZM_FUNCTIONAL_TEST_FAILED"


def build_report(job_id: str, lock: dict[str, Any], source_dir: Path, isolated: Path, perform_install: bool = True) -> dict[str, Any]:
    report: dict[str, Any] = {
        "job_id": job_id,
        "status": "CZM_ISOLATED_LIBRARY_NOT_READY",
        "r_version": None,
        "r_path": R_PATH,
        "rscript_path": RSCRIPT_PATH,
        "isolated_library_path": str(isolated),
        "zCompositions": {"requested_version": "1.6.2", "installed_version": None, "installed_path": None, "source_url": None, "source_checksum": None, "version_match": False},
        "dependencies": {},
        "system_library": {"path": str(SYSTEM_LIBRARY), "package_set_changed": None, "package_versions_changed": None},
        "compiler_probe": {"required": list(R_REQUIRED_EXECUTABLES), "resolved_paths": {}, "passed": False},
        "czm_probe": {"attempted": False, "passed": False, "function": "zCompositions::cmultRepl", "method": "CZM", "input_shape": [4, 5], "output_shape": None, "finite": False, "strictly_positive": False, "deterministic": False, "input_sha256": hashlib.sha256(canonical(SYNTHETIC_INPUT)).hexdigest(), "output_sha256": None, "repeat_output_sha256": None, "error_if_any": None},
        "network_acquisition_performed": perform_install,
        "downloaded_package_count": len(lock_new_packages(lock)) if perform_install else 0,
        "downloaded_bytes": lock["total_expected_download_bytes"] if perform_install else 0,
        "package_installation_performed": False,
        "package_upgrade_performed": False,
        "system_library_modified": False,
        "nada_status": "UNKNOWN",
        "truncnorm_status": "UNKNOWN",
        "biological_analysis_executed": False,
        "deepseek_invoked": False,
        "reason": None,
    }
    for package in lock["packages"]:
        report["dependencies"][package["package"]] = {"required": True, "reused_existing": not package.get("install_new", False), "installed_new": False, "version": package.get("version"), "path": None, "source_url_if_downloaded": package.get("source_url"), "checksum_if_downloaded": package.get("expected_sha256")}
    target_info = next(x for x in lock_new_packages(lock) if x["package"] == "zCompositions")
    report["zCompositions"].update({"source_url": target_info["source_url"], "source_checksum": target_info["expected_sha256"]})
    if not confined_isolated_path(isolated):
        report["reason"] = "ISOLATED_LIBRARY_PATH_ESCAPE"
        return report
    resolved_compilers, missing_compiler = compiler_probe()
    report["compiler_probe"].update({"resolved_paths": resolved_compilers, "passed": missing_compiler is None})
    if missing_compiler:
        report["reason"] = f"COMPILER_UNAVAILABLE:{missing_compiler}"
        return report
    r_version, error = r_runtime_info()
    report["r_version"] = r_version
    if error or not r_version or EXPECTED_R_VERSION not in r_version:
        report["reason"] = "R_VERSION_MISMATCH_OR_UNAVAILABLE"
        report["r_error"] = error
        return report
    before, error = r_inventory(SYSTEM_LIBRARY)
    if error:
        report["reason"] = "SYSTEM_LIBRARY_INVENTORY_FAILED"
        report["system_library"]["error"] = error
        return report
    report["system_library"]["before"] = before
    if "MASS" not in before or "survival" not in before:
        report["reason"] = "REQUIRED_SYSTEM_DEPENDENCY_MISSING"
        return report
    isolated_inventory, inventory_error = r_inventory(isolated) if isolated.exists() else ({}, None)
    inventory_valid, unexpected, mismatched = validate_isolated_inventory(isolated_inventory, lock)
    if inventory_error or not inventory_valid:
        report["isolated_inventory"] = isolated_inventory
        report["reason"] = "ISOLATED_LIBRARY_CONTENTS_INVALID"
        if inventory_error:
            report["isolated_inventory_error"] = inventory_error
        if unexpected:
            report["unexpected_packages"] = unexpected
        if mismatched:
            report["version_mismatches"] = mismatched
        return report
    for package, version in isolated_inventory.items():
        report["dependencies"][package].update({"reused_partial": True, "version": version, "path": str(isolated / package)})
    if perform_install:
        tarballs, error = validate_tarballs(lock, source_dir)
        if error:
            report["reason"] = error
            return report
        isolated.mkdir(parents=True, exist_ok=True)
        for package in (package for package in tarballs if package["package"] in {item["package"] for item in missing_locked_packages(lock, isolated_inventory)}):
            ok, error = install_package(package, isolated)
            if not ok:
                report["reason"] = f"PACKAGE_INSTALL_FAILED:{package['package']}"
                report["install_error"] = error
                break
            report["package_installation_performed"] = True
            report["dependencies"][package["package"]].update({"installed_new": True, "path": str(isolated / package["package"])})
    after, inventory_error = r_inventory(SYSTEM_LIBRARY)
    report["system_library"]["after"] = after
    same_set, same_versions = system_library_unchanged(before, after)
    report["system_library"]["package_set_changed"] = not same_set
    report["system_library"]["package_versions_changed"] = not same_versions
    report["system_library_modified"] = bool(report["system_library"]["package_set_changed"] or report["system_library"]["package_versions_changed"])
    if inventory_error:
        report["reason"] = report["reason"] or "SYSTEM_LIBRARY_POST_INVENTORY_FAILED"
        return report
    if report["system_library_modified"]:
        report["reason"] = report["reason"] or "SYSTEM_LIBRARY_CHANGED"
        return report
    if report["reason"]:
        return report
    isolated_inventory, error = r_inventory(isolated)
    allowed_new = {item["package"] for item in lock_new_packages(lock)}
    versions_match, _, _ = validate_isolated_inventory(isolated_inventory, lock)
    if error or set(isolated_inventory) != allowed_new or not versions_match:
        report["reason"] = "ISOLATED_LIBRARY_CONTENTS_INVALID"
        report["isolated_inventory"] = isolated_inventory
        return report
    probe, error = validate_czm(isolated)
    report["czm_probe"] = probe
    for package, version in {**before, **isolated_inventory}.items():
        if package in report["dependencies"]:
            report["dependencies"][package]["version"] = version
            if package in before:
                report["dependencies"][package]["path"] = str(SYSTEM_LIBRARY / package)
    report["zCompositions"].update({"installed_version": isolated_inventory.get("zCompositions"), "installed_path": str(isolated / "zCompositions"), "version_match": isolated_inventory.get("zCompositions") == "1.6.2"})
    report["nada_status"] = "REQUIRED_AND_INSTALLED" if "NADA" in isolated_inventory else "UNKNOWN"
    report["truncnorm_status"] = "REQUIRED_AND_INSTALLED" if "truncnorm" in isolated_inventory else "UNKNOWN"
    if error:
        report["reason"] = error
        return report
    report["status"] = "CZM_ISOLATED_LIBRARY_READY"
    report["reason"] = None
    return report


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "r_czm_install_validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    source_note = "No network acquisition or package installation was performed; only the existing isolated stack and synthetic matrix were used." if not report["network_acquisition_performed"] else "Only locked CRAN source tarballs and a synthetic matrix were used."
    lines = ["# Isolated zCompositions installation validation", "", f"- Job: `{report['job_id']}`", f"- Verdict: `{report['status']}`", f"- Reason: `{report.get('reason') or 'none'}`", f"- R: `{report.get('r_version') or 'unavailable'}`", f"- zCompositions version match: `{report['zCompositions']['version_match']}`", f"- CZM synthetic test: `{report['czm_probe']['passed']}`", f"- System library modified: `{report['system_library']['package_set_changed'] or report['system_library']['package_versions_changed']}`", "", source_note]
    (output_dir / "r_czm_install_summary.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("noop", "install", "validate"), default="install")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--isolated-library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "noop":
        return 0
    try:
        lock = json.loads(args.lock.read_text())
        report = build_report(args.job_id, lock, args.source_dir, args.isolated_library, perform_install=args.mode == "install")
    except Exception as exc:  # preserve bounded diagnostic evidence for any implementation failure
        report = {"job_id": args.job_id, "status": "CZM_ISOLATED_LIBRARY_NOT_READY", "reason": "INSTALLER_INTERNAL_ERROR", "error": f"{type(exc).__name__}: {exc}"[:1000], "biological_analysis_executed": False, "deepseek_invoked": False}
    write_outputs(args.output_dir, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
