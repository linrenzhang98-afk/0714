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
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_SEARCH_DIRS: list[Path] = []
CONDA_BIN = "/home/suma/anaconda3/bin/conda"
CLEAN_ENV_PREFIX = "/home/suma/anaconda3/envs/humann-shotgun-clean"
METAPHLAN_PACKAGE_SPEC = "metaphlan=4.1.1"
METAPHLAN_EXACT_VERSION = "4.1.1"
HUMANN_EXACT_VERSION = "3.9"
PYTHON_MAJOR_MINOR = "3.10"
METAPHLAN_DB_INDEX = "mpa_vJun23_CHOCOPhlAnSGB_202403"
METAPHLAN_DB_ROOT = "/mnt/disk1/db/metaphlan/vJun23"


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
    for directory in TOOL_SEARCH_DIRS:
        candidate = directory / command
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which(command) or ""


def env_command_path(functional_env_prefix: Path, command: str) -> str:
    candidate = functional_env_prefix / "bin" / command
    if candidate.exists() and os.access(candidate, os.X_OK):
        return str(candidate)
    return ""


def conda_path() -> str:
    return CONDA_BIN if Path(CONDA_BIN).exists() else command_path("conda")


def activate_functional_environment(functional_env_prefix: Path) -> None:
    dedicated_bin = functional_env_prefix / "bin"
    if dedicated_bin not in TOOL_SEARCH_DIRS:
        TOOL_SEARCH_DIRS.insert(0, dedicated_bin)

    current_path = os.environ.get("PATH", "")
    path_entries = [entry for entry in current_path.split(os.pathsep) if entry and entry != str(dedicated_bin)]
    os.environ["PATH"] = os.pathsep.join([str(dedicated_bin), *path_entries])


def command_healthy(command: str, args: list[str], log_path: Path, functional_env_prefix: Path | None = None) -> bool:
    path = env_command_path(functional_env_prefix, command) if functional_env_prefix is not None else command_path(command)
    if not path:
        append_log(log_path, f"health_check {command}=missing")
        return False
    result = run_command([path, *args], log_path, timeout=120)
    healthy = result.returncode == 0
    append_log(log_path, f"health_check {command}={str(healthy).lower()}")
    return healthy


def metaphlan_version_output_compatible(log_path: Path, functional_env_prefix: Path | None = None) -> bool:
    path = env_command_path(functional_env_prefix, "metaphlan") if functional_env_prefix is not None else command_path("metaphlan")
    if not path:
        append_log(log_path, "health_check metaphlan_humann_version_output=missing")
        return False

    result = run_command([path, "--version"], log_path, timeout=120)
    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    last_fields = output_lines[-1].split() if output_lines else []
    compatible = (
        result.returncode == 0
        and len(last_fields) > 2
        and re.match(r"^v?\d+\.\d+", last_fields[2]) is not None
    )
    append_log(log_path, f"health_check metaphlan_humann_version_output={str(compatible).lower()}")
    return compatible


def package_version_from_conda_list(functional_env_prefix: Path, package: str, log_path: Path) -> str:
    conda = conda_path()
    if not conda:
        append_log(log_path, "conda_list=missing_conda")
        return ""
    result = run_command([conda, "list", "-p", str(functional_env_prefix), package], log_path, timeout=120)
    if result.returncode != 0:
        return ""
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == package:
            return fields[1]
    return ""


def python_metadata_versions(functional_env_prefix: Path, log_path: Path) -> dict[str, str]:
    python = env_command_path(functional_env_prefix, "python")
    if not python:
        append_log(log_path, "python_metadata=missing_python")
        return {}
    code = "\n".join(
        [
            "import importlib.metadata, sys",
            "print('python=' + sys.version.split()[0])",
            "for name in ('humann', 'metaphlan'):",
            "    try:",
            "        print(name + '=' + importlib.metadata.version(name))",
            "    except Exception as exc:",
            "        print(name + '=ERROR:' + str(exc))",
        ]
    )
    result = run_command([python, "-c", code], log_path, timeout=120)
    versions: dict[str, str] = {}
    if result.returncode != 0:
        return versions
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.strip().split("=", 1)
            versions[key] = value
    return versions


def python_import_package(functional_env_prefix: Path, package: str, log_path: Path) -> bool:
    python = env_command_path(functional_env_prefix, "python")
    if not python:
        append_log(log_path, f"python_import_{package}=missing_python")
        return False
    result = run_command(
        [python, "-c", f"import {package}; print({package}.__file__)"],
        log_path,
        timeout=120,
    )
    ok = result.returncode == 0
    append_log(log_path, f"python_import_{package}={str(ok).lower()}")
    return ok


def repair_humann_module_if_needed(functional_env_prefix: Path, log_path: Path, timeout: int) -> None:
    if python_import_package(functional_env_prefix, "humann", log_path):
        return

    python = env_command_path(functional_env_prefix, "python")
    if not python:
        raise RuntimeError("Clean HUMAnN environment has no Python executable")

    append_log(log_path, "repair_humann_module=pip_no_deps")
    result = run_command(
        [
            python,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--no-deps",
            f"humann=={HUMANN_EXACT_VERSION}",
        ],
        log_path,
        timeout=timeout,
        env=clean_conda_cache_env(),
    )
    if result.returncode != 0:
        append_log(log_path, "repair_humann_module=ensurepip_then_retry")
        run_command([python, "-m", "ensurepip", "--upgrade"], log_path, timeout=300)
        result = run_command(
            [
                python,
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                f"humann=={HUMANN_EXACT_VERSION}",
            ],
            log_path,
            timeout=timeout,
            env=clean_conda_cache_env(),
        )
    if result.returncode != 0 or not python_import_package(functional_env_prefix, "humann", log_path):
        raise RuntimeError(f"HUMAnN Python module repair failed rc={result.returncode}")


def metaphlan_exact_version_installed(log_path: Path, functional_env_prefix: Path | None = None) -> bool:
    path = env_command_path(functional_env_prefix, "metaphlan") if functional_env_prefix is not None else command_path("metaphlan")
    if not path:
        append_log(log_path, "health_check metaphlan_exact_version=missing")
        return False

    result = run_command([path, "--version"], log_path, timeout=120)
    output = result.stdout + "\n" + result.stderr
    exact = result.returncode == 0 and f"MetaPhlAn version {METAPHLAN_EXACT_VERSION}" in output
    append_log(log_path, f"health_check metaphlan_exact_version={str(exact).lower()}")
    return exact


def functional_commands_healthy(log_path: Path, functional_env_prefix: Path | None = None) -> bool:
    checks = (
        ("humann", ["--version"]),
        ("humann_databases", ["--help"]),
        ("diamond", ["version"]),
        ("bowtie2", ["--version"]),
    )
    results = [command_healthy(command, args, log_path, functional_env_prefix) for command, args in checks]
    return all(results) and metaphlan_version_output_compatible(log_path, functional_env_prefix)


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
            f"- MetaPhlAn DB ready: {db_status.get('metaphlan_db_ready', False)}",
            f"- MetaPhlAn DB root: `{db_status.get('metaphlan_db_root', '')}`",
            f"- MetaPhlAn DB index: `{db_status.get('metaphlan_index', '')}`",
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


def clean_env_versions_ok(functional_env_prefix: Path, log_path: Path) -> bool:
    if not functional_commands_healthy(log_path, functional_env_prefix):
        return False
    conda_metaphlan = package_version_from_conda_list(functional_env_prefix, "metaphlan", log_path)
    conda_humann = package_version_from_conda_list(functional_env_prefix, "humann", log_path)
    metadata = python_metadata_versions(functional_env_prefix, log_path)
    checks = {
        "python": metadata.get("python", "").startswith(f"{PYTHON_MAJOR_MINOR}."),
        "humann_conda": conda_humann.startswith(HUMANN_EXACT_VERSION),
        "humann_metadata": metadata.get("humann", "").startswith(HUMANN_EXACT_VERSION),
        "metaphlan_conda": conda_metaphlan == METAPHLAN_EXACT_VERSION,
        "metaphlan_metadata": metadata.get("metaphlan") == METAPHLAN_EXACT_VERSION,
        "metaphlan_cli": metaphlan_exact_version_installed(log_path, functional_env_prefix),
    }
    for key, value in checks.items():
        append_log(log_path, f"health_check {key}={str(value).lower()}")
    return all(checks.values())


def write_persistent_pins(functional_env_prefix: Path, log_path: Path) -> None:
    pin_path = functional_env_prefix / "conda-meta" / "pinned"
    pin_path.parent.mkdir(parents=True, exist_ok=True)
    pin_path.write_text(
        "\n".join(
            [
                f"python={PYTHON_MAJOR_MINOR}",
                f"humann={HUMANN_EXACT_VERSION}",
                f"metaphlan={METAPHLAN_EXACT_VERSION}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    append_log(log_path, f"persistent_pins_written={pin_path}")


def clean_conda_cache_env() -> dict[str, str]:
    env = os.environ.copy()
    env["CONDA_PKGS_DIRS"] = str(Path(".runner_state") / "conda_pkgs_humann_clean")
    return env


def conda_create_extra_args(conda: str, log_path: Path) -> list[str]:
    result = run_command([conda, "create", "--help"], log_path, timeout=120, env=clean_conda_cache_env())
    if result.returncode == 0 and "--no-use-local" in result.stdout:
        append_log(log_path, "conda_create_supports_no_use_local=true")
        return ["--no-use-local"]
    append_log(log_path, "conda_create_supports_no_use_local=false")
    return []


def remove_clean_environment(conda: str, functional_env_prefix: Path, log_path: Path, timeout: int) -> None:
    if str(functional_env_prefix) != CLEAN_ENV_PREFIX:
        raise RuntimeError(f"Refusing to remove non-clean HUMAnN environment: {functional_env_prefix}")
    append_log(log_path, f"removing incomplete clean HUMAnN environment at {functional_env_prefix}")
    result = run_command(
        [conda, "env", "remove", "-p", str(functional_env_prefix), "-y"],
        log_path,
        timeout=timeout,
        env=clean_conda_cache_env(),
    )
    if result.returncode != 0 and functional_env_prefix.exists():
        raise RuntimeError(f"Failed to remove incomplete clean HUMAnN environment rc={result.returncode}")


def install_humann_if_needed(log_path: Path, functional_env_prefix: Path, timeout: int) -> None:
    conda = conda_path()
    if not conda:
        raise RuntimeError("Conda is unavailable; clean HUMAnN environment cannot be created")

    activate_functional_environment(functional_env_prefix)
    if functional_env_prefix.exists():
        try:
            repair_humann_module_if_needed(functional_env_prefix, log_path, timeout)
        except RuntimeError as exc:
            append_log(log_path, f"existing_clean_env_repair_failed={exc}")
    if functional_env_prefix.exists() and clean_env_versions_ok(functional_env_prefix, log_path):
        write_persistent_pins(functional_env_prefix, log_path)
        return

    if functional_env_prefix.exists():
        remove_clean_environment(conda, functional_env_prefix, log_path, timeout)

    append_log(log_path, f"creating clean HUMAnN environment at {functional_env_prefix}")
    result = run_command(
        [
            conda,
            "create",
            "-p",
            str(functional_env_prefix),
            "-y",
            "--solver",
            "classic",
            "--override-channels",
            "--strict-channel-priority",
            "-c",
            "conda-forge",
            "-c",
            "bioconda",
            *conda_create_extra_args(conda, log_path),
            f"python={PYTHON_MAJOR_MINOR}",
            f"humann={HUMANN_EXACT_VERSION}",
            METAPHLAN_PACKAGE_SPEC,
        ],
        log_path,
        timeout=timeout,
        env=clean_conda_cache_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Clean HUMAnN environment creation failed rc={result.returncode}")
    activate_functional_environment(functional_env_prefix)
    repair_humann_module_if_needed(functional_env_prefix, log_path, timeout)
    if not clean_env_versions_ok(functional_env_prefix, log_path):
        raise RuntimeError("Clean HUMAnN environment failed strict version health check")
    write_persistent_pins(functional_env_prefix, log_path)


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


def db_status(db_root: Path, metaphlan_db_root: Path | None = None, metaphlan_index: str = METAPHLAN_DB_INDEX) -> dict[str, Any]:
    chocophlan = db_root / "chocophlan"
    uniref = db_root / "uniref"
    metaphlan_db_root = metaphlan_db_root or Path(METAPHLAN_DB_ROOT)
    return {
        "db_root": str(db_root),
        "chocophlan_ready": has_db_files(chocophlan, (".ffn.gz", ".ffn")),
        "uniref_ready": has_db_files(uniref, (".dmnd", ".faa.gz", ".faa")),
        "utility_mapping_ready": (db_root / "utility_mapping").exists() and any((db_root / "utility_mapping").iterdir()),
        "chocophlan": str(chocophlan),
        "uniref": str(uniref),
        "metaphlan_db_root": str(metaphlan_db_root),
        "metaphlan_index": metaphlan_index,
        "metaphlan_db_ready": metaphlan_db_files_ready(metaphlan_db_root, metaphlan_index),
    }


def metaphlan_db_files_ready(metaphlan_db_root: Path, index: str) -> bool:
    required_suffixes = (".1.bt2l", ".2.bt2l", ".3.bt2l", ".4.bt2l", ".rev.1.bt2l", ".rev.2.bt2l")
    return all(file_nonempty(metaphlan_db_root / f"{index}{suffix}") for suffix in required_suffixes)


def ensure_metaphlan_db(functional_env_prefix: Path, metaphlan_db_root: Path, index: str, log_path: Path, timeout: int) -> None:
    metaphlan_db_root.mkdir(parents=True, exist_ok=True)
    if metaphlan_db_files_ready(metaphlan_db_root, index):
        append_log(log_path, f"metaphlan_db_ready={metaphlan_db_root} index={index}")
        return

    metaphlan = env_command_path(functional_env_prefix, "metaphlan")
    if not metaphlan:
        raise RuntimeError("MetaPhlAn command missing from clean environment; cannot install marker database")
    result = run_command(
        [
            metaphlan,
            "--install",
            "--index",
            index,
            "--bowtie2db",
            str(metaphlan_db_root),
        ],
        log_path,
        timeout=timeout,
    )
    if result.returncode != 0 or not metaphlan_db_files_ready(metaphlan_db_root, index):
        raise RuntimeError(f"MetaPhlAn vJun23 marker database incomplete or install failed rc={result.returncode}")


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


def select_smoke_fastq(rows: list[dict[str, Any]]) -> tuple[str, Path]:
    for row in rows:
        run = str(row.get("run", ""))
        fastq = Path(str(row.get("host_removed_fastq", "")))
        if run and file_nonempty(fastq):
            return run, fastq
    raise RuntimeError("No existing non-empty host-removed FASTQ is available for smoke tests")


def metaphlan_smoke_ready(result_dir: Path) -> bool:
    output = result_dir / "smoke_tests" / "metaphlan_smoke_test.tsv"
    return file_nonempty(output)


def humann_smoke_ready(result_dir: Path, run: str) -> bool:
    smoke_dir = result_dir / "smoke_tests" / "humann"
    return (
        file_nonempty(smoke_dir / f"{run}_genefamilies.tsv")
        and file_nonempty(smoke_dir / f"{run}_pathabundance.tsv")
        and file_nonempty(smoke_dir / f"{run}_pathcoverage.tsv")
    )


def run_metaphlan_smoke_test(
    functional_env_prefix: Path,
    result_dir: Path,
    rows: list[dict[str, Any]],
    metaphlan_db_root: Path,
    index: str,
    log_path: Path,
    threads: int,
    timeout: int,
) -> tuple[str, Path]:
    run, fastq = select_smoke_fastq(rows)
    smoke_dir = result_dir / "smoke_tests"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    output = smoke_dir / "metaphlan_smoke_test.tsv"
    if file_nonempty(output):
        append_log(log_path, f"metaphlan_smoke_test=reusing_existing output={output}")
        return run, fastq
    metaphlan = env_command_path(functional_env_prefix, "metaphlan")
    if not metaphlan:
        raise RuntimeError("MetaPhlAn command missing from clean environment")
    result = run_command(
        [
            metaphlan,
            str(fastq),
            "--input_type",
            "fastq",
            "--bowtie2db",
            str(metaphlan_db_root),
            "--index",
            index,
            "--nproc",
            str(threads),
            "-o",
            str(output),
        ],
        log_path,
        timeout=timeout,
    )
    append_log(log_path, f"metaphlan_smoke_test_index={index}")
    if result.returncode != 0 or not file_nonempty(output):
        raise RuntimeError(f"MetaPhlAn smoke test failed rc={result.returncode}")
    append_log(log_path, f"metaphlan_smoke_test=pass run={run} output={output}")
    return run, fastq


def run_humann_smoke_test(
    functional_env_prefix: Path,
    result_dir: Path,
    run: str,
    fastq: Path,
    current_db_status: dict[str, Any],
    metaphlan_db_root: Path,
    index: str,
    log_path: Path,
    threads: int,
    timeout: int,
) -> None:
    if humann_smoke_ready(result_dir, run):
        append_log(log_path, f"humann_smoke_test=reusing_existing run={run}")
        return
    humann = env_command_path(functional_env_prefix, "humann")
    if not humann:
        raise RuntimeError("HUMAnN command missing from clean environment")
    smoke_dir = result_dir / "smoke_tests" / "humann"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            humann,
            "--input",
            str(fastq),
            "--output",
            str(smoke_dir),
            "--threads",
            str(threads),
            "--nucleotide-database",
            str(Path(current_db_status["chocophlan"])),
            "--protein-database",
            str(Path(current_db_status["uniref"])),
            "--metaphlan-options",
            f"--bowtie2db {metaphlan_db_root} --index {index}",
        ],
        log_path,
        timeout=timeout,
    )
    if result.returncode != 0 or not humann_smoke_ready(result_dir, run):
        raise RuntimeError(f"HUMAnN single-sample smoke test failed rc={result.returncode}")
    append_log(log_path, f"humann_smoke_test=pass run={run} output={smoke_dir}")


def setup_gate_passed(result_dir: Path) -> bool:
    marker = result_dir / "setup_ready.ok"
    return file_nonempty(marker)


def mark_setup_ready(result_dir: Path, run: str, fastq: Path, metaphlan_db_root: Path, index: str) -> None:
    marker = result_dir / "setup_ready.ok"
    marker.write_text(
        "\n".join(
            [
                f"generated_at={utc_now()}",
                f"smoke_run={run}",
                f"smoke_fastq={fastq}",
                f"metaphlan_db_root={metaphlan_db_root}",
                f"metaphlan_index={index}",
                "",
            ]
        ),
        encoding="utf-8",
    )


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
    parser.add_argument("--functional-env-prefix", default=CLEAN_ENV_PREFIX)
    parser.add_argument("--metaphlan-db-root", default=METAPHLAN_DB_ROOT)
    parser.add_argument("--metaphlan-index", default=METAPHLAN_DB_INDEX)
    parser.add_argument("--auto-install", action="store_true")
    parser.add_argument("--auto-download-dbs", action="store_true")
    args = parser.parse_args()

    result_dir = Path(args.out_dir)
    public_dir = Path(args.public_dir)
    db_root = Path(args.db_root)
    functional_env_prefix = Path(args.functional_env_prefix)
    metaphlan_db_root = Path(args.metaphlan_db_root)
    activate_functional_environment(functional_env_prefix)
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
    if str(functional_env_prefix) != CLEAN_ENV_PREFIX:
        reason = f"Refusing unsafe HUMAnN environment: {functional_env_prefix}; expected {CLEAN_ENV_PREFIX}"
        write_public_status(
            public_dir,
            result_dir,
            "blocked_setup",
            reason,
            rows,
            tool_status,
            db_status(db_root, metaphlan_db_root, args.metaphlan_index),
        )
        return 2
    write_public_status(
        public_dir,
        result_dir,
        "initializing",
        "Functional profiling worker started.",
        rows,
        tool_status,
        db_status(db_root, metaphlan_db_root, args.metaphlan_index),
    )

    try:
        if args.auto_install:
            install_humann_if_needed(log_path, functional_env_prefix, args.install_timeout_seconds)
        tool_status = {
            "humann": env_command_path(functional_env_prefix, "humann"),
            "humann_databases": env_command_path(functional_env_prefix, "humann_databases"),
            "humann_join_tables": env_command_path(functional_env_prefix, "humann_join_tables"),
            "humann_renorm_table": env_command_path(functional_env_prefix, "humann_renorm_table"),
            "metaphlan": env_command_path(functional_env_prefix, "metaphlan"),
            "diamond": env_command_path(functional_env_prefix, "diamond"),
            "bowtie2": env_command_path(functional_env_prefix, "bowtie2"),
        }
        if not tool_status["humann"]:
            raise RuntimeError("HUMAnN is unavailable after tool check/install stage")
        if args.auto_download_dbs:
            download_humann_dbs(db_root, log_path, args.db_timeout_seconds)
        current_db_status = db_status(db_root, metaphlan_db_root, args.metaphlan_index)
        if not current_db_status["chocophlan_ready"] or not current_db_status["uniref_ready"]:
            raise RuntimeError("HUMAnN databases are not ready after database check/download stage")
        ensure_metaphlan_db(functional_env_prefix, metaphlan_db_root, args.metaphlan_index, log_path, args.db_timeout_seconds)
        if not setup_gate_passed(result_dir):
            smoke_run, smoke_fastq = run_metaphlan_smoke_test(
                functional_env_prefix,
                result_dir,
                rows,
                metaphlan_db_root,
                args.metaphlan_index,
                log_path,
                args.threads,
                args.per_command_timeout_seconds,
            )
            run_humann_smoke_test(
                functional_env_prefix,
                result_dir,
                smoke_run,
                smoke_fastq,
                current_db_status,
                metaphlan_db_root,
                args.metaphlan_index,
                log_path,
                args.threads,
                args.per_command_timeout_seconds,
            )
            mark_setup_ready(result_dir, smoke_run, smoke_fastq, metaphlan_db_root, args.metaphlan_index)
            write_public_status(
                public_dir,
                result_dir,
                "setup_ready",
                "Clean HUMAnN/MetaPhlAn environment and smoke tests passed; formal 30-sample run is released for the next launcher pass.",
                rows,
                tool_status,
                current_db_status,
            )
            return 0
    except Exception as exc:  # noqa: BLE001 - report blocker for unattended repair.
        write_public_status(
            public_dir,
            result_dir,
            "blocked_setup",
            str(exc),
            rows,
            tool_status,
            db_status(db_root, metaphlan_db_root, args.metaphlan_index),
        )
        return 2

    humann = tool_status["humann"]
    current_db_status = db_status(db_root, metaphlan_db_root, args.metaphlan_index)
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
                "--metaphlan-options",
                f"--bowtie2db {metaphlan_db_root} --index {args.metaphlan_index}",
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
