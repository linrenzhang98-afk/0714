#!/usr/bin/env python3
"""Read-only technical completion QC for frozen Kraken2 production outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


QC_TYPE = "PRJCA046985_NATIVE_KRAKEN2_PRODUCTION_TECHNICAL_QC"
RECOVERY_JOB_ID = "20260822T175547Z-prjca046985-122-native-kraken2-recovery"
RESULTS_ROOT = Path("/mnt/disk1/0714_control/results")
RAW_ROOT = Path("/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq")
KRAKEN2 = "/home/suma/anaconda3/envs/mgshotgun/bin/kraken2"
DATABASE = "/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209"
DATABASE_IDENTITY = "6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3"
GROUPS = ("Drug_Sensitive", "Drug_Resistance")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class QCError(Exception):
    pass


def fraction(classified: int, total: int) -> float:
    return classified / total if total else 0.0


def flag_value(command: list[str], flag: str) -> str:
    if command.count(flag) != 1:
        raise QCError(f"command must contain exactly one {flag}")
    index = command.index(flag)
    if index + 1 >= len(command):
        raise QCError(f"command is missing the value for {flag}")
    return command[index + 1]


def checked_output(path_value: str, seen: set[Path]) -> Path:
    path = Path(path_value)
    if not path.is_absolute() or ".." in path.parts or path.is_symlink():
        raise QCError("output path is invalid or is a symlink")
    try:
        resolved = path.resolve(strict=True)
        results_root = RESULTS_ROOT.resolve(strict=True)
        raw_root = RAW_ROOT.resolve(strict=True)
    except OSError as exc:
        raise QCError(f"output path cannot be resolved: {type(exc).__name__}") from exc
    if results_root not in resolved.parents:
        raise QCError("output path escapes the approved results root")
    if resolved == raw_root or raw_root in resolved.parents:
        raise QCError("output path overlaps the raw FASTQ root")
    if resolved in seen:
        raise QCError("duplicate output path")
    if not path.is_file():
        raise QCError("output is not a regular file")
    seen.add(resolved)
    return path


def parse_kraken2_output(path: Path) -> tuple[int, int, int]:
    classified = 0
    unclassified = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            status = line.split("\t", 1)[0]
            if status == "C":
                classified += 1
            elif status == "U":
                unclassified += 1
            else:
                raise QCError("Kraken2 output contains an unexpected record status")
    total = classified + unclassified
    if total <= 0:
        raise QCError("Kraken2 output contains no read records")
    return classified, unclassified, total


def count_nonempty_lines(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    if count <= 0:
        raise QCError("Kraken2 report contains no nonempty lines")
    return count


def empty_group() -> dict[str, int]:
    return {"runs": 0, "classified_reads": 0, "unclassified_reads": 0, "total_reads": 0}


def validate(production: dict[str, Any], recovery: dict[str, Any]) -> dict[str, Any]:
    if recovery != {"job_id": RECOVERY_JOB_ID, "status": "done"}:
        raise QCError("recovery result is not the exact completed job")
    items = production.get("items")
    if not isinstance(items, list) or len(items) != 122:
        raise QCError("production definition must contain exactly 122 items")
    identifiers = [item.get("id") for item in items]
    if any(not isinstance(item_id, str) or not item_id for item_id in identifiers) or len(set(identifiers)) != 122:
        raise QCError("production run IDs are invalid or duplicated")
    expected_method = {
        "job_id": RECOVERY_JOB_ID,
        "acquire": False,
        "database_path": DATABASE,
        "database_manifest_identity_sha256": DATABASE_IDENTITY,
        "threads": 4,
        "confidence": 0.0,
        "minimum_hit_groups": 2,
        "host_filtering": False,
        "trimming": False,
        "bracken": False,
        "biological_inference": False,
    }
    for key, expected in expected_method.items():
        if production.get(key) != expected:
            raise QCError(f"frozen production method mismatch: {key}")

    seen_outputs: set[Path] = set()
    groups = {name: empty_group() for name in GROUPS}
    runs: list[dict[str, Any]] = []
    total_classified = 0
    total_unclassified = 0
    for item in items:
        run = item["id"]
        group = item.get("clinical_group")
        if group not in groups:
            raise QCError("production item has an unexpected clinical group")
        expected_bytes = item.get("expected_bytes")
        input_sha256 = item.get("sha256")
        if not isinstance(expected_bytes, int) or expected_bytes <= 0 or not isinstance(input_sha256, str) or not SHA256.fullmatch(input_sha256):
            raise QCError("production input identity is invalid")
        command = item.get("command")
        if not isinstance(command, list) or any(not isinstance(arg, str) for arg in command):
            raise QCError("production command is not an argv list")
        if len(command) != 14 or command[0] != KRAKEN2:
            raise QCError("production command executable or shape is invalid")
        if flag_value(command, "--db") != DATABASE:
            raise QCError("production command database mismatch")
        if flag_value(command, "--threads") != "4":
            raise QCError("production command thread mismatch")
        if flag_value(command, "--confidence") != "0.0":
            raise QCError("production command confidence mismatch")
        if flag_value(command, "--minimum-hit-groups") != "2":
            raise QCError("production command minimum-hit-groups mismatch")
        input_path = command[-1]
        if input_path != item.get("destination") or Path(input_path).parent != RAW_ROOT:
            raise QCError("production command input path mismatch")
        report = checked_output(flag_value(command, "--report"), seen_outputs)
        kraken_output = checked_output(flag_value(command, "--output"), seen_outputs)
        kreport_bytes = report.stat().st_size
        if kreport_bytes <= 0:
            raise QCError("Kraken2 report is empty")
        report_lines = count_nonempty_lines(report)
        classified, unclassified, total = parse_kraken2_output(kraken_output)
        if classified + unclassified != total:
            raise QCError("per-run read totals are inconsistent")
        total_classified += classified
        total_unclassified += unclassified
        group_row = groups[group]
        group_row["runs"] += 1
        group_row["classified_reads"] += classified
        group_row["unclassified_reads"] += unclassified
        group_row["total_reads"] += total
        runs.append({
            "run_accession": run,
            "clinical_group": group,
            "input_expected_bytes": expected_bytes,
            "input_sha256": input_sha256,
            "kreport_bytes": kreport_bytes,
            "kraken2_output_bytes": kraken_output.stat().st_size,
            "kreport_nonempty_lines": report_lines,
            "classified_reads": classified,
            "unclassified_reads": unclassified,
            "total_reads": total,
            "classified_fraction": fraction(classified, total),
        })

    total_reads = total_classified + total_unclassified
    if len(runs) != 122 or len(seen_outputs) != 244:
        raise QCError("verified output count is incomplete")
    if sum(row["runs"] for row in groups.values()) != 122:
        raise QCError("group run counts are inconsistent")
    if sum(row["total_reads"] for row in groups.values()) != total_reads:
        raise QCError("group and overall read totals are inconsistent")
    for row in groups.values():
        row["classified_fraction"] = fraction(row["classified_reads"], row["total_reads"])
    return {
        "qc_type": QC_TYPE,
        "recovery_job_id": RECOVERY_JOB_ID,
        "status": "VERIFIED",
        "expected_runs": 122,
        "verified_runs": 122,
        "expected_kreports": 122,
        "verified_kreports": 122,
        "expected_kraken2_outputs": 122,
        "verified_kraken2_outputs": 122,
        "method": {
            "kraken2_version": "2.17.1",
            "database_identity": DATABASE_IDENTITY,
            "threads": 4,
            "confidence": 0.0,
            "minimum_hit_groups": 2,
            "native_reads": True,
            "host_filtering": False,
            "trimming": False,
            "bracken": False,
            "biological_inference": False,
        },
        "totals": {
            "classified_reads": total_classified,
            "unclassified_reads": total_unclassified,
            "total_reads": total_reads,
            "classified_fraction": fraction(total_classified, total_reads),
        },
        "groups": groups,
        "runs": sorted(runs, key=lambda row: row["run_accession"]),
    }


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-definition", required=True, type=Path)
    parser.add_argument("--recovery-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        production = json.loads(args.production_definition.read_text(encoding="utf-8"))
        recovery = json.loads(args.recovery_result.read_text(encoding="utf-8"))
        payload = validate(production, recovery)
        write_output(args.output, payload)
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, QCError) as exc:
        failure = {
            "qc_type": QC_TYPE,
            "recovery_job_id": RECOVERY_JOB_ID,
            "status": "FAILED",
            "expected_runs": 122,
            "failure": " ".join(str(exc).split())[:500],
        }
        try:
            write_output(args.output, failure)
        except OSError:
            pass
        print(f"technical QC failed: {failure['failure']}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
