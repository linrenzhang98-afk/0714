#!/usr/bin/env python3
"""Read-only structural/QC audit for the fixed PRJNA1056765 HUMAnN cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

KINDS = ("genefamilies", "pathabundance", "pathcoverage")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(path: Path, run: str, kind: str, small_bytes: int) -> dict[str, object]:
    row: dict[str, object] = {
        "run": run, "kind": kind, "path": str(path), "exists": path.is_file(),
        "bytes": "", "sha256": "", "comment_lines": "", "header_lines": "",
        "data_rows": "", "stratified_rows": "", "unstratified_rows": "",
        "malformed_rows": "", "nonfinite_values": "", "negative_values": "",
        "duplicate_feature_rows": "", "status": "", "flags": "",
    }
    if not path.is_file():
        row.update(status="FAIL", flags="missing")
        return row
    row["bytes"] = path.stat().st_size
    row["sha256"] = sha256(path)
    flags: list[str] = []
    if path.stat().st_size == 0:
        row.update(comment_lines=0, header_lines=0, data_rows=0, stratified_rows=0,
                   unstratified_rows=0, malformed_rows=0, nonfinite_values=0,
                   negative_values=0, duplicate_feature_rows=0, status="FAIL", flags="empty")
        return row
    comments = headers = data = stratified = malformed = nonfinite = negative = 0
    seen: set[str] = set()
    duplicates = 0
    expected_columns: int | None = None
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            fields = line.split("\t")
            if line.startswith("#"):
                comments += 1
                # HUMAnN's final # header is tabular; version lines are not.
                if len(fields) >= 2:
                    headers += 1
                    expected_columns = len(fields)
                continue
            data += 1
            feature = fields[0]
            if "|" in feature:
                stratified += 1
            if feature in seen:
                duplicates += 1
            seen.add(feature)
            if expected_columns is None:
                expected_columns = len(fields)
            if len(fields) != expected_columns or len(fields) < 2:
                malformed += 1
                continue
            for value in fields[1:]:
                try:
                    number = float(value)
                    if not math.isfinite(number):
                        nonfinite += 1
                    elif number < 0:
                        negative += 1
                except ValueError:
                    malformed += 1
                    break
    row.update(comment_lines=comments, header_lines=headers, data_rows=data,
               stratified_rows=stratified, unstratified_rows=data - stratified,
               malformed_rows=malformed, nonfinite_values=nonfinite,
               negative_values=negative, duplicate_feature_rows=duplicates)
    if path.stat().st_size < small_bytes:
        flags.append(f"small_lt_{small_bytes}B")
    if data == 0:
        flags.append("header_only")
    if headers == 0:
        flags.append("missing_tabular_header")
    if malformed:
        flags.append("malformed_rows")
    if nonfinite:
        flags.append("nonfinite_values")
    if negative:
        flags.append("negative_values")
    if duplicates:
        flags.append("duplicate_features")
    row["flags"] = ";".join(flags)
    row["status"] = "FAIL" if any(x in flags for x in
        ("header_only", "missing_tabular_header", "malformed_rows", "nonfinite_values",
         "negative_values", "duplicate_features")) else ("WARN" if flags else "PASS")
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--cohort", default="reports_public/metagenome_functional_profile/run_status.tsv", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--small-bytes", default=1024, type=int)
    args = parser.parse_args()
    with args.cohort.open(newline="", encoding="utf-8") as handle:
        cohort = list(csv.DictReader(handle, delimiter="\t"))
    runs = [r["run"] for r in cohort]
    if len(runs) != 30 or len(set(runs)) != 30:
        raise SystemExit(f"cohort must contain exactly 30 unique runs; observed {len(runs)}/{len(set(runs))}")
    input_available = args.input_root.is_dir()
    if input_available:
        rows = [inspect(args.input_root / run / f"{run}_{kind}.tsv", run, kind, args.small_bytes)
                for run in runs for kind in KINDS]
    else:
        rows = []
        for run in runs:
            for kind in KINDS:
                path = args.input_root / run / f"{run}_{kind}.tsv"
                rows.append({
                    "run": run, "kind": kind, "path": str(path), "exists": "",
                    "bytes": "", "sha256": "", "comment_lines": "", "header_lines": "",
                    "data_rows": "", "stratified_rows": "", "unstratified_rows": "",
                    "malformed_rows": "", "nonfinite_values": "", "negative_values": "",
                    "duplicate_feature_rows": "", "status": "NOT_RUN", "flags": "input_unavailable",
                })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (args.output_dir / "file_qc.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    special = [r for r in rows if r["run"] == "SRR27344041"]
    same_header_only = [r for r in rows if r["kind"] in ("pathabundance", "pathcoverage") and r["data_rows"] == 0]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "read_only_input_audit", "input_root": str(args.input_root.resolve()),
        "cohort_source": str(args.cohort.resolve()), "cohort_n": len(runs),
        "audit_state": ("PASSED" if all(r["status"] != "FAIL" for r in rows) else "QC_FAILED") if input_available else "INPUT_UNAVAILABLE",
        "input_available": input_available,
        "expected_files": 90, "present_files": sum(r["exists"] is True for r in rows),
        "pass": sum(r["status"] == "PASS" for r in rows),
        "warn": sum(r["status"] == "WARN" for r in rows),
        "fail": sum(r["status"] == "FAIL" for r in rows),
        "not_run": sum(r["status"] == "NOT_RUN" for r in rows),
        "audit_passed": input_available and all(r["status"] != "FAIL" for r in rows),
        "SRR27344041": special,
        "other_header_only_path_files": [r for r in same_header_only if r["run"] != "SRR27344041"],
        "parameters": {"small_bytes": args.small_bytes},
    }
    (args.output_dir / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["audit_passed"] else (3 if not input_available else 2)


if __name__ == "__main__":
    raise SystemExit(main())
