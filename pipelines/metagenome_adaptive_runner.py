#!/usr/bin/env python3
"""Adaptive metagenome pipeline wrapper with Kraken2/Bracken first pass."""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_job(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def command_exists(command: str) -> bool:
    return subprocess.run(["bash", "-lc", f"command -v {sh_quote(command)}"], check=False).returncode == 0


def find_fastqs(input_dir: Path) -> list[str]:
    patterns = ["*.fastq", "*.fq", "*.fastq.gz", "*.fq.gz"]
    files: list[str] = []
    for pattern in patterns:
        files.extend(glob.glob(str(input_dir / pattern)))
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and plan metagenome analysis")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = load_job(job_path)
    params: dict[str, Any] = job.get("params", {})

    input_dir = Path(params.get("input_dir", ""))
    kraken2_db = Path(params.get("kraken2_db", ""))
    bracken_db = Path(params.get("bracken_db", str(kraken2_db)))
    threads = int(params.get("threads", max(1, (os.cpu_count() or 2) - 1)))
    read_type = params.get("read_type", "paired")

    errors: list[str] = []
    warnings: list[str] = []
    if not input_dir.exists() or not input_dir.is_dir():
        errors.append(f"input_dir not found: {input_dir}")
    if not kraken2_db.exists() or not kraken2_db.is_dir():
        errors.append(f"kraken2_db not found: {kraken2_db}")
    if not bracken_db.exists() or not bracken_db.is_dir():
        errors.append(f"bracken_db not found: {bracken_db}")
    if read_type not in {"paired", "single"}:
        errors.append("read_type must be paired or single")
    if not command_exists("kraken2"):
        errors.append("kraken2 command not found in PATH or active environment")
    if not command_exists("bracken"):
        warnings.append("bracken command not found; Kraken2 report will still be planned")

    fastqs = find_fastqs(input_dir) if input_dir.exists() else []
    if not fastqs:
        errors.append(f"No FASTQ files found in {input_dir}")

    safe_threads = max(1, min(threads, max(1, int((os.cpu_count() or 2) * 0.8))))
    if safe_threads != threads:
        warnings.append(f"threads reduced from {threads} to {safe_threads}")

    report = {
        "job_id": job.get("job_id"),
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline": "metagenome_adaptive",
        "input_fastq_count": len(fastqs),
        "errors": errors,
        "warnings": warnings,
        "first_pass": "kraken2_bracken",
    }
    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"mkdir -p {sh_quote(str(out_dir / 'kraken2'))}",
        "# This first-pass plan writes per-input Kraken2 outputs. Pairing can be tightened once project naming is known.",
    ]
    for fastq in fastqs:
        sample = Path(fastq).name
        for suffix in [".fastq.gz", ".fq.gz", ".fastq", ".fq"]:
            if sample.endswith(suffix):
                sample = sample[: -len(suffix)]
                break
        kreport = out_dir / "kraken2" / f"{sample}.kreport"
        kout = out_dir / "kraken2" / f"{sample}.kraken2.out"
        commands.append(
            f"kraken2 --db {sh_quote(str(kraken2_db))} --threads {safe_threads} "
            f"--report {sh_quote(str(kreport))} --output {sh_quote(str(kout))} {sh_quote(fastq)}"
        )
        if command_exists("bracken"):
            commands.append(
                f"bracken -d {sh_quote(str(bracken_db))} -i {sh_quote(str(kreport))} "
                f"-o {sh_quote(str(out_dir / 'kraken2' / f'{sample}.bracken'))}"
            )
    (out_dir / "run_plan.sh").write_text("\n".join(commands) + "\n", encoding="utf-8")

    if errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
