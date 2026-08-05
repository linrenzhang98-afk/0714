#!/usr/bin/env python3
"""Prepare host-removal and AMR database resources for the next stage.

This script is idempotent and conservative:
- It never deletes existing databases.
- It writes progress logs and public status.
- It downloads/builds only when the expected target is missing.
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


HOST_INDEX_URL = "https://genome-idx.s3.amazonaws.com/bt/GRCh38_noalt_as.zip"
HOST_INDEX_NAME = "GRCh38_noalt_as"
AMRFINDER_CANDIDATE_PATHS = [
    "/home/suma/anaconda3/envs/mgshotgun/bin/amrfinder",
    "/home/suma/anaconda3/envs/clinical_meta/bin/amrfinder",
    "/home/suma/anaconda3/envs/metag_env/bin/amrfinder",
    "/home/suma/anaconda3/bin/amrfinder",
    "/usr/local/bin/amrfinder",
    "/usr/bin/amrfinder",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(args: list[str], log_path: Path, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": utc_now(),
            "args": args,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }, ensure_ascii=False) + "\n")
    return result


def find_command(name: str, candidates: list[str] | None = None) -> str | None:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    for candidate in candidates or []:
        path = Path(candidate)
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    return None


def bowtie2_index_ready(prefix: Path) -> bool:
    bt2 = [prefix.with_suffix(prefix.suffix + f".{suffix}.bt2") for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    bt2l = [prefix.with_suffix(prefix.suffix + f".{suffix}.bt2l") for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    return all(path.exists() for path in bt2) or all(path.exists() for path in bt2l)


def zip_archive_ready(zip_path: Path, log_path: Path) -> bool:
    if not zip_path.exists():
        return False
    unzip = shutil.which("unzip")
    if unzip is None:
        return True
    result = run([unzip, "-t", str(zip_path)], log_path, timeout=None)
    return result.returncode == 0


def download_host_index(zip_path: Path, log_path: Path) -> subprocess.CompletedProcess[str]:
    tmp_path = zip_path.with_suffix(zip_path.suffix + ".download")
    downloader = shutil.which("curl")
    if downloader:
        return run([
            downloader,
            "-L",
            "--fail",
            "--retry",
            "3",
            "--continue-at",
            "-",
            "-o",
            str(tmp_path),
            HOST_INDEX_URL,
        ], log_path, timeout=None)
    downloader = shutil.which("wget")
    if downloader:
        return run([downloader, "-c", "-O", str(tmp_path), HOST_INDEX_URL], log_path, timeout=None)
    return subprocess.CompletedProcess([], 127, "", "curl/wget not found")


def amrfinder_db_ready(log_path: Path) -> tuple[bool, str]:
    amrfinder = find_command("amrfinder", AMRFINDER_CANDIDATE_PATHS)
    if amrfinder is None:
        return False, "amrfinder command not found"
    result = run([amrfinder, "-V"], log_path)
    text = result.stdout + "\n" + result.stderr
    ready = result.returncode == 0 and "database" in text.lower()
    return ready, text.strip()[-1000:]


def ensure_amrfinder_command(log_path: Path) -> str | None:
    amrfinder = find_command("amrfinder", AMRFINDER_CANDIDATE_PATHS)
    if amrfinder:
        return amrfinder
    conda = find_command("conda", ["/home/suma/anaconda3/bin/conda"])
    if conda is None:
        return None
    result = run([
        conda,
        "install",
        "-y",
        "-n",
        "mgshotgun",
        "-c",
        "bioconda",
        "-c",
        "conda-forge",
        "ncbi-amrfinderplus",
    ], log_path, timeout=None)
    if result.returncode != 0:
        return None
    return find_command("amrfinder", AMRFINDER_CANDIDATE_PATHS)


def write_status(out_dir: Path, summary: dict[str, Any]) -> None:
    (out_dir / "setup_status.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Metagenome Next-Stage Database Setup",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "## Status",
        "",
        f"- Setup state: {summary.get('setup_state', 'unknown')}",
        f"- Host index ready: {summary['host_index_ready']}",
        f"- Host index prefix: `{summary['host_index_prefix']}`",
        f"- AMRFinderPlus DB ready: {summary['amrfinder_db_ready']}",
        "",
        "## Actions",
        "",
    ]
    actions = summary.get("actions", [])
    warnings = summary.get("warnings", [])
    errors = summary.get("errors", [])
    lines.extend(f"- {item}" for item in actions) if actions else lines.append("- None.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None.")
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {item}" for item in errors) if errors else lines.append("- None.")
    lines.extend(["", "## Output Files", "", "- `setup_status.json`", "- `env_recommendations.sh`", "- `setup_log.jsonl`"])
    (out_dir / "setup_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up metagenome next-stage DB resources")
    parser.add_argument("--host-index-root", default="/mnt/disk1/db/host_indexes")
    parser.add_argument("--amr-root", default="/mnt/disk1/db/amr")
    parser.add_argument("--out-dir", default="reports_public/metagenome_next_stage_setup")
    parser.add_argument("--log", default="reports_public/metagenome_next_stage_setup/setup_log.jsonl")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log)
    host_root = Path(args.host_index_root)
    host_dir = host_root / HOST_INDEX_NAME
    host_prefix = host_dir / HOST_INDEX_NAME
    amr_root = Path(args.amr_root)
    host_root.mkdir(parents=True, exist_ok=True)
    amr_root.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []
    env_lines = [
        f"export HOST_INDEX_PREFIX={host_prefix}",
        "# AMRFinderPlus uses its installed/default database after `amrfinder -u`.",
        "# AMR_DB_DIR is not required when AMRFinderPlus reports a valid database via `amrfinder -V`.",
    ]
    (out_dir / "env_recommendations.sh").write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    write_status(out_dir, {
        "generated_at": utc_now(),
        "setup_state": "running",
        "host_index_url": HOST_INDEX_URL,
        "host_index_prefix": str(host_prefix),
        "host_index_ready": bowtie2_index_ready(host_prefix),
        "amrfinder_db_ready": False,
        "amrfinder_version_before": "",
        "amrfinder_version_after": "",
        "actions": ["Database setup started."],
        "warnings": [],
        "errors": [],
    })

    host_ready_before = bowtie2_index_ready(host_prefix)
    if host_ready_before:
        actions.append(f"Host index already present: {host_prefix}")
    else:
        zip_path = host_root / f"{HOST_INDEX_NAME}.zip"
        if not zip_archive_ready(zip_path, log_path):
            result = download_host_index(zip_path, log_path)
            if result.returncode != 0:
                errors.append("Failed to download GRCh38 Bowtie2 index.")
            else:
                tmp_path = zip_path.with_suffix(zip_path.suffix + ".download")
                if zip_archive_ready(tmp_path, log_path):
                    os.replace(tmp_path, zip_path)
                    actions.append(f"Downloaded valid host index archive: {zip_path}")
                else:
                    errors.append("Downloaded GRCh38 Bowtie2 index archive failed zip validation.")
        else:
            actions.append(f"Host index archive is valid: {zip_path}")
        if zip_path.exists() and not bowtie2_index_ready(host_prefix):
            host_dir.mkdir(parents=True, exist_ok=True)
            unzip = shutil.which("unzip")
            if unzip is None:
                errors.append("unzip command not found for host index archive.")
            else:
                result = run(["unzip", "-n", str(zip_path), "-d", str(host_dir)], log_path, timeout=None)
                if result.returncode != 0:
                    errors.append("Failed to unzip GRCh38 Bowtie2 index.")
        if bowtie2_index_ready(host_prefix):
            actions.append(f"Host index ready: {host_prefix}")
        else:
            warnings.append(f"Host index not ready yet: {host_prefix}")

    amr_ready_before, amr_version_before = amrfinder_db_ready(log_path)
    if amr_ready_before:
        actions.append("AMRFinderPlus database already available.")
    else:
        amrfinder = ensure_amrfinder_command(log_path)
        if amrfinder is None:
            errors.append("amrfinder command not found and automatic ncbi-amrfinderplus install failed.")
        else:
            actions.append(f"AMRFinderPlus command available: {amrfinder}")
            result = run([amrfinder, "-u"], log_path, timeout=None)
            if result.returncode != 0:
                errors.append("AMRFinderPlus database update failed.")
    amr_ready_after, amr_version_after = amrfinder_db_ready(log_path)
    if amr_ready_after:
        actions.append("AMRFinderPlus database ready after update/check.")
    else:
        warnings.append("AMRFinderPlus database still not ready after update/check.")

    summary: dict[str, Any] = {
        "generated_at": utc_now(),
        "setup_state": "done" if not errors else "error",
        "host_index_url": HOST_INDEX_URL,
        "host_index_prefix": str(host_prefix),
        "host_index_ready": bowtie2_index_ready(host_prefix),
        "amrfinder_db_ready": amr_ready_after,
        "amrfinder_version_before": amr_version_before,
        "amrfinder_version_after": amr_version_after,
        "actions": actions,
        "warnings": warnings,
        "errors": errors,
    }
    write_status(out_dir, summary)
    print(out_dir)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
