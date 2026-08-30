#!/usr/bin/env python3
"""Run the complete prespecified Aitchison sensitivity grid for one cohort.

This workstation-ready driver creates no job and performs no discovery. It is
not to be invoked on biological inputs until the recovery/runtime/authorization
gates in the runbook have passed.
"""

from __future__ import annotations

import argparse
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
    parser.add_argument("--permutations", type=int, default=9999)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = Path(__file__).with_name("run_formal_cross_cohort_analysis.py")
    for zero_method in ("czm", "pseudocount_0.5"):
        for prevalence in (0.05, 0.10, 0.20):
            cell = args.output_root / f"aitchison_{zero_method}_prev{int(prevalence * 100):02d}"
            command = [
                sys.executable, str(runner), "--cohort", args.cohort,
                "--manifest", str(args.manifest), "--counts", str(args.counts),
                "--sample-qc", str(args.sample_qc), "--r-library", str(args.r_library),
                "--output", str(cell), "--prevalence", str(prevalence),
                "--zero-method", zero_method, "--permutations", str(args.permutations),
            ]
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
