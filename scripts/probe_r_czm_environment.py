#!/usr/bin/env python3
"""Bounded, read-only R/zCompositions environment probe.

This script never installs software, accesses the network, or reads project
data.  It checks only explicit R/Rscript paths and, if an existing Rscript is
available, runs a tiny synthetic CZM call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


R_PAIRS = (
    ("/usr/bin/Rscript", "/usr/bin/R"),
    ("/usr/local/bin/Rscript", "/usr/local/bin/R"),
    ("/home/suma/anaconda3/bin/Rscript", "/home/suma/anaconda3/bin/R"),
    (
        "/home/suma/anaconda3/envs/mgshotgun/bin/Rscript",
        "/home/suma/anaconda3/envs/mgshotgun/bin/R",
    ),
)
SYNTHETIC_INPUT = [
    [10, 0, 2, 0, 8],
    [0, 5, 1, 4, 0],
    [3, 7, 0, 2, 1],
    [0, 2, 8, 0, 6],
]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def inspect_path(path: str) -> dict[str, Any]:
    candidate = Path(path)
    exists = candidate.exists()
    regular = candidate.is_file() if exists else False
    executable = os.access(candidate, os.X_OK) if regular else False
    return {
        "path": path,
        "exists": exists,
        "is_regular_file": regular,
        "is_executable": executable,
        "resolved_path": str(candidate.resolve(strict=False)) if exists else None,
    }


def r_probe_code() -> str:
    # Base R only is used for the output protocol.  No package installation,
    # repository configuration, or network-capable function is called.
    return r'''
emit <- function(kind, key, value) {
  value <- gsub("[\\t\\r\\n]", " ", as.character(value))
  cat(kind, "\t", key, "\t", value, "\n", sep="")
}
emit("KV", "r_version", R.version.string)
emit("KV", "r_major", R.version$major)
emit("KV", "r_minor", R.version$minor)
emit("KV", "r_home", R.home())
emit("KV", "r_library_paths", paste(.libPaths(), collapse="|"))
packages <- c("zCompositions", "NADA", "truncnorm")
for (pkg in packages) {
  present <- requireNamespace(pkg, quietly=TRUE)
  emit("PKG", paste0(pkg, ".installed"), present)
  if (present) {
    emit("PKG", paste0(pkg, ".version"), as.character(packageVersion(pkg)))
    emit("PKG", paste0(pkg, ".path"), find.package(pkg))
    desc <- packageDescription(pkg)
    for (field in c("Package", "Version", "Built", "Packaged", "Repository")) {
      if (!is.null(desc[[field]]) && !is.na(desc[[field]]))
        emit("PKG", paste0(pkg, ".description.", field), desc[[field]])
    }
  }
}
if (requireNamespace("zCompositions", quietly=TRUE)) {
  x <- matrix(c(10,0,2,0,8, 0,5,1,4,0, 3,7,0,2,1, 0,2,8,0,6), nrow=4, byrow=TRUE)
  f <- zCompositions::cmultRepl
  emit("CZM", "formals", paste(names(formals(f)), collapse="|"))
  run_once <- function() f(x, label=0, method="CZM", output="prop", frac=0.65, threshold=0.5, adjust=TRUE)
  first <- tryCatch(run_once(), error=function(e) e)
  if (inherits(first, "error")) {
    emit("CZM", "error", conditionMessage(first))
  } else {
    second <- tryCatch(run_once(), error=function(e) e)
    if (inherits(second, "error")) {
      emit("CZM", "error", conditionMessage(second))
    } else {
      emit("CZM", "rows", nrow(first))
      emit("CZM", "cols", ncol(first))
      emit("CZM", "values", paste(format(as.numeric(first), digits=17, scientific=FALSE, trim=TRUE), collapse=","))
      emit("CZM", "row_sums", paste(format(rowSums(first), digits=17, scientific=FALSE, trim=TRUE), collapse=","))
      emit("CZM", "deterministic", isTRUE(all.equal(first, second, tolerance=0)))
    }
  }
}
'''


def parse_r_output(stdout: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"packages": {}, "czm": {}}
    malformed: list[str] = []
    for line in stdout.splitlines():
        fields = line.split("\t", 2)
        if len(fields) != 3 or fields[0] not in {"KV", "PKG", "CZM"}:
            if line.strip():
                malformed.append(line[:300])
            continue
        kind, key, value = fields
        if kind == "KV":
            parsed[key] = value
        elif kind == "PKG":
            pkg, field = key.split(".", 1)
            parsed["packages"].setdefault(pkg, {})[field] = value
        else:
            parsed["czm"][key] = value
    if malformed:
        parsed["malformed_lines"] = malformed
    return parsed


def bool_value(value: Any) -> bool:
    return str(value).lower() == "true"


def build_report(job_id: str) -> dict[str, Any]:
    rscript_checks = [inspect_path(rscript) for rscript, _ in R_PAIRS]
    r_checks = [inspect_path(r) for _, r in R_PAIRS]
    chosen_rscript = next((item for item in rscript_checks if item["is_executable"]), None)
    chosen_r = next(
        (
            item
            for item in r_checks
            if chosen_rscript
            and item["path"] == next(r for rs, r in R_PAIRS if rs == chosen_rscript["path"])
            and item["is_executable"]
        ),
        None,
    )
    report: dict[str, Any] = {
        "job_id": job_id,
        "probe_status": "CZM_ENVIRONMENT_NOT_READY",
        "candidate_rscript_paths": rscript_checks,
        "candidate_r_paths": r_checks,
        "rscript_found": bool(chosen_rscript),
        "rscript_path": chosen_rscript["resolved_path"] if chosen_rscript else None,
        "r_found": bool(chosen_r),
        "r_path": chosen_r["resolved_path"] if chosen_r else None,
        "r_version": None,
        "r_home": None,
        "r_library_paths": [],
        "packages": {
            pkg: {"installed": False, "version": None, "path": None}
            for pkg in ("zCompositions", "NADA", "truncnorm")
        },
        "czm_probe": {
            "attempted": False,
            "passed": False,
            "function": "zCompositions::cmultRepl",
            "method": "CZM",
            "input_shape": [4, 5],
            "output_shape": None,
            "finite": False,
            "strictly_positive": False,
            "deterministic": False,
            "input_sha256": sha256_bytes(canonical_bytes(SYNTHETIC_INPUT)),
            "output_sha256": None,
            "error_if_any": None,
        },
        "network_acquisition_performed": False,
        "package_installation_performed": False,
        "package_upgrade_performed": False,
        "biological_analysis_executed": False,
        "deepseek_invoked": False,
    }
    if not chosen_rscript:
        report["reason"] = "RSCRIPT_NOT_FOUND"
        return report
    try:
        completed = subprocess.run(
            [chosen_rscript["path"], "--vanilla", "--slave", "-e", r_probe_code()],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        report["reason"] = "RSCRIPT_INVOCATION_FAILED"
        report["r_error"] = str(exc)[:500]
        return report
    parsed = parse_r_output(completed.stdout)
    report["r_version"] = parsed.get("r_version")
    report["r_home"] = parsed.get("r_home")
    report["r_library_paths"] = (parsed.get("r_library_paths") or "").split("|") if parsed.get("r_library_paths") else []
    for pkg in report["packages"]:
        report["packages"][pkg].update(parsed.get("packages", {}).get(pkg, {}))
        report["packages"][pkg]["installed"] = bool_value(report["packages"][pkg].get("installed", False))
    czm = report["czm_probe"]
    czm["attempted"] = report["packages"]["zCompositions"]["installed"]
    if czm["attempted"]:
        if parsed.get("czm", {}).get("error"):
            czm["error_if_any"] = parsed["czm"]["error"][:1000]
            report["reason"] = "CZM_FUNCTIONAL_TEST_FAILED"
        else:
            raw_values = parsed.get("czm", {}).get("values", "")
            try:
                values = [float(item) for item in raw_values.split(",") if item]
                rows = int(parsed["czm"]["rows"])
                cols = int(parsed["czm"]["cols"])
                row_sums = [float(item) for item in parsed["czm"]["row_sums"].split(",") if item]
                output = {"rows": rows, "cols": cols, "values": values, "row_sums": row_sums}
                output_bytes = canonical_bytes(output)
                czm["output_shape"] = [rows, cols]
                czm["finite"] = len(values) == rows * cols and all(map(lambda v: v == v and abs(v) != float("inf"), values))
                czm["strictly_positive"] = bool(values) and all(v > 0 for v in values)
                czm["deterministic"] = bool_value(parsed.get("czm", {}).get("deterministic", False))
                czm["row_sums"] = row_sums
                czm["row_sums_consistent_with_prop"] = len(row_sums) == rows and all(abs(v - 1.0) < 1e-10 for v in row_sums)
                czm["output_sha256"] = sha256_bytes(output_bytes)
                czm["passed"] = all((czm["output_shape"] == [4, 5], czm["finite"], czm["strictly_positive"], czm["deterministic"], czm["row_sums_consistent_with_prop"]))
                if not czm["passed"]:
                    report["reason"] = "CZM_FUNCTIONAL_TEST_FAILED"
            except (KeyError, TypeError, ValueError) as exc:
                czm["error_if_any"] = f"malformed R probe output: {exc}"
                report["reason"] = "MALFORMED_R_OUTPUT"
    else:
        report["reason"] = "ZCOMPOSITIONS_NOT_INSTALLED"
    if completed.returncode != 0 and not report.get("reason"):
        report["reason"] = "RSCRIPT_INVOCATION_FAILED"
        report["r_error"] = (completed.stderr or completed.stdout)[-1000:]
    if report["rscript_found"] and report["packages"]["zCompositions"]["installed"] and czm["passed"]:
        report["probe_status"] = "CZM_ENVIRONMENT_READY"
        report.pop("reason", None)
    return report


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "r_czm_environment_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "job_id": report["job_id"],
        "status": "done",
        "probe_status": report["probe_status"],
        "reason": report.get("reason"),
        "network_acquisition_performed": False,
        "package_installation_performed": False,
        "biological_analysis_executed": False,
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# R/CZM environment probe",
        "",
        f"- Job: `{report['job_id']}`",
        f"- Verdict: `{report['probe_status']}`",
        f"- Rscript: `{report.get('rscript_path') or 'not found'}`",
        f"- R version: `{report.get('r_version') or 'unavailable'}`",
        f"- zCompositions installed: `{report['packages']['zCompositions']['installed']}`",
        f"- CZM synthetic test passed: `{report['czm_probe']['passed']}`",
        f"- Reason: `{report.get('reason', 'none')}`",
        "",
        "No package installation, network acquisition, or biological input access was performed.",
    ]
    (output_dir / "r_czm_environment_probe_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    write_outputs(args.output_dir, build_report(args.job_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
