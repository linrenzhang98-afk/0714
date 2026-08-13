#!/usr/bin/env python3
"""Production HUMAnN 3.9 route for the fixed 30-sample PRJNA1056765 cohort.

The route reuses the Bowtie2 index produced by the successful SRR27343490
short-read smoke test and analyzes exactly the remaining 29 host-removed
FASTQ files.  It deliberately bypasses MetaPhlAn/raw-read prescreening and
Bowtie2 index construction.  It never installs software, repairs conda
environments, downloads databases, or changes cohort membership.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_SAMPLE_COUNT = 30
EXPECTED_REMAINING_COUNT = 29
FINAL_SUFFIXES = ("genefamilies.tsv", "pathabundance.tsv", "pathcoverage.tsv")
STATUS_FIELDS = [
    "run",
    "pathogen_group",
    "status",
    "error",
    "host_removed_fastq",
    "sample_dir",
    "genefamilies",
    "pathabundance",
    "pathcoverage",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATUS_FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(args: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=120, env=env)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}")
    return (result.stdout + result.stderr).strip()


def runtime_env(cfg: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    ordered = [cfg["bowtie2_dir"], cfg["humann_env_bin"], "/usr/local/bin", "/usr/bin", "/bin"]
    env["PATH"] = os.pathsep.join(ordered)
    return env


def version_gate(cfg: dict[str, Any]) -> dict[str, str]:
    env = runtime_env(cfg)
    tools = {
        "humann": (Path(cfg["humann"]), ["--version"]),
        "bowtie2": (Path(cfg["bowtie2_dir"]) / "bowtie2", ["--version"]),
        "bowtie2_build": (Path(cfg["bowtie2_dir"]) / "bowtie2-build", ["--version"]),
        "diamond": (Path(cfg["humann_env_bin"]) / "diamond", ["version"]),
    }
    versions: dict[str, str] = {}
    for name, (path, args) in tools.items():
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RuntimeError(f"required existing executable missing or not executable: {path}")
        versions[name] = command_output([str(path), *args], env=env).splitlines()[0]
    required = cfg["required_versions"]
    if required["humann"] not in versions["humann"]:
        raise RuntimeError(f"HUMAnN version mismatch: {versions['humann']}")
    if required["bowtie2"] not in versions["bowtie2"]:
        raise RuntimeError(f"Bowtie2 version mismatch: {versions['bowtie2']}")
    if required["bowtie2"] not in versions["bowtie2_build"]:
        raise RuntimeError(f"bowtie2-build version mismatch: {versions['bowtie2_build']}")
    if required["diamond"] not in versions["diamond"]:
        raise RuntimeError(f"DIAMOND version mismatch: {versions['diamond']}")
    return versions


def cohort(cfg: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    matrix_rows = read_tsv(Path(cfg["cohort_matrix"]))
    status_rows = read_tsv(Path(cfg["run_status"]))
    if len(matrix_rows) != EXPECTED_SAMPLE_COUNT or len(status_rows) != EXPECTED_SAMPLE_COUNT:
        raise RuntimeError(
            f"cohort is pinned to 30 samples; matrix={len(matrix_rows)} run_status={len(status_rows)}"
        )
    matrix_ids = [row["run"] for row in matrix_rows]
    status_ids = [row["run"] for row in status_rows]
    if len(set(matrix_ids)) != EXPECTED_SAMPLE_COUNT or len(set(status_ids)) != EXPECTED_SAMPLE_COUNT:
        raise RuntimeError("cohort contains duplicate run IDs")
    if set(matrix_ids) != set(status_ids):
        raise RuntimeError("cohort matrix and host-AMR run status membership differ")
    smoke = cfg["smoke_sample"]
    if smoke not in set(matrix_ids):
        raise RuntimeError(f"smoke sample is not in the fixed cohort: {smoke}")
    remaining = [run for run in matrix_ids if run != smoke]
    if len(remaining) != EXPECTED_REMAINING_COUNT:
        raise RuntimeError(f"expected exactly 29 non-smoke samples, found {len(remaining)}")
    if int(cfg["remaining_sample_cap"]) != EXPECTED_REMAINING_COUNT:
        raise RuntimeError("remaining_sample_cap must stay pinned to 29")
    return matrix_rows, {row["run"]: row for row in status_rows}


def find_index_prefix(directory: Path) -> tuple[str, list[Path]]:
    if not directory.is_dir():
        raise RuntimeError(f"shared index directory missing: {directory}")
    for ext in (".1.bt2", ".1.bt2l"):
        for first in sorted(directory.glob(f"*{ext}")):
            prefix = str(first)[: -len(ext)]
            shard_ext = ".bt2l" if ext.endswith("bt2l") else ".bt2"
            expected = [
                Path(prefix + f".1{shard_ext}"),
                Path(prefix + f".2{shard_ext}"),
                Path(prefix + f".3{shard_ext}"),
                Path(prefix + f".4{shard_ext}"),
                Path(prefix + f".rev.1{shard_ext}"),
                Path(prefix + f".rev.2{shard_ext}"),
            ]
            if all(path.is_file() and path.stat().st_size > 0 for path in expected):
                return prefix, expected
    raise RuntimeError(f"no complete six-shard Bowtie2 index found in {directory}")


def final_paths(sample_dir: Path, run: str) -> dict[str, Path]:
    return {
        "genefamilies": sample_dir / f"{run}_genefamilies.tsv",
        "pathabundance": sample_dir / f"{run}_pathabundance.tsv",
        "pathcoverage": sample_dir / f"{run}_pathcoverage.tsv",
    }


def outputs_complete(paths: dict[str, Path]) -> bool:
    return all(path.is_file() and path.stat().st_size > 0 for path in paths.values())


def preserve_smoke(cfg: dict[str, Any], output_root: Path) -> dict[str, Path]:
    run = cfg["smoke_sample"]
    source = Path(cfg["smoke_output_dir"])
    if not source.is_dir():
        raise RuntimeError(f"validated smoke output directory missing: {source}")
    source_paths = final_paths(source, run)
    if not outputs_complete(source_paths):
        raise RuntimeError("validated smoke final outputs are incomplete")
    target_dir = output_root / run
    target_dir.mkdir(parents=True, exist_ok=True)
    target_paths = final_paths(target_dir, run)
    for key, src in source_paths.items():
        dst = target_paths[key]
        if dst.exists():
            if not dst.is_file() or dst.stat().st_size == 0 or sha256(dst) != sha256(src):
                raise RuntimeError(f"existing smoke target conflicts with validated output: {dst}")
        else:
            shutil.copy2(src, dst)
    return target_paths


def humann_command(cfg: dict[str, Any], fastq: Path, sample_dir: Path) -> list[str]:
    return [
        cfg["humann"],
        "--input",
        str(fastq),
        "--output",
        str(sample_dir),
        "--threads",
        str(cfg["threads"]),
        "--nucleotide-database",
        cfg["shared_index_dir"],
        "--bypass-nucleotide-index",
        "--protein-database",
        cfg["uniref90"],
        "--resume",
    ]


def row_for(run: str, source: dict[str, str], sample_dir: Path, status: str, error: str = "") -> dict[str, str]:
    paths = final_paths(sample_dir, run)
    return {
        "run": run,
        "pathogen_group": source.get("pathogen_group", ""),
        "status": status,
        "error": error,
        "host_removed_fastq": source.get("host_removed_fastq", ""),
        "sample_dir": str(sample_dir),
        "genefamilies": str(paths["genefamilies"]) if paths["genefamilies"].exists() else "",
        "pathabundance": str(paths["pathabundance"]) if paths["pathabundance"].exists() else "",
        "pathcoverage": str(paths["pathcoverage"]) if paths["pathcoverage"].exists() else "",
    }


def publish(public_dir: Path, rows: list[dict[str, str]], cfg: dict[str, Any], versions: dict[str, str], state: str, reason: str) -> None:
    write_tsv(public_dir / "run_status.tsv", rows)
    counts = {name: sum(row["status"] == name for row in rows) for name in ("done", "running", "failed", "queued")}
    summary = {
        "generated_at": now(),
        "state": state,
        "reason": reason,
        "route": "short_read_shared_index",
        "method": "Bracken-derived 30-sample joint ChocoPhlAn selection; MetaPhlAn raw-read prescreen bypassed",
        "sample_count": EXPECTED_SAMPLE_COUNT,
        "done_count": counts["done"],
        "failed_count": counts["failed"],
        "running_count": counts["running"],
        "queued_count": counts["queued"],
        "smoke_sample": cfg["smoke_sample"],
        "shared_index_dir": cfg["shared_index_dir"],
        "joint_profile": cfg["joint_profile"],
        "threads_per_sample": cfg["threads"],
        "versions": versions,
    }
    public_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (public_dir / "summary.md").write_text(
        "\n".join(
            [
                "# PRJNA1056765 HUMAnN short-read functional profile",
                "",
                f"- State: `{state}`",
                f"- Reason: {reason}",
                f"- Progress: {counts['done']}/30 done, {counts['running']} running, {counts['failed']} failed, {counts['queued']} queued",
                "- Route: shared Bowtie2 index from the validated SRR27343490 smoke test",
                "- MetaPhlAn raw-read prescreen: bypassed",
                "- Database downloads/environment rebuilds: disabled by design",
                "",
            ]
        ),
        encoding="utf-8",
    )


def provenance(cfg: dict[str, Any], versions: dict[str, str], shards: list[Path], public_dir: Path) -> None:
    profile = Path(cfg["joint_profile"])
    if not profile.is_file() or profile.stat().st_size == 0:
        raise RuntimeError(f"validated joint profile missing: {profile}")
    data = {
        "generated_at": now(),
        "route": "short_read_shared_index",
        "cohort_matrix": cfg["cohort_matrix"],
        "cohort_matrix_sha256": sha256(Path(cfg["cohort_matrix"])),
        "host_amr_run_status": cfg["run_status"],
        "host_amr_run_status_sha256": sha256(Path(cfg["run_status"])),
        "smoke_sample": cfg["smoke_sample"],
        "smoke_output_dir": cfg["smoke_output_dir"],
        "joint_profile": str(profile),
        "joint_profile_sha256": sha256(profile),
        "shared_index_dir": cfg["shared_index_dir"],
        "shared_index_shards": [{"name": p.name, "size": p.stat().st_size} for p in shards],
        "taxonomy_policy": "validated 30-sample joint profile; no fuzzy taxonomic remapping in production runner",
        "metaphlan_raw_read_prescreen": False,
        "index_rebuilt_per_sample": False,
        "software_or_database_downloads": False,
        "environment_rebuild": False,
        "versions": versions,
    }
    public_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "method_provenance.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/prjna1056765_humann_short_read_production.json"))
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.preflight == args.execute:
        parser.error("choose exactly one of --preflight or --execute")

    cfg = load_json(args.config)
    matrix_rows, source_status = cohort(cfg)
    output_root = Path(cfg["output_root"])
    public_dir = Path(cfg["public_status"])
    output_root.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    versions = version_gate(cfg)
    _, shards = find_index_prefix(Path(cfg["shared_index_dir"]))
    if not Path(cfg["uniref90"]).is_dir():
        raise RuntimeError(f"existing UniRef database directory missing: {cfg['uniref90']}")
    provenance(cfg, versions, shards, public_dir)

    smoke_paths = preserve_smoke(cfg, output_root)
    smoke = cfg["smoke_sample"]
    rows_by_run: dict[str, dict[str, str]] = {}
    for row in matrix_rows:
        run = row["run"]
        sample_dir = output_root / run
        if run == smoke:
            rows_by_run[run] = row_for(run, source_status[run], sample_dir, "done")
        elif outputs_complete(final_paths(sample_dir, run)):
            rows_by_run[run] = row_for(run, source_status[run], sample_dir, "done")
        else:
            rows_by_run[run] = row_for(run, source_status[run], sample_dir, "queued")

    ordered_rows = lambda: [rows_by_run[row["run"]] for row in matrix_rows]
    publish(public_dir, ordered_rows(), cfg, versions, "ready" if args.preflight else "running", "preflight passed" if args.preflight else "production worker started")
    if args.preflight:
        print(json.dumps({"state": "ready", "remaining": sum(r["status"] != "done" for r in ordered_rows())}))
        return 0

    env = runtime_env(cfg)
    for row in matrix_rows:
        run = row["run"]
        if run == smoke or rows_by_run[run]["status"] == "done":
            continue
        fastq = Path(source_status[run]["host_removed_fastq"])
        if not fastq.is_file() or fastq.stat().st_size == 0:
            rows_by_run[run] = row_for(run, source_status[run], output_root / run, "failed", "host-removed FASTQ missing or empty")
            publish(public_dir, ordered_rows(), cfg, versions, "blocked_or_failed", f"missing FASTQ for {run}")
            return 2

        sample_dir = output_root / run
        sample_dir.mkdir(parents=True, exist_ok=True)
        rows_by_run[run] = row_for(run, source_status[run], sample_dir, "running")
        publish(public_dir, ordered_rows(), cfg, versions, "running", f"HUMAnN running for {run}")
        log_path = sample_dir / "humann.production.log"
        cmd = humann_command(cfg, fastq, sample_dir)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"{now()}\tRUN {' '.join(cmd)}\n")
            log.flush()
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False, env=env)
            log.write(f"{now()}\tRETURN_CODE {result.returncode}\n")

        if result.returncode != 0 or not outputs_complete(final_paths(sample_dir, run)):
            error = f"HUMAnN rc={result.returncode}; final outputs complete={outputs_complete(final_paths(sample_dir, run))}"
            rows_by_run[run] = row_for(run, source_status[run], sample_dir, "failed", error)
            publish(public_dir, ordered_rows(), cfg, versions, "blocked_or_failed", f"production stopped at {run}: {error}")
            return result.returncode or 2

        rows_by_run[run] = row_for(run, source_status[run], sample_dir, "done")
        publish(public_dir, ordered_rows(), cfg, versions, "running", f"completed {run}; continuing")

    if not all(row["status"] == "done" for row in ordered_rows()):
        publish(public_dir, ordered_rows(), cfg, versions, "blocked_or_failed", "worker ended before all 30 samples were complete")
        return 2
    publish(public_dir, ordered_rows(), cfg, versions, "done", "all 30 samples complete")
    print(json.dumps({"state": "done", "done": 30}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
