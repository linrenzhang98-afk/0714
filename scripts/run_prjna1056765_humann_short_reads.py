#!/usr/bin/env python3
"""Bounded HUMAnN 3.9 short-read validation for exactly two PRJNA1056765 samples.

This route is deliberately independent of the legacy MetaPhlAn-first worker.  It
does not install, download, repair, or configure software/databases.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILE_HEADER = ["#clade_name", "NCBI_tax_id", "relative_abundance", "additional_species"]
EXPECTED_SAMPLE_COUNT = 30
MAX_VALIDATION_SAMPLES = 2


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(args: list[str]) -> str:
    result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=120)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}")
    return (result.stdout + result.stderr).strip()


def version_gate(cfg: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for tool in ("humann", "bowtie2", "bowtie2_build", "diamond"):
        path = Path(cfg[tool])
        if not path.is_file():
            raise RuntimeError(f"required existing executable is missing: {path}")
        versions[tool] = command_output([str(path), "--version"]).splitlines()[0]
    if cfg["required_versions"]["humann"] not in versions["humann"]:
        raise RuntimeError(f"HUMAnN version mismatch: {versions['humann']}")
    if cfg["required_versions"]["bowtie2"] not in versions["bowtie2"]:
        raise RuntimeError(f"Bowtie2 version mismatch: {versions['bowtie2']}")
    return versions


def cohort(cfg: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    matrix_path = Path(cfg["cohort_matrix"])
    matrix_rows = read_tsv(matrix_path)
    if len(matrix_rows) != EXPECTED_SAMPLE_COUNT:
        raise RuntimeError(f"cohort matrix must contain exactly 30 rows, found {len(matrix_rows)}")
    if len({row["run"] for row in matrix_rows}) != EXPECTED_SAMPLE_COUNT:
        raise RuntimeError("cohort matrix run IDs are not unique")
    status = {row["run"]: row for row in read_tsv(Path(cfg["run_status"]))}
    matrix = {row["run"]: row for row in matrix_rows}
    if set(matrix) != set(status):
        raise RuntimeError("30-sample matrix and run-status membership differ; refusing cohort change")
    selected = cfg["validation_samples"]
    if len(selected) != MAX_VALIDATION_SAMPLES or len(set(selected)) != MAX_VALIDATION_SAMPLES:
        raise RuntimeError("validation_samples must contain exactly two unique IDs")
    if cfg["smoke_sample"] in selected or not set(selected) <= set(matrix):
        raise RuntimeError("validation IDs must be cohort members and exclude the smoke sample")
    return matrix_rows, status


def parse_bracken(path: Path) -> list[dict[str, str]]:
    rows = read_tsv(path)
    required = {"name", "taxonomy_id", "fraction_total_reads"}
    if not rows or not required <= set(rows[0]):
        raise RuntimeError(f"invalid Bracken species file: {path}")
    return rows


def clade_name(name: str) -> str:
    # Syntax-only serialization, never a taxonomic lookup or fuzzy remap.
    exact = name.strip()
    if not exact or "|" in exact or "\t" in exact:
        raise RuntimeError(f"unsafe/unrepresentable exact taxonomy name: {name!r}")
    # A species-only MetaPhlAn clade avoids inventing higher ranks (the cohort
    # includes non-bacterial taxa) while retaining the exact Bracken label.
    return f"s__{exact.replace(' ', '_')}"


def profile_rows(bracken_rows: list[dict[str, str]], threshold_percent: float) -> list[list[str]]:
    output: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    for row in bracken_rows:
        percent = float(row["fraction_total_reads"]) * 100.0
        # HUMAnN semantics are strictly greater-than the percent threshold.
        if percent <= threshold_percent:
            continue
        key = (row["name"].strip(), row["taxonomy_id"].strip())
        if key in seen:
            raise RuntimeError(f"duplicate exact Bracken taxonomy: {key}")
        seen.add(key)
        output.append([clade_name(key[0]), key[1], f"{percent:.10g}", ""])
    return sorted(output, key=lambda row: (-float(row[2]), row[0], row[1]))


def write_profile(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(PROFILE_HEADER)
        writer.writerows(rows)


def prepare(cfg: dict[str, Any], out: Path) -> dict[str, Any]:
    matrix_rows, status = cohort(cfg)
    threshold = float(cfg["prescreen_threshold_percent"])
    if threshold != 0.01:
        raise RuntimeError("prescreen threshold is pinned to 0.01 percent")
    sample_profiles: dict[str, list[list[str]]] = {}
    joint: dict[tuple[str, str], list[str]] = {}
    for matrix_row in matrix_rows:
        run = matrix_row["run"]
        bracken_path = Path(status[run]["bracken"])
        rows = profile_rows(parse_bracken(bracken_path), threshold)
        if run in cfg["validation_samples"]:
            sample_profiles[run] = rows
        for row in rows:
            key = (row[0], row[1])
            if key not in joint or float(row[2]) > float(joint[key][2]):
                joint[key] = row
    profiles = out / "profiles"
    write_profile(profiles / "joint_union_30_samples.tsv", sorted(joint.values(), key=lambda x: (-float(x[2]), x[0])))
    for run, rows in sample_profiles.items():
        write_profile(profiles / f"{run}.sample_specific.tsv", rows)
    provenance = {
        "generated_at": now(), "state": "prepared_not_executed",
        "cohort_count": len(matrix_rows), "cohort_ids": [r["run"] for r in matrix_rows],
        "validation_samples": cfg["validation_samples"], "smoke_sample_preserved": cfg["smoke_sample"],
        "prescreen_threshold_percent": threshold, "profile_columns": PROFILE_HEADER,
        "taxonomy_policy": "exact Bracken name/taxid only; formatting spaces as underscores is serialization, not remapping",
        "matrix_sha256": sha256(Path(cfg["cohort_matrix"])),
        "run_status_sha256": sha256(Path(cfg["run_status"])),
        "metaphlan_raw_read_prescreen": False,
        "downstream_results_claimed": False,
    }
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return provenance


def index_shards(directory: Path) -> list[Path]:
    return sorted([*directory.glob("*_bowtie2_index*.bt2"), *directory.glob("*_bowtie2_index*.bt2l")])


def run_humann(cfg: dict[str, Any], out: Path, execute: bool) -> list[list[str]]:
    versions = version_gate(cfg)
    for db_key in ("chocophlan", "uniref90"):
        if not Path(cfg[db_key]).is_dir():
            raise RuntimeError(f"existing database path missing: {cfg[db_key]}")
    commands: list[list[str]] = []
    status = {row["run"]: row for row in read_tsv(Path(cfg["run_status"]))}
    joint_index: Path | None = None
    for run in cfg["validation_samples"]:
        fastq = Path(status[run]["host_removed_fastq"])
        if not fastq.is_file() or fastq.stat().st_size == 0:
            raise RuntimeError(f"host-removed FASTQ missing: {fastq}")
        for mode in ("joint_union", "sample_specific"):
            target = out / "humann" / run / mode
            if target.exists() and any(target.iterdir()):
                raise RuntimeError(f"refusing to overwrite existing validation output: {target}")
            profile = out / "profiles" / ("joint_union_30_samples.tsv" if mode == "joint_union" else f"{run}.sample_specific.tsv")
            cmd = [cfg["humann"], "--input", str(fastq), "--output", str(target), "--threads", "4",
                   "--protein-database", cfg["uniref90"], "--bowtie2", cfg["bowtie2"],
                   "--diamond", cfg["diamond"], "--prescreen-threshold", "0.01"]
            if mode == "joint_union" and joint_index is not None:
                shards = index_shards(joint_index)
                if len(shards) not in (6, 8):
                    raise RuntimeError(f"joint index is incomplete and unsafe to reuse: {joint_index}")
                cmd += ["--nucleotide-database", str(joint_index), "--bypass-nucleotide-index"]
            else:
                cmd += ["--nucleotide-database", cfg["chocophlan"], "--taxonomic-profile", str(profile)]
            commands.append(cmd)
            if execute:
                target.mkdir(parents=True, exist_ok=False)
                result = subprocess.run(cmd, check=False)
                if result.returncode:
                    raise RuntimeError(f"HUMAnN failed for {run}/{mode}: rc={result.returncode}")
                if mode == "joint_union" and joint_index is None:
                    temps = list(target.glob("*_humann_temp"))
                    if len(temps) != 1 or len(index_shards(temps[0])) not in (6, 8):
                        raise RuntimeError("HUMAnN joint-union index was not produced as a complete shard set")
                    joint_index = temps[0]
                    manifest = {
                        "created_at": now(),
                        "profile_sha256": sha256(profile),
                        "bowtie2_version": versions["bowtie2"],
                        "shards": [p.name for p in index_shards(joint_index)],
                        "reuse_scope": "joint_union_30_samples only",
                    }
                    (joint_index / "0714_index_reuse_manifest.json").write_text(
                        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
                    )
    plan = {"generated_at": now(), "execute": execute, "versions": versions,
            "commands": commands, "sample_cap": 2, "reference_modes": ["joint_union", "sample_specific"]}
    (out / "execution_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return commands


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/prjna1056765_humann_short_read_validation.json"))
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute", action="store_true", help="hospital workstation only; exactly two configured samples")
    args = parser.parse_args()
    cfg = load_json(args.config)
    out = Path(cfg["output_root"])
    if not (args.prepare or args.preflight or args.execute):
        parser.error("choose --prepare, --preflight, or --execute")
    out.mkdir(parents=True, exist_ok=True)
    prepare(cfg, out)
    if args.preflight or args.execute:
        run_humann(cfg, out, args.execute)
    print(json.dumps({"state": "executed" if args.execute else "prepared", "output": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
