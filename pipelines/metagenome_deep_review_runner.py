#!/usr/bin/env python3
"""Plan a compact deep-review metagenome re-analysis set.

This runner is intentionally conservative. By default it validates inputs and
writes an executable plan, but it does not download data or run heavy tools.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def command_status(command: str) -> dict[str, Any]:
    path = shutil.which(command)
    return {"command": command, "available": path is not None, "path": path or ""}


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan metagenome deep-review re-analysis")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = load_json(job_path)
    job_id = str(job.get("job_id", "unknown"))
    params: dict[str, Any] = job.get("params", {})

    shortlist_path = Path(str(params.get("shortlist_path", ""))).expanduser()
    selected_limit = int(params.get("selected_limit", 30))
    work_dir = Path(str(params.get("work_dir", out_dir / "work"))).expanduser()
    fastq_dir = work_dir / "fastq"
    qc_dir = out_dir / "qc"
    host_removed_dir = out_dir / "host_removed"
    kraken_dir = out_dir / "kraken2_confirm"
    host_index = str(params.get("host_index", "")).strip()
    kraken2_db = Path(str(params.get("kraken2_db", ""))).expanduser()
    bracken_db = Path(str(params.get("bracken_db", str(kraken2_db)))).expanduser()
    threads = int(params.get("threads", 4))
    execute_mode = str(params.get("execute_mode", "plan_only"))

    errors: list[str] = []
    warnings: list[str] = []
    if execute_mode != "plan_only":
        errors.append("Only execute_mode=plan_only is enabled for this guarded runner.")
    if not shortlist_path.exists():
        errors.append(f"shortlist_path not found: {shortlist_path}")
        rows: list[dict[str, str]] = []
    else:
        rows = read_tsv(shortlist_path)[:selected_limit]
    if not kraken2_db.exists():
        errors.append(f"kraken2_db not found: {kraken2_db}")
    if not bracken_db.exists():
        warnings.append(f"bracken_db not found or not checked: {bracken_db}")

    required = ["prefetch", "fasterq-dump", "kraken2", "bracken"]
    optional = ["fastp", "bowtie2", "samtools"]
    commands = [command_status(cmd) for cmd in required + optional]
    missing_required = [c["command"] for c in commands if c["command"] in required and not c["available"]]
    if missing_required:
        errors.append("Required commands missing: " + ", ".join(missing_required))
    missing_optional = [c["command"] for c in commands if c["command"] in optional and not c["available"]]
    if missing_optional:
        warnings.append("Optional QC/host-removal commands missing: " + ", ".join(missing_optional))
    if not host_index:
        warnings.append("host_index not configured; host-removal commands are written as commented placeholders.")

    validation = {
        "job_id": job_id,
        "checked_at": utc_now(),
        "pipeline": "metagenome_deep_review",
        "execute_mode": execute_mode,
        "selected_count": len(rows),
        "errors": errors,
        "warnings": warnings,
        "commands": commands,
    }
    (out_dir / "validation_report.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    plan_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"mkdir -p {shell_quote(str(fastq_dir))} {shell_quote(str(qc_dir))} {shell_quote(str(host_removed_dir))} {shell_quote(str(kraken_dir))}",
        "",
        "# This plan is generated for review. It is not executed by the guarded runner.",
        "",
    ]
    for row in rows:
        run = row.get("run", "").strip()
        if not run:
            continue
        fastq_gz = fastq_dir / f"{run}.fastq.gz"
        fastq = fastq_dir / f"{run}.fastq"
        qc_fastq = qc_dir / f"{run}.fastq.gz"
        host_removed_fastq = host_removed_dir / f"{run}.fastq.gz"
        input_for_kraken = host_removed_fastq if host_index else qc_fastq
        kreport = kraken_dir / f"{run}.kreport"
        kout = kraken_dir / f"{run}.kraken2.out"
        bracken_out = kraken_dir / f"{run}.bracken"
        plan_lines.extend(
            [
                f"# {run}: {row.get('top_pathogen', '')} ({row.get('pathogen_group', '')})",
                f"prefetch {shell_quote(run)} --output-directory {shell_quote(str(work_dir / 'sra'))}",
                f"fasterq-dump {shell_quote(str(work_dir / 'sra' / run / (run + '.sra')))} --outdir {shell_quote(str(fastq_dir))} --threads {threads}",
                f"gzip -f {shell_quote(str(fastq))}",
                f"fastp -i {shell_quote(str(fastq_gz))} -o {shell_quote(str(qc_fastq))} --thread {threads} --json {shell_quote(str(qc_dir / (run + '.fastp.json')))} --html {shell_quote(str(qc_dir / (run + '.fastp.html')))}",
            ]
        )
        if host_index:
            plan_lines.extend(
                [
                    f"bowtie2 -x {shell_quote(host_index)} -U {shell_quote(str(qc_fastq))} --threads {threads} --un-gz {shell_quote(str(host_removed_fastq))} -S /dev/null",
                ]
            )
        else:
            plan_lines.append(f"# host removal skipped until host_index is configured; using {shell_quote(str(qc_fastq))}")
        plan_lines.extend(
            [
                f"kraken2 --db {shell_quote(str(kraken2_db))} --threads {threads} --report {shell_quote(str(kreport))} --output {shell_quote(str(kout))} {shell_quote(str(input_for_kraken))}",
                f"bracken -d {shell_quote(str(bracken_db))} -i {shell_quote(str(kreport))} -o {shell_quote(str(bracken_out))}",
                "",
            ]
        )
    (out_dir / "run_plan.sh").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")
    (out_dir / "selected_runs.tsv").write_text(
        "\n".join(["run\tpathogen_group\ttop_pathogen\ttop_pathogen_fraction"] + [
            f"{r.get('run','')}\t{r.get('pathogen_group','')}\t{r.get('top_pathogen','')}\t{r.get('top_pathogen_fraction','')}"
            for r in rows
        ]) + "\n",
        encoding="utf-8",
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
