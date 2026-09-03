#!/usr/bin/env python3
"""Run the complete frozen Aitchison grid and single Bray comparator.

This workstation-ready driver creates no job and performs no discovery. It is
not to be invoked on biological inputs until the recovery/runtime/authorization
gates in the runbook have passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("anchor", "external"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--sample-qc", type=Path, required=True)
    parser.add_argument("--r-library", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--czm-gate-evidence", type=Path, required=True)
    parser.add_argument("--czm-gate-sha256", required=True)
    parser.add_argument("--permutations", type=int, choices=(9999,), default=9999)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = Path(__file__).with_name("run_formal_cross_cohort_analysis.py")
    for zero_method in ("czm", "additive_pseudocount"):
        for prevalence in (0.05, 0.10, 0.20):
            cell = args.output_root / f"aitchison_{zero_method}_prev{int(prevalence * 100):02d}"
            command = [
                sys.executable, str(runner), "--cohort", args.cohort,
                "--manifest", str(args.manifest), "--counts", str(args.counts),
                "--sample-qc", str(args.sample_qc), "--r-library", str(args.r_library),
                "--output", str(cell), "--prevalence", str(prevalence),
                "--zero-method", zero_method, "--geometry", "Aitchison",
                "--permutations", str(args.permutations),
                "--analysis-id", f"{args.analysis_id}:{cell.name}",
                "--czm-gate-evidence", str(args.czm_gate_evidence), "--czm-gate-sha256", args.czm_gate_sha256,
            ]
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                return completed.returncode
    bray_cell = args.output_root / "bray_curtis_none_prev10"
    bray_command = [
        sys.executable, str(runner), "--cohort", args.cohort,
        "--manifest", str(args.manifest), "--counts", str(args.counts),
        "--sample-qc", str(args.sample_qc), "--r-library", str(args.r_library),
        "--output", str(bray_cell), "--prevalence", "0.10",
        "--zero-method", "none", "--geometry", "Bray-Curtis",
        "--permutations", str(args.permutations),
        "--analysis-id", f"{args.analysis_id}:{bray_cell.name}",
        "--czm-gate-evidence", str(args.czm_gate_evidence), "--czm-gate-sha256", args.czm_gate_sha256,
    ]
    completed = subprocess.run(bray_command, check=False)
    if completed.returncode != 0:
        return completed.returncode
    cell_dirs = sorted(path for path in args.output_root.iterdir() if path.is_dir())
    summaries = [json.loads((path / "sensitivity_summary.json").read_text()) for path in cell_dirs]
    (args.output_root / "sensitivity_summary.json").write_text(json.dumps({"cohort": args.cohort, "cells": summaries}, indent=2, sort_keys=True) + "\n")
    completion = args.output_root / "GRID_COMPLETE.json"
    if completion.exists():
        raise RuntimeError("grid completion marker already exists")
    completion.write_text(
        '{"status":"COMPLETE","cells":7,"permutations":9999}\n', encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
