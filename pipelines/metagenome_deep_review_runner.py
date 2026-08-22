#!/usr/bin/env python3
"""Plan a compact deep-review metagenome re-analysis set.

This runner is intentionally conservative. By default it validates inputs and
writes an executable plan, but it does not download data or run heavy tools.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import getpass
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import resource
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fastq_gz_to_fasta_subset(fastq_gz: Path, fasta: Path, max_reads: int) -> int:
    count = 0
    fasta.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(fastq_gz, "rt", encoding="utf-8", errors="replace") as src, fasta.open("w", encoding="utf-8") as dst:
        while count < max_reads:
            header = src.readline()
            if not header:
                break
            seq = src.readline().strip()
            src.readline()
            src.readline()
            if not seq:
                continue
            count += 1
            dst.write(f">{header[1:].strip() or 'read_' + str(count)}\n{seq}\n")
    return count


def file_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def sha256_small_file(path: Path, limit: int = 64 * 1024 * 1024) -> str:
    if not path.is_file() or path.stat().st_size > limit:
        return "NOT_HASHED_SIZE_LIMIT"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_version(executable: str, flags: list[str]) -> dict[str, Any]:
    path = shutil.which(executable)
    if not path:
        return {"path": "", "version": "UNAVAILABLE", "returncode": 127}
    result = run_command([path, *flags], timeout=30)
    text = (result.stdout + "\n" + result.stderr).strip()
    return {"path": path, "version": text[:2000], "returncode": result.returncode}


def readonly_inventory(out_dir: Path, project_path: Path, kraken2_db: Path, bracken_db: Path) -> int:
    """Record a bounded, read-only workstation inventory."""
    kraken = command_version("kraken2", ["--version"])
    bracken = command_version("bracken", ["-v"])
    database_files = []
    if kraken2_db.is_dir():
        for path in sorted(kraken2_db.iterdir()):
            if not path.is_file():
                continue
            stat = path.stat()
            database_files.append({
                "name": path.name,
                "size_bytes": stat.st_size,
                "mtime_epoch": int(stat.st_mtime),
                "sha256_if_small": sha256_small_file(path),
            })
    redistributions = []
    if bracken_db.is_dir():
        for path in sorted(bracken_db.glob("database*mers.kmer_distrib")):
            match = __import__("re").match(r"database(\d+)mers\.kmer_distrib$", path.name)
            redistributions.append({
                "file": path.name,
                "read_length_nt": int(match.group(1)) if match else None,
                "size_bytes": path.stat().st_size,
                "mtime_epoch": int(path.stat().st_mtime),
            })
    disk = {}
    for label, path in {"project": project_path, "kraken2_db": kraken2_db, "bracken_db": bracken_db}.items():
        try:
            usage = shutil.disk_usage(path)
            disk[label] = {"path": str(path), "total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}
        except OSError as exc:
            disk[label] = {"path": str(path), "error": str(exc)}
    meminfo = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, value = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                meminfo[key] = value.strip()
    except OSError as exc:
        meminfo["error"] = str(exc)
    cpu_model = "UNAVAILABLE"
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    manifest_identity = hashlib.sha256(json.dumps(database_files, sort_keys=True).encode("utf-8")).hexdigest()
    payload = {
        "inventory_type": "READ_ONLY_HOSPITAL_RUNNER",
        "generated_at": utc_now(),
        "hostname": socket.gethostname(),
        "whoami": getpass.getuser(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "project_path": str(project_path),
        "project_path_exists": project_path.is_dir(),
        "project_parent_writable": os.access(project_path, os.W_OK),
        "logical_threads": os.cpu_count(),
        "cpu_model": cpu_model,
        "load_average": list(os.getloadavg()),
        "memory": meminfo,
        "disk": disk,
        "kraken2": kraken,
        "bracken": bracken,
        "kraken2_db": str(kraken2_db),
        "bracken_db": str(bracken_db),
        "database_manifest_identity_sha256": manifest_identity,
        "database_files": database_files,
        "bracken_redistributions": redistributions,
        "has_40nt_redistribution": any(row["read_length_nt"] == 40 for row in redistributions),
    }
    write_json(out_dir / "hospital_readonly_inventory.json", payload)
    fields = ["file", "read_length_nt", "size_bytes", "mtime_epoch"]
    with (out_dir / "bracken_redistributions.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(redistributions)
    return 0


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def inspect_fastq_gz(path: Path) -> dict[str, Any]:
    read_count = 0
    length_counts: dict[int, int] = {}
    with gzip.open(path, "rt", encoding="ascii", errors="strict") as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().rstrip("\r\n")
            separator = handle.readline()
            quality = handle.readline().rstrip("\r\n")
            if not sequence or not separator or not quality:
                raise RuntimeError("truncated FASTQ record")
            if not header.startswith("@") or not separator.startswith("+"):
                raise RuntimeError("invalid FASTQ record structure")
            if len(sequence) != len(quality):
                raise RuntimeError("sequence/quality length mismatch")
            read_count += 1
            length_counts[len(sequence)] = length_counts.get(len(sequence), 0) + 1
    if read_count == 0:
        raise RuntimeError("empty FASTQ")
    return {"read_count": read_count, "read_length_counts": {str(k): v for k, v in sorted(length_counts.items())}}


def validate_fastq_gz(path: Path, expected_length: int) -> dict[str, Any]:
    result = inspect_fastq_gz(path)
    length_counts = {int(k): v for k, v in result["read_length_counts"].items()}
    if set(length_counts) != {expected_length}:
        raise RuntimeError(f"unexpected or mixed read lengths: {length_counts}; expected only {expected_length}")
    return result


def remaining_seconds(deadline: float) -> int:
    remaining = int(deadline - time.monotonic())
    if remaining <= 0:
        raise RuntimeError("total wall-time cap reached")
    return remaining


def process_memory_kib(pid: int) -> dict[str, int]:
    values = {"VmRSS": 0, "VmPeak": 0}
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            key = line.split(":", 1)[0]
            if key in values:
                values[key] = int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return values


def run_bounded_command(
    args: list[str], log_path: Path, workspace: Path, workspace_cap: int,
    deadline: float, memory_cap_bytes: int,
) -> dict[str, Any]:
    def enforce_child_limit() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (memory_cap_bytes, memory_cap_bytes))

    started = time.monotonic()
    peak_rss_kib = 0
    peak_vmem_kib = 0
    stop_reason = ""
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, text=True, preexec_fn=enforce_child_limit)
        while process.poll() is None:
            memory = process_memory_kib(process.pid)
            peak_rss_kib = max(peak_rss_kib, memory["VmRSS"])
            peak_vmem_kib = max(peak_vmem_kib, memory["VmPeak"])
            if directory_size(workspace) > workspace_cap:
                stop_reason = "workspace cap exceeded during command"
            elif time.monotonic() >= deadline:
                stop_reason = "total wall-time cap reached during command"
            elif memory["VmRSS"] * 1024 > memory_cap_bytes:
                stop_reason = "RAM cap exceeded during command"
            if stop_reason:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break
            time.sleep(1)
    return {
        "returncode": process.returncode,
        "seconds": round(time.monotonic() - started, 3),
        "peak_rss_kib": peak_rss_kib,
        "peak_vmem_kib": peak_vmem_kib,
        "stop_reason": stop_reason,
    }


def bounded_download(
    url: str, destination: Path, expected_bytes: int, budget: dict[str, int], retries: int,
    workspace: Path, workspace_cap: int, deadline: float,
) -> dict[str, Any]:
    attempts = 0
    last_error = ""
    destination.parent.mkdir(parents=True, exist_ok=True)
    while attempts <= retries:
        attempts += 1
        tmp = destination.with_suffix(destination.suffix + ".part")
        if tmp.exists():
            tmp.unlink()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "0714-bounded-external-pilot/1.0"})
            with urllib.request.urlopen(request, timeout=min(120, remaining_seconds(deadline))) as response, tmp.open("wb") as output:
                if response.geturl() != url:
                    raise RuntimeError(f"unexpected redirect: {response.geturl()}")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) != expected_bytes:
                    raise RuntimeError(f"Content-Length {content_length} != frozen {expected_bytes}")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    if budget["consumed"] + len(chunk) > budget["maximum"]:
                        raise RuntimeError("cumulative download cap would be exceeded")
                    if directory_size(workspace) + len(chunk) > workspace_cap:
                        raise RuntimeError("workspace cap would be exceeded during download")
                    remaining_seconds(deadline)
                    output.write(chunk)
                    budget["consumed"] += len(chunk)
            if tmp.stat().st_size != expected_bytes:
                raise RuntimeError(f"downloaded bytes {tmp.stat().st_size} != frozen {expected_bytes}")
            tmp.replace(destination)
            return {"attempts": attempts, "cumulative_bytes": budget["consumed"]}
        except Exception as exc:  # noqa: BLE001 - retry policy is explicitly bounded.
            last_error = str(exc)
            if tmp.exists():
                tmp.unlink()
            if budget["consumed"] >= budget["maximum"]:
                break
    raise RuntimeError(f"download failed after {attempts} attempt(s): {last_error}")


def bounded_external_pilot(out_dir: Path, params: dict[str, Any], kraken2_db: Path, bracken_db: Path, threads: int) -> int:
    started = time.monotonic()
    deadline = started + int(params.get("maximum_wall_time_seconds", 28800))
    manifest = params.get("pilot_runs", [])
    allowed = {"CRR2423962", "CRR2423909"}
    if len(manifest) != 2 or {str(row.get("run_accession")) for row in manifest} != allowed:
        raise RuntimeError("pilot allowlist mismatch")
    if threads > 8:
        raise RuntimeError("thread cap exceeded")
    maximum_download = int(params.get("maximum_download_bytes", 0))
    if maximum_download != 10526255:
        raise RuntimeError("frozen cumulative download cap mismatch")
    maximum_workspace = int(params.get("maximum_working_space_bytes", 0))
    if maximum_workspace > 5_000_000_000:
        raise RuntimeError("workspace cap exceeds authorization")
    if shutil.disk_usage(out_dir).free < int(params.get("minimum_free_disk_bytes", 5_000_000_000)):
        raise RuntimeError("minimum free disk requirement not met")
    memory_cap_bytes = int(params.get("memory_cap_bytes", 0))
    if memory_cap_bytes != 64 * 1024**3:
        raise RuntimeError("64 GiB memory cap mismatch")
    if not os.access(kraken2_db, os.R_OK) or not os.access(bracken_db, os.R_OK):
        raise RuntimeError("classifier database is not readable")

    db_inventory = readonly_inventory(out_dir / "database_identity", Path.cwd(), kraken2_db, bracken_db)
    if db_inventory != 0:
        raise RuntimeError("database identity inventory failed")
    inventory = load_json(out_dir / "database_identity" / "hospital_readonly_inventory.json")
    installed = {int(row["read_length_nt"]): row for row in inventory["bracken_redistributions"]}
    if params.get("host_filtering") is not False:
        raise RuntimeError("host filtering must be explicitly disabled")
    for row in manifest:
        if str(row.get("host_status")) != "HOST_DEPLETED":
            raise RuntimeError(f"host-depletion provenance is not closed for {row.get('run_accession')}")
        expected_length = int(row["expected_read_length"])
        redistribution = bracken_db / str(installed.get(expected_length, {}).get("file", ""))
        if expected_length not in installed or not redistribution.is_file():
            raise RuntimeError(f"matching Bracken redistribution missing for {expected_length} nt")
    budget = {"consumed": 0, "maximum": maximum_download}
    fastq_dir = out_dir / "fastq"
    taxonomy_dir = out_dir / "taxonomy"
    logs_dir = out_dir / "logs"
    for directory in (fastq_dir, taxonomy_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    statuses: list[dict[str, Any]] = []
    stop_event = ""

    for row in manifest:
        run = str(row["run_accession"])
        expected_bytes = int(row["expected_bytes"])
        expected_length = int(row["expected_read_length"])
        status: dict[str, Any] = {"run_accession": run, "expected_bytes": expected_bytes, "expected_read_length": expected_length}
        try:
            if expected_length not in installed:
                raise RuntimeError(f"matching Bracken redistribution missing for {expected_length} nt")
            redistribution = bracken_db / str(installed[expected_length]["file"])
            if not redistribution.is_file():
                raise RuntimeError(f"matching Bracken redistribution missing: {redistribution}")
            fastq = fastq_dir / f"{run}.fq.gz"
            if directory_size(out_dir) > maximum_workspace:
                raise RuntimeError("workspace cap exceeded before download")
            download = bounded_download(
                str(row["url"]), fastq, expected_bytes, budget, int(params.get("maximum_retry_count", 2)),
                out_dir, maximum_workspace, deadline,
            )
            status.update(download)
            status["downloaded_bytes"] = fastq.stat().st_size
            status["sha256"] = sha256_small_file(fastq)
            status.update(validate_fastq_gz(fastq, expected_length))

            kreport = taxonomy_dir / f"{run}.kreport"
            kout = taxonomy_dir / f"{run}.kraken2.out"
            bracken_out = taxonomy_dir / f"{run}.bracken.species.tsv"
            if directory_size(out_dir) > maximum_workspace:
                raise RuntimeError("workspace cap exceeded before Kraken2")
            kraken = run_bounded_command([
                "kraken2", "--db", str(kraken2_db), "--threads", str(threads),
                "--report", str(kreport), "--output", str(kout), str(fastq),
            ], logs_dir / f"{run}.kraken2.log", out_dir, maximum_workspace, deadline, memory_cap_bytes)
            status["kraken2"] = kraken
            if kraken["returncode"] != 0 or kraken["stop_reason"] or not file_nonempty(kreport):
                raise RuntimeError(f"Kraken2 failed: {kraken}")

            if directory_size(out_dir) > maximum_workspace:
                raise RuntimeError("workspace cap exceeded before Bracken")
            bracken = run_bounded_command([
                "bracken", "-d", str(bracken_db), "-i", str(kreport), "-o", str(bracken_out),
                "-r", str(expected_length), "-l", "S",
            ], logs_dir / f"{run}.bracken.log", out_dir, maximum_workspace, deadline, memory_cap_bytes)
            status["bracken"] = bracken
            if bracken["returncode"] != 0 or bracken["stop_reason"] or not file_nonempty(bracken_out):
                raise RuntimeError(f"Bracken failed: {bracken}")
            status.update({"status": "done", "redistribution_file": str(redistribution), "error": ""})
        except Exception as exc:  # noqa: BLE001 - mandatory stop is recorded.
            status.update({"status": "stopped", "error": str(exc)})
            stop_event = f"{run}: {exc}"
        statuses.append(status)
        if stop_event:
            break
        if directory_size(out_dir) > maximum_workspace:
            stop_event = "workspace cap exceeded"
            break
        if time.monotonic() >= deadline:
            stop_event = "wall-time cap exceeded"
            break

    output_inventory = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file():
            output_inventory.append({"path": str(path.relative_to(out_dir)), "size_bytes": path.stat().st_size, "sha256_if_small": sha256_small_file(path)})
    peak_kib = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    summary = {
        "pilot_type": "BOUNDED_TECHNICAL_SMOKE_ONLY",
        "generated_at": utc_now(),
        "final_status": "done" if len(statuses) == 2 and all(row.get("status") == "done" for row in statuses) else "stopped",
        "stop_event": stop_event,
        "cumulative_downloaded_bytes": budget["consumed"],
        "wall_time_seconds": round(time.monotonic() - started, 3),
        "peak_ram_kib": peak_kib,
        "final_workspace_bytes": directory_size(out_dir),
        "database_manifest_identity_sha256": inventory["database_manifest_identity_sha256"],
        "runs": statuses,
        "output_inventory": output_inventory,
        "biological_inference": "PROHIBITED",
    }
    write_json(out_dir / "pilot_summary.json", summary)
    return 0 if summary["final_status"] == "done" else 2


def bounded_read_length_audit(out_dir: Path, params: dict[str, Any]) -> int:
    started = time.monotonic()
    deadline = started + int(params.get("maximum_wall_time_seconds", 7200))
    manifest = params.get("audit_runs", [])
    allowed = {
        "CRR2423961", "CRR2424000", "CRR2423957", "CRR2423986",
        "CRR2423912", "CRR2423921", "CRR2423991", "CRR2424010",
    }
    if len(manifest) != 8 or {str(row.get("run_accession")) for row in manifest} != allowed:
        raise RuntimeError("read-length audit allowlist mismatch")
    maximum_download = int(params.get("maximum_download_bytes", 0))
    if maximum_download != 12_866_805:
        raise RuntimeError("frozen cumulative download cap mismatch")
    if sum(int(row.get("expected_bytes", 0)) for row in manifest) != maximum_download:
        raise RuntimeError("manifest byte sum does not equal cumulative cap")
    if params.get("host_filtering") is not False or params.get("taxonomy") is not False:
        raise RuntimeError("host filtering and taxonomy must be explicitly disabled")
    maximum_workspace = int(params.get("maximum_working_space_bytes", 1_000_000_000))
    if maximum_workspace > 1_000_000_000:
        raise RuntimeError("workspace cap exceeds frozen audit envelope")
    if shutil.disk_usage(out_dir).free < int(params.get("minimum_free_disk_bytes", 1_000_000_000)):
        raise RuntimeError("minimum free disk requirement not met")

    budget = {"consumed": 0, "maximum": maximum_download}
    fastq_dir = out_dir / "fastq"
    fastq_dir.mkdir(parents=True, exist_ok=True)
    statuses: list[dict[str, Any]] = []
    histogram_rows: list[dict[str, Any]] = []
    stop_event = ""
    installed_lengths = [50, 75, 100, 150, 200, 250, 300]

    for row in manifest:
        run = str(row["run_accession"])
        expected_bytes = int(row["expected_bytes"])
        status: dict[str, Any] = {"run_accession": run, "expected_bytes": expected_bytes}
        try:
            if run not in allowed:
                raise RuntimeError(f"unauthorized run encountered: {run}")
            if directory_size(out_dir) > maximum_workspace:
                raise RuntimeError("workspace cap exceeded before download")
            fastq = fastq_dir / f"{run}.fq.gz"
            download = bounded_download(
                str(row["url"]), fastq, expected_bytes, budget,
                int(params.get("maximum_retry_count", 2)), out_dir,
                maximum_workspace, deadline,
            )
            status.update(download)
            status["downloaded_bytes"] = fastq.stat().st_size
            status["sha256"] = sha256_small_file(fastq)
            inspection = inspect_fastq_gz(fastq)
            counts = {int(k): int(v) for k, v in inspection["read_length_counts"].items()}
            total = int(inspection["read_count"])
            highest = max(counts.values())
            modal_lengths = sorted(k for k, value in counts.items() if value == highest)
            for length, count in sorted(counts.items()):
                histogram_rows.append({
                    "run_accession": run,
                    "read_length_nt": length,
                    "read_count": count,
                    "fraction": f"{count / total:.12f}",
                })
            status.update({
                "fastq_integrity": "PASS",
                "total_reads": total,
                "minimum_read_length": min(counts),
                "maximum_read_length": max(counts),
                "distinct_read_lengths": len(counts),
                "modal_read_length": modal_lengths[0],
                "all_modal_read_lengths": modal_lengths,
                "modal_read_count": highest,
                "modal_fraction": highest / total,
                "fractions_at_installed_bracken_lengths": {
                    str(length): counts.get(length, 0) / total for length in installed_lengths
                },
                "read_length_classification": "FIXED_LENGTH" if len(counts) == 1 else "VARIABLE_LENGTH",
                "status": "done",
                "error": "",
            })
        except Exception as exc:  # noqa: BLE001 - mandatory stop is recorded.
            status.update({"status": "stopped", "read_length_classification": "INVALID_STOPPED", "error": str(exc)})
            stop_event = f"{run}: {exc}"
        statuses.append(status)
        if stop_event:
            break
        if directory_size(out_dir) > maximum_workspace:
            stop_event = "workspace cap exceeded between runs"
            break
        remaining_seconds(deadline)

    histogram_path = out_dir / "complete_read_length_histograms.tsv"
    with histogram_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["run_accession", "read_length_nt", "read_count", "fraction"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(histogram_rows)
    summary = {
        "audit_type": "BOUNDED_READ_LENGTH_ONLY",
        "generated_at": utc_now(),
        "final_status": "done" if len(statuses) == 8 and all(row.get("status") == "done" for row in statuses) else "stopped",
        "stop_event": stop_event,
        "cumulative_downloaded_bytes": budget["consumed"],
        "wall_time_seconds": round(time.monotonic() - started, 3),
        "peak_ram_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "final_workspace_bytes": directory_size(out_dir),
        "fixed_length_count": sum(row.get("read_length_classification") == "FIXED_LENGTH" for row in statuses),
        "variable_length_count": sum(row.get("read_length_classification") == "VARIABLE_LENGTH" for row in statuses),
        "failed_or_unresolved_count": sum(row.get("status") != "done" for row in statuses),
        "runs": statuses,
        "taxonomy_performed": False,
        "trimming_or_filtering_performed": False,
        "biological_inference": "PROHIBITED",
    }
    write_json(out_dir / "read_length_audit_summary.json", summary)
    return 0 if summary["final_status"] == "done" else 2


def trim_fastq_exact(path: Path, destination: Path, target_length: int) -> dict[str, Any]:
    """Retain reads at least target_length and deterministically trim to it."""
    total_reads = retained_reads = total_bases = retained_input_bases = output_bases = 0
    logical_input = hashlib.sha256()
    logical_output = hashlib.sha256()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "rb") as source, destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=0) as output:
            while True:
                header = source.readline()
                if not header:
                    break
                sequence = source.readline().rstrip(b"\r\n")
                separator = source.readline()
                quality = source.readline().rstrip(b"\r\n")
                if not sequence or not separator or not quality:
                    raise RuntimeError("truncated FASTQ record during trimming")
                if not header.startswith(b"@") or not separator.startswith(b"+") or len(sequence) != len(quality):
                    raise RuntimeError("invalid FASTQ record during trimming")
                canonical_input = header.rstrip(b"\r\n") + b"\n" + sequence + b"\n+\n" + quality + b"\n"
                logical_input.update(canonical_input)
                total_reads += 1
                total_bases += len(sequence)
                if len(sequence) < target_length:
                    continue
                retained_reads += 1
                retained_input_bases += len(sequence)
                trimmed_sequence = sequence[:target_length]
                trimmed_quality = quality[:target_length]
                canonical_output = header.rstrip(b"\r\n") + b"\n" + trimmed_sequence + b"\n+\n" + trimmed_quality + b"\n"
                logical_output.update(canonical_output)
                output.write(canonical_output)
                output_bases += target_length
    if total_reads == 0 or retained_reads == 0:
        raise RuntimeError("trimming produced no retained reads")
    return {
        "total_reads": total_reads,
        "retained_reads": retained_reads,
        "retained_read_fraction": retained_reads / total_reads,
        "total_bases": total_bases,
        "retained_input_bases": retained_input_bases,
        "retained_base_fraction": retained_input_bases / total_bases,
        "trimmed_output_bases": output_bases,
        "logical_input_sha256": logical_input.hexdigest(),
        "logical_output_sha256": logical_output.hexdigest(),
    }


def parse_kraken_report(path: Path) -> dict[str, Any]:
    taxa: dict[str, dict[str, Any]] = {}
    total = classified = unclassified = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 6:
                continue
            clade_reads = int(fields[1])
            rank = fields[3].strip()
            taxid = fields[4].strip()
            name = fields[5].strip()
            if rank == "U":
                unclassified = clade_reads
            elif rank == "R":
                classified = clade_reads
            if rank in {"S", "G"} and clade_reads > 0:
                taxa[f"{rank}:{taxid}"] = {"rank": rank, "taxid": taxid, "name": name, "count": clade_reads}
    total = classified + unclassified
    if total <= 0:
        raise RuntimeError(f"Kraken report has no classified/unclassified total: {path}")
    return {"total": total, "classified": classified, "unclassified": unclassified, "taxa": taxa}


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for position in range(start, end):
            ranks[order[position]] = rank
        start = end
    return ranks


def spearman(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a) < 2:
        return None
    ranks_a, ranks_b = average_ranks(values_a), average_ranks(values_b)
    mean_a, mean_b = sum(ranks_a) / len(ranks_a), sum(ranks_b) / len(ranks_b)
    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(ranks_a, ranks_b))
    denominator = math.sqrt(sum((a - mean_a) ** 2 for a in ranks_a) * sum((b - mean_b) ** 2 for b in ranks_b))
    return numerator / denominator if denominator else None


def taxonomy_stability(native: dict[str, Any], trimmed: dict[str, Any], rank: str) -> dict[str, Any]:
    keys = sorted(set(native["taxa"]) | set(trimmed["taxa"]))
    keys = [key for key in keys if key.startswith(rank + ":")]
    native_values = [native["taxa"].get(key, {}).get("count", 0) / native["total"] for key in keys]
    trimmed_values = [trimmed["taxa"].get(key, {}).get("count", 0) / trimmed["total"] for key in keys]
    denominator = sum(native_values) + sum(trimmed_values)
    bray = sum(abs(a - b) for a, b in zip(native_values, trimmed_values)) / denominator if denominator else 0.0
    major_rows = []
    for key, native_value, trimmed_value in zip(keys, native_values, trimmed_values):
        if max(native_value, trimmed_value) < 0.01:
            continue
        item = native["taxa"].get(key) or trimmed["taxa"][key]
        relative_change = None if native_value == 0 else (trimmed_value - native_value) / native_value
        major_rows.append({
            "taxon_key": key, "taxon_name": item["name"], "native_fraction": native_value,
            "trimmed_fraction": trimmed_value, "absolute_change": trimmed_value - native_value,
            "relative_change": relative_change,
        })
    return {
        "rank": rank, "union_taxa": len(keys), "native_richness": sum(value > 0 for value in native_values),
        "trimmed_richness": sum(value > 0 for value in trimmed_values), "spearman": spearman(native_values, trimmed_values),
        "bray_curtis": bray, "major_taxa": major_rows,
    }


def bounded_taxonomy_method_benchmark(
    out_dir: Path, params: dict[str, Any], kraken2_db: Path, bracken_db: Path, threads: int,
) -> int:
    """Zero-download, four-run technical comparison of native and Trim50 taxonomy."""
    started = time.monotonic()
    deadline = started + int(params.get("maximum_wall_time_seconds", 28800))
    allowed = {"CRR2423957", "CRR2424000", "CRR2423921", "CRR2424010"}
    manifest = params.get("benchmark_runs", [])
    if len(manifest) != 4 or {str(row.get("run_accession")) for row in manifest} != allowed:
        raise RuntimeError("taxonomy benchmark allowlist mismatch")
    if int(params.get("maximum_new_download_bytes", -1)) != 0:
        raise RuntimeError("taxonomy benchmark must use zero new download bytes")
    if threads > 16:
        raise RuntimeError("thread cap exceeded")
    workspace_cap = int(params.get("maximum_working_space_bytes", 0))
    if not 0 < workspace_cap <= 100_000_000_000:
        raise RuntimeError("invalid workspace cap")
    memory_cap = int(params.get("memory_cap_bytes", 0))
    if memory_cap != 64 * 1024**3:
        raise RuntimeError("64 GiB memory cap mismatch")
    expected_identity = str(params.get("database_manifest_identity_sha256", ""))
    readonly_inventory(out_dir / "database_identity", Path.cwd(), kraken2_db, bracken_db)
    inventory = load_json(out_dir / "database_identity" / "hospital_readonly_inventory.json")
    if inventory["database_manifest_identity_sha256"] != expected_identity:
        raise RuntimeError("database manifest identity mismatch")
    redistribution = bracken_db / "database50mers.kmer_distrib"
    if not redistribution.is_file():
        raise RuntimeError("installed 50-nt Bracken redistribution is missing")

    source_root = Path(str(params.get("source_audit_result", ""))) / "fastq"
    histogram_path = Path(str(params.get("expected_histogram_path", "")))
    if not histogram_path.is_file():
        raise RuntimeError("frozen audit histogram is missing")
    expected_histograms: dict[str, dict[str, int]] = {}
    for histogram_row in read_tsv(histogram_path):
        accession = histogram_row["run_accession"]
        expected_histograms.setdefault(accession, {})[histogram_row["read_length_nt"]] = int(histogram_row["read_count"])
    trim_dir, taxonomy_dir, logs_dir = out_dir / "trim50", out_dir / "taxonomy", out_dir / "logs"
    for directory in (trim_dir, taxonomy_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    run_results: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    major_rows: list[dict[str, Any]] = []
    stop_event = ""
    for row in manifest:
        run = str(row["run_accession"])
        result: dict[str, Any] = {"run_accession": run, "architecture_role": row["architecture_role"]}
        try:
            source = source_root / f"{run}.fq.gz"
            if not source.is_file() or source.stat().st_size != int(row["expected_bytes"]):
                raise RuntimeError("retained audit FASTQ missing or byte count mismatch")
            if sha256_small_file(source) != str(row["sha256"]):
                raise RuntimeError("retained audit FASTQ checksum mismatch")
            inspection = inspect_fastq_gz(source)
            if inspection["read_length_counts"] != expected_histograms.get(run):
                raise RuntimeError("retained audit FASTQ length histogram mismatch")
            trimmed = trim_dir / f"{run}.trim50.fq.gz"
            retention = trim_fastq_exact(source, trimmed, 50)
            result["retention"] = retention
            if run == "CRR2423957" and retention["logical_input_sha256"] != retention["logical_output_sha256"]:
                raise RuntimeError("fixed-50 identity control failed")
            reports = {}
            command_results = {}
            for label, fastq in (("native", source), ("trim50", trimmed)):
                report = taxonomy_dir / f"{run}.{label}.kreport"
                command = [
                    "kraken2", "--db", str(kraken2_db), "--threads", str(threads),
                    "--confidence", str(params.get("kraken2_confidence", 0.0)),
                    "--minimum-hit-groups", str(params.get("kraken2_minimum_hit_groups", 2)),
                    "--report", str(report), "--output", "/dev/null", str(fastq),
                ]
                command_results[label] = run_bounded_command(
                    command, logs_dir / f"{run}.{label}.kraken2.log", out_dir, workspace_cap, deadline, memory_cap,
                )
                if command_results[label]["returncode"] != 0 or command_results[label]["stop_reason"] or not file_nonempty(report):
                    raise RuntimeError(f"Kraken2 {label} failed: {command_results[label]}")
                reports[label] = parse_kraken_report(report)
            bracken_out = taxonomy_dir / f"{run}.trim50.bracken.species.tsv"
            bracken_result = run_bounded_command([
                "bracken", "-d", str(bracken_db), "-i", str(taxonomy_dir / f"{run}.trim50.kreport"),
                "-o", str(bracken_out), "-r", "50", "-l", "S", "-t", "10",
            ], logs_dir / f"{run}.trim50.bracken.log", out_dir, workspace_cap, deadline, memory_cap)
            if bracken_result["returncode"] != 0 or bracken_result["stop_reason"] or not file_nonempty(bracken_out):
                raise RuntimeError(f"Bracken trim50 failed: {bracken_result}")
            result.update({
                "input_bytes": source.stat().st_size, "input_sha256": str(row["sha256"]),
                "native_classified_fraction": reports["native"]["classified"] / reports["native"]["total"],
                "trim50_classified_fraction": reports["trim50"]["classified"] / reports["trim50"]["total"],
                "commands": command_results, "bracken": bracken_result, "status": "done", "error": "",
            })
            for rank in ("S", "G"):
                stability = taxonomy_stability(reports["native"], reports["trim50"], rank)
                comparison_rows.append({
                    "run_accession": run, "architecture_role": row["architecture_role"], "rank": rank,
                    "total_reads": retention["total_reads"], "retained_reads": retention["retained_reads"],
                    "retained_read_fraction": retention["retained_read_fraction"], "total_bases": retention["total_bases"],
                    "retained_input_bases": retention["retained_input_bases"], "retained_base_fraction": retention["retained_base_fraction"],
                    "native_classified_fraction": result["native_classified_fraction"],
                    "trim50_classified_fraction": result["trim50_classified_fraction"],
                    "native_richness": stability["native_richness"], "trim50_richness": stability["trimmed_richness"],
                    "spearman": stability["spearman"], "bray_curtis": stability["bray_curtis"],
                })
                for item in stability["major_taxa"]:
                    major_rows.append({"run_accession": run, "rank": rank, **item})
        except Exception as exc:  # noqa: BLE001 - bounded stop is recorded.
            result.update({"status": "stopped", "error": str(exc)})
            stop_event = f"{run}: {exc}"
        run_results.append(result)
        if stop_event:
            break
        if directory_size(out_dir) > workspace_cap:
            stop_event = "workspace cap exceeded between samples"
            break
        remaining_seconds(deadline)

    for filename, rows in (("benchmark_comparisons.tsv", comparison_rows), ("major_taxon_changes.tsv", major_rows)):
        if rows:
            with (out_dir / filename).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
                writer.writeheader(); writer.writerows(rows)
    summary = {
        "benchmark_type": "ZERO_DOWNLOAD_TAXONOMY_METHOD_DISCRIMINATION", "generated_at": utc_now(),
        "final_status": "done" if len(run_results) == 4 and all(row.get("status") == "done" for row in run_results) else "stopped",
        "stop_event": stop_event, "new_downloaded_bytes": 0, "wall_time_seconds": round(time.monotonic() - started, 3),
        "peak_ram_kib": max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss),
        "final_workspace_bytes": directory_size(out_dir), "database_manifest_identity_sha256": expected_identity,
        "kraken2_confidence": params.get("kraken2_confidence", 0.0), "kraken2_minimum_hit_groups": params.get("kraken2_minimum_hit_groups", 2),
        "bracken_redistribution": str(redistribution), "runs": run_results,
        "host_filtering_performed": False, "biological_inference": "PROHIBITED",
    }
    write_json(out_dir / "benchmark_summary.json", summary)
    return 0 if summary["final_status"] == "done" else 2


def bounded_native_kraken2_pilot(
    out_dir: Path, params: dict[str, Any], kraken2_db: Path, threads: int,
) -> int:
    """Zero-download eight-run native-read Kraken2-only technical pilot."""
    started = time.monotonic()
    deadline = started + int(params.get("maximum_wall_time_seconds", 28800))
    allowed = {"CRR2423961", "CRR2424000", "CRR2423957", "CRR2423986", "CRR2423912", "CRR2423921", "CRR2423991", "CRR2424010"}
    manifest = params.get("pilot_runs", [])
    if len(manifest) != 8 or {str(row.get("run_accession")) for row in manifest} != allowed:
        raise RuntimeError("native Kraken2 pilot allowlist mismatch")
    if int(params.get("maximum_new_download_bytes", -1)) != 0:
        raise RuntimeError("native Kraken2 pilot must use zero new download bytes")
    if threads > 16:
        raise RuntimeError("thread cap exceeded")
    workspace_cap = int(params.get("maximum_working_space_bytes", 0))
    if not 0 < workspace_cap <= 100_000_000_000:
        raise RuntimeError("invalid workspace cap")
    memory_cap = int(params.get("memory_cap_bytes", 0))
    if memory_cap != 64 * 1024**3:
        raise RuntimeError("64 GiB memory cap mismatch")
    expected_identity = str(params.get("database_manifest_identity_sha256", ""))
    readonly_inventory(out_dir / "database_identity", Path.cwd(), kraken2_db, kraken2_db)
    inventory = load_json(out_dir / "database_identity" / "hospital_readonly_inventory.json")
    if inventory["database_manifest_identity_sha256"] != expected_identity:
        raise RuntimeError("database manifest identity mismatch")

    source_root = Path(str(params.get("source_audit_result", ""))) / "fastq"
    taxonomy_dir, logs_dir = out_dir / "native_kraken2", out_dir / "logs"
    taxonomy_dir.mkdir(parents=True, exist_ok=True); logs_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    stop_event = ""
    for row in manifest:
        run = str(row["run_accession"])
        result: dict[str, Any] = {"run_accession": run, "clinical_group": row["clinical_group"], "nominal_length_nt": row["nominal_length_nt"]}
        try:
            source = source_root / f"{run}.fq.gz"
            if not source.is_file() or source.stat().st_size != int(row["expected_bytes"]):
                raise RuntimeError("retained audit FASTQ missing or byte count mismatch")
            if sha256_small_file(source) != str(row["sha256"]):
                raise RuntimeError("retained audit FASTQ checksum mismatch")
            inspection = inspect_fastq_gz(source)
            report = taxonomy_dir / f"{run}.native.kreport"
            output = taxonomy_dir / f"{run}.native.kraken2.out"
            command = ["kraken2", "--db", str(kraken2_db), "--threads", str(threads), "--report", str(report), "--output", str(output), str(source)]
            command_result = run_bounded_command(command, logs_dir / f"{run}.kraken2.log", out_dir, workspace_cap, deadline, memory_cap)
            if command_result["returncode"] != 0 or command_result["stop_reason"] or not file_nonempty(report):
                raise RuntimeError(f"Kraken2 failed: {command_result}")
            parsed = parse_kraken_report(report)
            result.update({"status": "done", "error": "", "input_bytes": source.stat().st_size, "input_sha256": row["sha256"], "read_count": inspection["read_count"], "read_length_counts": inspection["read_length_counts"], "classified_reads": parsed["classified"], "unclassified_reads": parsed["unclassified"], "classified_fraction": parsed["classified"] / parsed["total"], "command": command, "command_result": command_result})
        except Exception as exc:  # noqa: BLE001
            result.update({"status": "stopped", "error": str(exc)})
            stop_event = f"{run}: {exc}"
        results.append(result)
        if stop_event:
            break
        if directory_size(out_dir) > workspace_cap:
            stop_event = "workspace cap exceeded between samples"; break
        remaining_seconds(deadline)
    summary = {"pilot_type": "ZERO_DOWNLOAD_NATIVE_KRAKEN2_ONLY", "generated_at": utc_now(), "final_status": "done" if len(results) == 8 and all(row.get("status") == "done" for row in results) else "stopped", "stop_event": stop_event, "new_downloaded_bytes": 0, "wall_time_seconds": round(time.monotonic() - started, 3), "peak_ram_kib": max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss), "final_workspace_bytes": directory_size(out_dir), "database_manifest_identity_sha256": expected_identity, "historical_default_behavior": {"confidence_explicit": False, "minimum_hit_groups_explicit": False}, "runs": results, "bracken_performed": False, "trimming_performed": False, "biological_inference": "PROHIBITED"}
    write_json(out_dir / "pilot_summary.json", summary)
    handoff = Path(str(params.get("handoff_dir", "/mnt/disk1/0714_handoff"))) / str(params.get("job_id", "native_kraken2_pilot"))
    handoff.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_dir / "pilot_summary.json", handoff / "pilot_summary.json")
    return 0 if summary["final_status"] == "done" else 2


def execute_host_removal_amr(
    rows: list[dict[str, str]],
    out_dir: Path,
    params: dict[str, Any],
    work_dir: Path,
    fastq_dir: Path,
    qc_dir: Path,
    host_removed_dir: Path,
    kraken_dir: Path,
    kraken2_db: Path,
    bracken_db: Path,
    host_index: str,
    threads: int,
) -> dict[str, Any]:
    sra_dir = work_dir / "sra"
    amr_dir = out_dir / "amr_screen"
    logs_dir = out_dir / "logs"
    for directory in [sra_dir, fastq_dir, qc_dir, host_removed_dir, kraken_dir, amr_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    amr_db = Path(str(params.get("amr_db", ""))).expanduser()
    amr_max_reads = int(params.get("amr_max_reads", 200000))
    per_command_timeout = int(params.get("per_command_timeout_seconds", 7200))
    continue_on_run_error = bool(params.get("continue_on_run_error", True))
    run_status: list[dict[str, Any]] = []

    for row in rows:
        run = row.get("run", "").strip()
        if not run:
            continue
        status = {
            "run": run,
            "pathogen_group": row.get("pathogen_group", ""),
            "baseline_top_pathogen": row.get("top_pathogen", ""),
            "status": "running",
            "error": "",
        }
        try:
            sra_path = sra_dir / run / f"{run}.sra"
            fastq = fastq_dir / f"{run}.fastq"
            fastq_gz = fastq_dir / f"{run}.fastq.gz"
            qc_fastq = qc_dir / f"{run}.fastq.gz"
            host_removed_fastq = host_removed_dir / f"{run}.fastq.gz"
            kreport = kraken_dir / f"{run}.kreport"
            kout = kraken_dir / f"{run}.kraken2.out"
            bracken_out = kraken_dir / f"{run}.bracken"
            fasta_subset = amr_dir / f"{run}.host_removed_subset.fasta"
            amr_out = amr_dir / f"{run}.amrfinder.tsv"

            if not file_nonempty(sra_path):
                result = run_command(["prefetch", run, "--output-directory", str(sra_dir)], timeout=per_command_timeout)
                (logs_dir / f"{run}.prefetch.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"prefetch failed rc={result.returncode}")

            if not file_nonempty(fastq_gz):
                if not file_nonempty(fastq):
                    result = run_command(
                        ["fasterq-dump", str(sra_path), "--outdir", str(fastq_dir), "--threads", str(threads)],
                        timeout=per_command_timeout,
                    )
                    (logs_dir / f"{run}.fasterq-dump.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                    if result.returncode != 0:
                        raise RuntimeError(f"fasterq-dump failed rc={result.returncode}")
                result = run_command(["gzip", "-f", str(fastq)], timeout=per_command_timeout)
                (logs_dir / f"{run}.gzip.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"gzip failed rc={result.returncode}")

            if not file_nonempty(qc_fastq):
                result = run_command(
                    [
                        "fastp",
                        "-i",
                        str(fastq_gz),
                        "-o",
                        str(qc_fastq),
                        "--thread",
                        str(threads),
                        "--json",
                        str(qc_dir / f"{run}.fastp.json"),
                        "--html",
                        str(qc_dir / f"{run}.fastp.html"),
                    ],
                    timeout=per_command_timeout,
                )
                (logs_dir / f"{run}.fastp.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"fastp failed rc={result.returncode}")

            if not file_nonempty(host_removed_fastq):
                result = run_command(
                    [
                        "bowtie2",
                        "-x",
                        host_index,
                        "-U",
                        str(qc_fastq),
                        "--threads",
                        str(threads),
                        "--un-gz",
                        str(host_removed_fastq),
                        "-S",
                        "/dev/null",
                    ],
                    timeout=per_command_timeout,
                )
                (logs_dir / f"{run}.bowtie2_host_removal.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"bowtie2 host-removal failed rc={result.returncode}")

            if not file_nonempty(kreport) or not file_nonempty(kout):
                result = run_command(
                    [
                        "kraken2",
                        "--db",
                        str(kraken2_db),
                        "--threads",
                        str(threads),
                        "--report",
                        str(kreport),
                        "--output",
                        str(kout),
                        str(host_removed_fastq),
                    ],
                    timeout=per_command_timeout,
                )
                (logs_dir / f"{run}.kraken2.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"kraken2 failed rc={result.returncode}")

            if not file_nonempty(bracken_out):
                result = run_command(
                    ["bracken", "-d", str(bracken_db), "-i", str(kreport), "-o", str(bracken_out)],
                    timeout=per_command_timeout,
                )
                (logs_dir / f"{run}.bracken.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(f"bracken failed rc={result.returncode}")

            amr_status = "skipped_no_db"
            amr_records = 0
            if amr_db.exists() and shutil.which("amrfinder"):
                if not file_nonempty(fasta_subset):
                    subset_reads = fastq_gz_to_fasta_subset(host_removed_fastq, fasta_subset, amr_max_reads)
                else:
                    subset_reads = amr_max_reads
                if not file_nonempty(amr_out):
                    result = run_command(
                        ["amrfinder", "-n", str(fasta_subset), "-d", str(amr_db), "-o", str(amr_out)],
                        timeout=per_command_timeout,
                    )
                    (logs_dir / f"{run}.amrfinder.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
                    if result.returncode != 0:
                        amr_status = f"failed_rc_{result.returncode}"
                    else:
                        amr_status = "done_short_read_subset"
                else:
                    amr_status = "done_short_read_subset"
                if amr_out.exists():
                    with amr_out.open(encoding="utf-8", errors="replace") as f:
                        amr_records = max(0, sum(1 for _ in f) - 1)
                status["amr_subset_reads"] = subset_reads
            status.update(
                {
                    "status": "done",
                    "host_removed_fastq": str(host_removed_fastq),
                    "kreport": str(kreport),
                    "bracken": str(bracken_out),
                    "amr_status": amr_status,
                    "amr_records": amr_records,
                }
            )
        except Exception as exc:  # noqa: BLE001 - per-run failure is recorded and the job continues.
            status["status"] = "failed"
            status["error"] = str(exc)
            if not continue_on_run_error:
                run_status.append(status)
                break
        run_status.append(status)

    fieldnames = [
        "run",
        "pathogen_group",
        "baseline_top_pathogen",
        "status",
        "error",
        "amr_status",
        "amr_records",
        "amr_subset_reads",
        "host_removed_fastq",
        "kreport",
        "bracken",
    ]
    with (out_dir / "run_status.tsv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in run_status)

    done_count = sum(1 for row in run_status if row["status"] == "done")
    failed = [row for row in run_status if row["status"] != "done"]
    summary = {
        "checked_at": utc_now(),
        "execute_mode": "host_removal_amr_screen",
        "run_count": len(run_status),
        "done_count": done_count,
        "failed_count": len(failed),
        "final_status": "done" if not failed else "partial_failed",
        "amr_note": (
            "AMRFinderPlus was run only on a capped host-removed short-read FASTA subset. "
            "Use as exploratory AMR signal only, not as phenotypic resistance evidence."
        ),
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "summary.md").write_text(
        "\n".join(
            [
                "# Host-Removal and AMR Screen Summary",
                "",
                f"- Runs: {len(run_status)}",
                f"- Done: {done_count}",
                f"- Failed: {len(failed)}",
                f"- Final status: {summary['final_status']}",
                "",
                "## AMR Interpretation Guardrail",
                "",
                summary["amr_note"],
                "",
                "## Output Files",
                "",
                "- `run_status.tsv`",
                "- `kraken2_confirm/`",
                "- `amr_screen/`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


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
    if execute_mode not in {"plan_only", "host_removal_amr_screen", "readonly_inventory", "bounded_external_pilot", "bounded_read_length_audit", "bounded_taxonomy_method_benchmark", "bounded_native_kraken2_pilot"}:
        errors.append("unsupported execute_mode")
    if execute_mode in {"readonly_inventory", "bounded_external_pilot", "bounded_read_length_audit", "bounded_taxonomy_method_benchmark", "bounded_native_kraken2_pilot"}:
        rows: list[dict[str, str]] = []
    elif not shortlist_path.exists():
        errors.append(f"shortlist_path not found: {shortlist_path}")
        rows: list[dict[str, str]] = []
    else:
        selected_offset = int(params.get("selected_offset", 0))
        rows = read_tsv(shortlist_path)[selected_offset:selected_offset + selected_limit]
    if execute_mode != "bounded_read_length_audit" and not kraken2_db.exists():
        errors.append(f"kraken2_db not found: {kraken2_db}")
    if execute_mode != "bounded_read_length_audit" and not bracken_db.exists():
        warnings.append(f"bracken_db not found or not checked: {bracken_db}")

    if execute_mode == "bounded_read_length_audit":
        required, optional = [], []
    elif execute_mode in {"readonly_inventory", "bounded_external_pilot", "bounded_taxonomy_method_benchmark"}:
        required, optional = ["kraken2", "bracken"], ["fastp", "bowtie2", "samtools"]
    elif execute_mode == "bounded_native_kraken2_pilot":
        required, optional = ["kraken2"], []
    else:
        required, optional = ["prefetch", "fasterq-dump", "kraken2", "bracken"], ["fastp", "bowtie2", "samtools"]
    commands = [command_status(cmd) for cmd in required + optional]
    missing_required = [c["command"] for c in commands if c["command"] in required and not c["available"]]
    if missing_required:
        errors.append("Required commands missing: " + ", ".join(missing_required))
    missing_optional = [c["command"] for c in commands if c["command"] in optional and not c["available"]]
    if missing_optional:
        warnings.append("Optional QC/host-removal commands missing: " + ", ".join(missing_optional))
    if execute_mode == "host_removal_amr_screen" and not host_index:
        errors.append("host_index is required for execute_mode=host_removal_amr_screen.")
    elif not host_index and execute_mode != "bounded_read_length_audit":
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

    if execute_mode == "readonly_inventory":
        if errors:
            return 2
        project_path = Path(str(params.get("project_path", "/mnt/disk1/db/kraken2/0714")))
        return readonly_inventory(out_dir, project_path, kraken2_db, bracken_db)
    if execute_mode == "bounded_external_pilot":
        if errors:
            return 2
        return bounded_external_pilot(out_dir, params, kraken2_db, bracken_db, threads)
    if execute_mode == "bounded_read_length_audit":
        if errors:
            return 2
        return bounded_read_length_audit(out_dir, params)
    if execute_mode == "bounded_taxonomy_method_benchmark":
        if errors:
            return 2
        return bounded_taxonomy_method_benchmark(out_dir, params, kraken2_db, bracken_db, threads)
    if execute_mode == "bounded_native_kraken2_pilot":
        if errors:
            return 2
        params["job_id"] = job_id
        return bounded_native_kraken2_pilot(out_dir, params, kraken2_db, threads)

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
    if execute_mode == "host_removal_amr_screen":
        if errors:
            return 2
        summary = execute_host_removal_amr(
            rows=rows,
            out_dir=out_dir,
            params=params,
            work_dir=work_dir,
            fastq_dir=fastq_dir,
            qc_dir=qc_dir,
            host_removed_dir=host_removed_dir,
            kraken_dir=kraken_dir,
            kraken2_db=kraken2_db,
            bracken_db=bracken_db,
            host_index=host_index,
            threads=threads,
        )
        return 0 if summary["final_status"] == "done" else 2
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
