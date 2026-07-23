#!/usr/bin/env python3
"""Travel-mode SRA-to-Kraken2/Bracken runner with per-run failure handling."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_job(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_decision(out_dir: Path, job_id: str, title: str, body: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "decision_request.md").write_text(
        f"# {title}\n\nJob: `{job_id}`\n\nGenerated: {utc_now()}\n\n{body}\n",
        encoding="utf-8",
    )


def run_command(args: list[str], cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def retry(args: list[str], attempts: int, sleep_seconds: int, log_path: Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        start = time.time()
        result = run_command(args, cwd=cwd)
        elapsed = round(time.time() - start, 3)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": utc_now(),
                "attempt": attempt,
                "args": args,
                "returncode": result.returncode,
                "elapsed_seconds": elapsed,
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            }, ensure_ascii=False) + "\n")
        last = result
        if result.returncode == 0:
            return result
        if attempt < attempts and sleep_seconds:
            time.sleep(sleep_seconds)
    assert last is not None
    return last


def disk_free_gb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024 ** 3)


def gzip_fastq(path: Path) -> Path:
    gz_path = path.with_suffix(path.suffix + ".gz")
    if gz_path.exists():
        return gz_path
    with path.open("rb") as src, gzip.open(gz_path, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)
    path.unlink()
    return gz_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SRA download plus Kraken2/Bracken travel batch")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = load_job(job_path)
    job_id = str(job.get("job_id", "unknown"))
    params: dict[str, Any] = job.get("params", {})
    run_accessions = params.get("run_accessions", [])
    if not isinstance(run_accessions, list):
        run_accessions = []
    run_accessions = [str(r).strip() for r in run_accessions if str(r).strip()]

    work_dir = Path(params.get("work_dir", out_dir / "work"))
    sra_dir = work_dir / "sra"
    fastq_dir = work_dir / "fastq"
    kraken_dir = out_dir / "kraken2"
    decision_dir = Path("decision_requests")
    for path in [work_dir, sra_dir, fastq_dir, kraken_dir]:
        path.mkdir(parents=True, exist_ok=True)

    log_path = out_dir / "command_log.jsonl"
    status_tsv = out_dir / "run_status.tsv"
    threads = int(params.get("threads", 4))
    db = Path(params.get("kraken2_db", ""))
    bracken_db = Path(params.get("bracken_db", str(db)))
    max_failed_fraction = float(params.get("max_failed_fraction", 0.2))
    max_failed_runs = int(params.get("max_failed_runs", 10))
    disk_free_min = float(params.get("disk_free_gb_min", 500))

    errors: list[str] = []
    for command in ["prefetch", "fasterq-dump", "kraken2"]:
        if shutil.which(command) is None:
            errors.append(f"Required command not found: {command}")
    bracken_available = shutil.which("bracken") is not None
    if not bracken_available:
        errors.append("Optional command not found: bracken; Kraken2 can still be used, but this job is configured to record Bracken as failed.")
    if not run_accessions:
        errors.append("No run_accessions provided.")
    if not db.exists():
        errors.append(f"Kraken2 database not found: {db}")
    if disk_free_gb(work_dir) < disk_free_min:
        errors.append(f"Disk free space is below threshold {disk_free_min} GB at {work_dir}")

    if errors:
        body = "\n".join(f"- {e}" for e in errors)
        write_decision(decision_dir, job_id, "Metagenome Travel Job Blocked", body)
        (out_dir / "validation_report.json").write_text(json.dumps({"job_id": job_id, "errors": errors}, indent=2) + "\n", encoding="utf-8")
        return 2

    statuses: list[dict[str, Any]] = []

    for run in run_accessions:
        row: dict[str, Any] = {"run": run, "status": "started", "error": ""}
        statuses.append(row)
        try:
            sra_path = sra_dir / run / f"{run}.sra"
            if not sra_path.exists():
                result = retry(["prefetch", run, "--output-directory", str(sra_dir)], 3, 120, log_path)
                if result.returncode != 0:
                    row.update(status="download_failed", error=result.stderr[-500:])
                    continue

            fastq_gz = fastq_dir / f"{run}.fastq.gz"
            if not fastq_gz.exists():
                result = retry(["fasterq-dump", str(sra_path), "--outdir", str(fastq_dir), "--threads", str(threads)], 2, 60, log_path)
                if result.returncode != 0:
                    row.update(status="fastq_failed", error=result.stderr[-500:])
                    continue
                fastq = fastq_dir / f"{run}.fastq"
                if not fastq.exists():
                    row.update(status="fastq_missing", error=f"Expected FASTQ missing: {fastq}")
                    continue
                fastq_gz = gzip_fastq(fastq)

            kreport = kraken_dir / f"{run}.kreport"
            kout = kraken_dir / f"{run}.kraken2.out"
            if not kreport.exists():
                result = retry(
                    ["kraken2", "--db", str(db), "--threads", str(threads), "--report", str(kreport), "--output", str(kout), str(fastq_gz)],
                    2,
                    60,
                    log_path,
                )
                if result.returncode != 0:
                    row.update(status="kraken2_failed", error=result.stderr[-500:])
                    continue

            bracken_out = kraken_dir / f"{run}.bracken"
            if bracken_available and not bracken_out.exists():
                result = retry(["bracken", "-d", str(bracken_db), "-i", str(kreport), "-o", str(bracken_out)], 1, 0, log_path)
                if result.returncode != 0:
                    row.update(status="kraken2_done_bracken_failed", error=result.stderr[-500:])
                    continue

            row.update(status="done", error="")
        except Exception as exc:  # noqa: BLE001
            row.update(status="unexpected_failed", error=str(exc))

    failed = [r for r in statuses if r["status"] not in {"done"}]
    failed_fraction = len(failed) / len(statuses) if statuses else 1.0
    final_status = "done"
    if len(failed) > max_failed_runs or failed_fraction > max_failed_fraction:
        final_status = "blocked"
        body = (
            f"Failed runs: {len(failed)} / {len(statuses)} ({failed_fraction:.1%}).\n\n"
            f"Thresholds: max_failed_runs={max_failed_runs}, max_failed_fraction={max_failed_fraction}.\n\n"
            "The job stopped for review. See `run_status.tsv` and `command_log.jsonl` in the result directory."
        )
        write_decision(decision_dir, job_id, "Metagenome Batch Failure Threshold Exceeded", body)

    with status_tsv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "status", "error"], delimiter="\t")
        writer.writeheader()
        writer.writerows(statuses)

    report = {
        "job_id": job_id,
        "checked_at": utc_now(),
        "pipeline": "metagenome_sra_kraken2",
        "run_count": len(statuses),
        "done_count": sum(1 for r in statuses if r["status"] == "done"),
        "failed_count": len(failed),
        "failed_fraction": failed_fraction,
        "final_status": final_status,
        "result_dir": str(out_dir),
    }
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if final_status == "done" else 2


if __name__ == "__main__":
    raise SystemExit(main())
