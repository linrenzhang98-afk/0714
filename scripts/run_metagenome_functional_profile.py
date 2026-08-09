#!/usr/bin/env python3
"""Run/resume a HUMAnN-style functional profiling stage for host-removed reads.

This worker is intended to be launched by the unattended status publisher. It
is resumable: each sample is skipped once HUMAnN output files are present.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_log(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{utc_now()}\t{message}\n")


def copy_log_tail(src: Path, dst: Path, max_lines: int = 200) -> None:
    if not src.exists():
        return
    try:
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    dst.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")


def run_command(
    args: list[str],
    log_path: Path,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    append_log(log_path, "RUN " + " ".join(args))
    result = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
    )
    with log_path.open("a", encoding="utf-8") as f:
        if result.stdout:
            f.write(result.stdout[-8000:])
            if not result.stdout.endswith("\n"):
                f.write("\n")
        if result.stderr:
            f.write(result.stderr[-8000:])
            if not result.stderr.endswith("\n"):
                f.write("\n")
        f.write(f"{utc_now()}\tRETURN_CODE {result.returncode}\n")
    return result


def command_path(command: str) -> str:
    return shutil.which(command) or ""


def file_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def sample_complete(sample_dir: Path, run: str) -> bool:
    return (
        file_nonempty(sample_dir / f"{run}_genefamilies.tsv")
        and file_nonempty(sample_dir / f"{run}_pathabundance.tsv")
    )


def write_public_status(
    public_dir: Path,
    result_dir: Path,
    state: str,
    reason: str,
    rows: list[dict[str, Any]],
    tool_status: dict[str, str],
    db_status: dict[str, Any],
) -> None:
    done = sum(1 for row in rows if row.get("status") == "done")
    failed = sum(1 for row in rows if row.get("status") == "failed")
    running = sum(1 for row in rows if row.get("status") == "running")
    skipped = sum(1 for row in rows if str(row.get("status", "")).startswith("skipped"))
    public_dir.mkdir(parents=True, exist_ok=True)
    copy_log_tail(result_dir / "logs" / "functional_profile.log", public_dir / "functional_profile_log_tail.txt")
    summary = {
        "generated_at": utc_now(),
        "state": state,
        "reason": reason,
        "result_dir": str(result_dir),
        "sample_count": len(rows),
        "done_count": done,
        "failed_count": failed,
        "running_count": running,
        "skipped_count": skipped,
        "tool_status": tool_status,
        "db_status": db_status,
    }
    write_json(public_dir / "summary.json", summary)
    write_tsv(
        public_dir / "run_status.tsv",
        rows,
        [
            "run",
            "pathogen_group",
            "status",
            "error",
            "host_removed_fastq",
            "sample_dir",
            "genefamilies",
            "pathabundance",
            "pathcoverage",
        ],
    )
    lines = [
        "# PRJNA1056765 Functional Shotgun Profile",
        "",
        f"Generated at: {summary['generated_at']}",
        f"State: `{state}`",
        "",
        "## Reason",
        "",
        f"- {reason}",
        "",
        "## Completion",
        "",
        f"- Samples considered: {len(rows)}",
        f"- Done: {done}",
        f"- Running: {running}",
        f"- Failed: {failed}",
        f"- Skipped: {skipped}",
        "",
        "## Tools",
        "",
    ]
    for name, value in tool_status.items():
        lines.append(f"- {name}: `{value or 'missing'}`")
    lines.extend(
        [
            "",
            "## Databases",
            "",
            f"- ChocoPhlAn ready: {db_status.get('chocophlan_ready', False)}",
            f"- UniRef ready: {db_status.get('uniref_ready', False)}",
            f"- Utility mapping ready: {db_status.get('utility_mapping_ready', False)}",
            f"- Database root: `{db_status.get('db_root', '')}`",
            "",
            "## Output Files",
            "",
            "- `run_status.tsv`",
            "- `summary.json`",
            "- `merged_genefamilies.tsv` if HUMAnN join succeeds",
            "- `merged_pathabundance.tsv` if HUMAnN join succeeds",
            "- `merged_pathabundance_relab.tsv` if HUMAnN renormalization succeeds",
            "",
            "## Guardrails",
            "",
            "- This stage uses existing host-removed FASTQ files from the deep-review set.",
            "- Functional profiling is exploratory until sample metadata and clinical grouping are strengthened.",
        ]
    )
    (public_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def has_db_files(path: Path, suffixes: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    for suffix in suffixes:
        if any(path.rglob(f"*{suffix}")):
            return True
    return False


def install_humann_if_needed(log_path: Path, conda_env: str, timeout: int) -> None:
    if command_path("humann") and command_path("humann_databases"):
        return
    installer = command_path("mamba") or command_path("conda")
    if not installer:
        raise RuntimeError("HUMAnN missing and neither mamba nor conda is available for installation")
    result = run_command(
        [
            installer,
            "install",
            "-n",
            conda_env,
            "-y",
            "-c",
            "bioconda",
            "-c",
            "conda-forge",
            "humann",
            "metaphlan",
        ],
        log_path,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HUMAnN/MetaPhlAn installation failed rc={result.returncode}")


def download_humann_dbs(db_root: Path, log_path: Path, timeout: int) -> None:
    db_root.mkdir(parents=True, exist_ok=True)
    humann_databases = command_path("humann_databases")
    if not humann_databases:
        raise RuntimeError("humann_databases command is not available")

    chocophlan = db_root / "chocophlan"
    uniref = db_root / "uniref"
    if not has_db_files(chocophlan, (".ffn.gz", ".ffn")):
        result = run_download_with_retries(
            [humann_databases, "--download", "chocophlan", "full", str(db_root), "--update-config", "yes"],
            log_path,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ChocoPhlAn download failed rc={result.returncode}; see functional_profile_log_tail.txt")
    if not has_db_files(uniref, (".dmnd", ".faa.gz", ".faa")):
        result = run_download_with_retries(
            [humann_databases, "--download", "uniref", "uniref90_diamond", str(db_root), "--update-config", "yes"],
            log_path,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"UniRef90 download failed rc={result.returncode}; see functional_profile_log_tail.txt")
    utility_mapping = db_root / "utility_mapping"
    if not utility_mapping.exists() or not any(utility_mapping.iterdir()):
        result = run_download_with_retries(
            [humann_databases, "--download", "utility_mapping", "full", str(db_root), "--update-config", "yes"],
            log_path,
            timeout=timeout,
        )
        if result.returncode != 0:
            append_log(log_path, f"utility_mapping_download_failed_nonfatal rc={result.returncode}")


def run_download_with_retries(args: list[str], log_path: Path, timeout: int, attempts: int = 3) -> subprocess.CompletedProcess[str]:
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        append_log(log_path, f"download_attempt={attempt}/{attempts}")
        last = run_command(args, log_path, timeout=timeout)
        if last.returncode == 0:
            return last
        if attempt < attempts:
            time.sleep(30)
    if last is None:
        raise RuntimeError("download retry loop did not run")
    return last


def db_status(db_root: Path) -> dict[str, Any]:
    chocophlan = db_root / "chocophlan"
    uniref = db_root / "uniref"
    return {
        "db_root": str(db_root),
        "chocophlan_ready": has_db_files(chocophlan, (".ffn.gz", ".ffn")),
        "uniref_ready": has_db_files(uniref, (".dmnd", ".faa.gz", ".faa")),
        "utility_mapping_ready": (db_root / "utility_mapping").exists() and any((db_root / "utility_mapping").iterdir()),
        "chocophlan": str(chocophlan),
        "uniref": str(uniref),
    }


def collect_rows(run_status: Path, max_samples: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_tsv(run_status):
        if row.get("status") != "done":
            continue
        fastq = row.get("host_removed_fastq", "").strip()
        run = row.get("run", "").strip()
        if not run:
            continue
        rows.append(
            {
                "run": run,
                "pathogen_group": row.get("pathogen_group", ""),
                "status": "queued",
                "error": "",
                "host_removed_fastq": fastq,
                "sample_dir": "",
                "genefamilies": "",
                "pathabundance": "",
                "pathcoverage": "",
            }
        )
        if max_samples and len(rows) >= max_samples:
            break
    return rows


def join_outputs(result_dir: Path, public_dir: Path, log_path: Path, timeout: int) -> None:
    join = command_path("humann_join_tables")
    renorm = command_path("humann_renorm_table")
    if not join:
        return
    for suffix, output_name in [
        ("genefamilies", "merged_genefamilies.tsv"),
        ("pathabundance", "merged_pathabundance.tsv"),
        ("pathcoverage", "merged_pathcoverage.tsv"),
    ]:
        result = run_command(
            [join, "--input", str(result_dir), "--file_name", suffix, "--output", str(public_dir / output_name)],
            log_path,
            timeout=timeout,
        )
        if result.returncode != 0:
            append_log(log_path, f"join_tables_{suffix}_failed rc={result.returncode}")
    merged_pathabundance = public_dir / "merged_pathabundance.tsv"
    if renorm and file_nonempty(merged_pathabundance):
        result = run_command(
            [
                renorm,
                "--input",
                str(merged_pathabundance),
                "--output",
                str(public_dir / "merged_pathabundance_relab.tsv"),
                "--units",
                "relab",
            ],
            log_path,
            timeout=timeout,
        )
        if result.returncode != 0:
            append_log(log_path, f"renorm_pathabundance_failed rc={result.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/resume PRJNA1056765 functional shotgun profiling")
    parser.add_argument("--run-status", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--public-dir", required=True)
    parser.add_argument("--db-root", default="/mnt/disk1/db/humann")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--max-samples", type=int, default=30)
    parser.add_argument("--per-command-timeout-seconds", type=int, default=86400)
    parser.add_argument("--install-timeout-seconds", type=int, default=21600)
    parser.add_argument("--db-timeout-seconds", type=int, default=172800)
    parser.add_argument("--conda-env", default="mgshotgun")
    parser.add_argument("--auto-install", action="store_true")
    parser.add_argument("--auto-download-dbs", action="store_true")
    args = parser.parse_args()

    result_dir = Path(args.out_dir)
    public_dir = Path(args.public_dir)
    db_root = Path(args.db_root)
    logs_dir = result_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "functional_profile.log"

    rows = collect_rows(Path(args.run_status), args.max_samples)
    tool_status = {
        "humann": command_path("humann"),
        "humann_databases": command_path("humann_databases"),
        "humann_join_tables": command_path("humann_join_tables"),
        "humann_renorm_table": command_path("humann_renorm_table"),
        "metaphlan": command_path("metaphlan"),
        "diamond": command_path("diamond"),
    }
    write_public_status(public_dir, result_dir, "initializing", "Functional profiling worker started.", rows, tool_status, db_status(db_root))

    try:
        if args.auto_install:
            install_humann_if_needed(log_path, args.conda_env, args.install_timeout_seconds)
        tool_status = {
            "humann": command_path("humann"),
            "humann_databases": command_path("humann_databases"),
            "humann_join_tables": command_path("humann_join_tables"),
            "humann_renorm_table": command_path("humann_renorm_table"),
            "metaphlan": command_path("metaphlan"),
            "diamond": command_path("diamond"),
        }
        if not tool_status["humann"]:
            raise RuntimeError("HUMAnN is unavailable after tool check/install stage")
        if args.auto_download_dbs:
            download_humann_dbs(db_root, log_path, args.db_timeout_seconds)
        current_db_status = db_status(db_root)
        if not current_db_status["chocophlan_ready"] or not current_db_status["uniref_ready"]:
            raise RuntimeError("HUMAnN databases are not ready after database check/download stage")
    except Exception as exc:  # noqa: BLE001 - report blocker for unattended repair.
        write_public_status(public_dir, result_dir, "blocked_setup", str(exc), rows, tool_status, db_status(db_root))
        return 2

    humann = tool_status["humann"]
    current_db_status = db_status(db_root)
    for row in rows:
        run = str(row["run"])
        fastq = Path(str(row["host_removed_fastq"]))
        sample_dir = result_dir / run
        row["sample_dir"] = str(sample_dir)
        row["genefamilies"] = str(sample_dir / f"{run}_genefamilies.tsv")
        row["pathabundance"] = str(sample_dir / f"{run}_pathabundance.tsv")
        row["pathcoverage"] = str(sample_dir / f"{run}_pathcoverage.tsv")
        if sample_complete(sample_dir, run):
            row["status"] = "done"
            continue
        if not file_nonempty(fastq):
            row["status"] = "failed"
            row["error"] = f"host_removed_fastq missing or empty: {fastq}"
            write_public_status(public_dir, result_dir, "running", "At least one sample failed; continuing.", rows, tool_status, current_db_status)
            continue
        row["status"] = "running"
        write_public_status(public_dir, result_dir, "running", f"Running HUMAnN for {run}.", rows, tool_status, current_db_status)
        sample_dir.mkdir(parents=True, exist_ok=True)
        result = run_command(
            [
                humann,
                "--input",
                str(fastq),
                "--output",
                str(sample_dir),
                "--threads",
                str(args.threads),
                "--nucleotide-database",
                str(Path(current_db_status["chocophlan"])),
                "--protein-database",
                str(Path(current_db_status["uniref"])),
            ],
            log_path,
            timeout=args.per_command_timeout_seconds,
        )
        if result.returncode == 0 and sample_complete(sample_dir, run):
            row["status"] = "done"
            row["error"] = ""
        else:
            row["status"] = "failed"
            row["error"] = f"HUMAnN failed or incomplete rc={result.returncode}"
        write_public_status(public_dir, result_dir, "running", f"Finished attempt for {run}.", rows, tool_status, current_db_status)
        time.sleep(1)

    join_outputs(result_dir, public_dir, log_path, args.per_command_timeout_seconds)
    failed = [row for row in rows if row.get("status") == "failed"]
    state = "done_with_failures" if failed else "done"
    reason = f"Functional profiling finished with {len(failed)} failed sample(s)." if failed else "Functional profiling finished for all selected samples."
    write_public_status(public_dir, result_dir, state, reason, rows, tool_status, current_db_status)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
