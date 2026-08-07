#!/usr/bin/env python3
"""QIIME2 amplicon pipeline wrapper.

This wrapper validates inputs and writes an executable shell plan. It does not
delete raw data or overwrite existing results. DADA2 truncation values must be
provided in the job JSON before denoising is emitted.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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


def require_file(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists() or not path.is_file():
        errors.append(f"{label} not found: {path}")


def run_checked(args: list[str], log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if log_path is not None:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "args": args,
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            }, ensure_ascii=False) + "\n")
    return result


def write_manifest_from_sra(params: dict[str, Any], out_dir: Path, errors: list[str]) -> Path | None:
    run_accessions = params.get("run_accessions", [])
    if not isinstance(run_accessions, list) or not run_accessions:
        errors.append("params.run_accessions must be a non-empty list when manifest is not provided")
        return None

    work_dir = Path(params.get("work_dir", out_dir / "work"))
    sra_dir = work_dir / "sra"
    fastq_dir = work_dir / "fastq"
    sra_dir.mkdir(parents=True, exist_ok=True)
    fastq_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "command_log.jsonl"
    threads = int(params.get("threads", max(1, (os.cpu_count() or 2) - 1)))
    run_to_sample = params.get("run_to_sample", {})
    if not isinstance(run_to_sample, dict):
        run_to_sample = {}

    manifest = out_dir / "manifest.csv"
    rows = ["sample-id,absolute-filepath,direction"]
    for run in [str(r).strip() for r in run_accessions if str(r).strip()]:
        sample_id = str(run_to_sample.get(run, run))
        sra_path = sra_dir / run / f"{run}.sra"
        if not sra_path.exists():
            result = run_checked(["prefetch", run, "--output-directory", str(sra_dir)], log_path)
            if result.returncode != 0:
                errors.append(f"prefetch failed for {run}: {result.stderr[-300:]}")
                continue

        forward = fastq_dir / f"{run}_1.fastq"
        reverse = fastq_dir / f"{run}_2.fastq"
        if not forward.exists() or not reverse.exists():
            source = sra_path if sra_path.exists() else sra_dir / f"{run}.sra"
            result = run_checked(
                ["fasterq-dump", str(source), "--split-files", "--outdir", str(fastq_dir), "--threads", str(threads)],
                log_path,
            )
            if result.returncode != 0:
                errors.append(f"fasterq-dump failed for {run}: {result.stderr[-300:]}")
                continue
        if not forward.exists() or not reverse.exists():
            errors.append(f"paired FASTQ files missing for {run}")
            continue
        rows.append(f"{sample_id},{forward.resolve()},forward")
        rows.append(f"{sample_id},{reverse.resolve()},reverse")

    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and plan QIIME2 amplicon analysis")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = load_job(job_path)
    params = job.get("params", {})

    execute_mode = params.get("execute_mode", "plan_only")
    manifest_value = params.get("manifest", "")
    manifest = Path(manifest_value) if manifest_value else Path()
    metadata = Path(params.get("metadata", ""))
    classifier_value = params.get("taxonomy_classifier", "")
    classifier = Path(classifier_value) if classifier_value else Path()
    read_type = params.get("read_type", "paired")
    threads = int(params.get("threads", max(1, (os.cpu_count() or 2) - 1)))
    trunc_len_f = params.get("trunc_len_f")
    trunc_len_r = params.get("trunc_len_r")

    errors: list[str] = []
    if not manifest_value and params.get("run_accessions"):
        for command in ["prefetch", "fasterq-dump"]:
            if shutil.which(command) is None:
                errors.append(f"{command} command not found in PATH or active environment")
        if not errors and execute_mode in {"sra_demux", "demux_only"}:
            generated_manifest = write_manifest_from_sra(params, out_dir, errors)
            if generated_manifest is not None:
                manifest = generated_manifest
        else:
            manifest = out_dir / "manifest.csv"
    require_file(manifest, "manifest", errors)
    require_file(metadata, "metadata", errors)
    if read_type not in {"paired", "single"}:
        errors.append("read_type must be paired or single")
    if not command_exists("qiime"):
        errors.append("qiime command not found in PATH or active environment")
    if trunc_len_f is not None and trunc_len_r is not None and classifier_value:
        require_file(classifier, "taxonomy_classifier", errors)

    decision_log = out_dir / "decision_request.md"
    if read_type == "paired" and (trunc_len_f is None or trunc_len_r is None):
        decision_log.write_text(
            "# Decision Required\n\n"
            "DADA2 paired-end truncation lengths are missing.\n\n"
            "Run demux summarize first, inspect quality plots, then set `trunc_len_f` and `trunc_len_r` in the job JSON.\n",
            encoding="utf-8",
        )

    report = {
        "job_id": job.get("job_id"),
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline": "amplicon_qiime2",
        "errors": errors,
        "warnings": ["DADA2 denoising is omitted until truncation parameters are provided"] if decision_log.exists() else [],
    }
    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"mkdir -p {sh_quote(str(out_dir / 'qiime2'))}",
        f"qiime tools import --type 'SampleData[PairedEndSequencesWithQuality]' --input-path {sh_quote(str(manifest))} --output-path {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --input-format PairedEndFastqManifestPhred33V2"
        if read_type == "paired"
        else f"qiime tools import --type 'SampleData[SequencesWithQuality]' --input-path {sh_quote(str(manifest))} --output-path {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --input-format SingleEndFastqManifestPhred33V2",
        f"qiime demux summarize --i-data {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'demux.qzv'))}",
    ]
    if read_type == "paired" and trunc_len_f is not None and trunc_len_r is not None:
        commands.append(
            "qiime dada2 denoise-paired "
            f"--i-demultiplexed-seqs {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} "
            f"--p-trunc-len-f {int(trunc_len_f)} --p-trunc-len-r {int(trunc_len_r)} "
            f"--p-n-threads {threads} "
            f"--o-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} "
            f"--o-representative-sequences {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qza'))} "
            f"--o-denoising-stats {sh_quote(str(out_dir / 'qiime2' / 'denoising-stats.qza'))}"
        )
        commands.append(
            "qiime feature-classifier classify-sklearn "
            f"--i-classifier {sh_quote(str(classifier))} "
            f"--i-reads {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qza'))} "
            f"--o-classification {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))}"
        )
    (out_dir / "run_plan.sh").write_text("\n".join(commands) + "\n", encoding="utf-8")

    if errors:
        return 2
    if execute_mode in {"demux_only", "sra_demux"}:
        log_path = out_dir / "command_log.jsonl"
        for raw in commands[2:5]:
            result = run_checked(["bash", "-lc", raw], log_path)
            if result.returncode != 0:
                errors.append(f"command failed: {raw}")
                report["errors"] = errors
                (out_dir / "validation_report.json").write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
