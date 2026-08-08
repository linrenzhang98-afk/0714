#!/usr/bin/env python3
"""Publish compact status for the PRJNA511633 amplicon analysis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_OUTPUTS = [
    ("validation_report", ["validation_report.json"]),
    ("manifest", ["manifest.tsv", "manifest.csv"]),
    ("command_log", ["command_log.jsonl"]),
    ("demux_artifact", ["qiime2/demux.qza"]),
    ("demux_visualization", ["qiime2/demux.qzv"]),
    ("feature_table", ["qiime2/table.qza"]),
    ("rep_seqs", ["qiime2/rep-seqs.qza"]),
    ("taxonomy", ["qiime2/taxonomy.qza"]),
    ("taxa_barplot", ["qiime2/taxa-bar-plots.qzv"]),
    ("genus_relative_table", ["qiime2/genus-relative-table.qza"]),
    ("species_relative_table", ["qiime2/species-relative-table.qza"]),
    ("core_metrics", ["qiime2/core-metrics"]),
    ("shannon_group_significance", ["qiime2/shannon-group-significance.qzv"]),
    ("bray_curtis_group_significance", ["qiime2/bray-curtis-group-significance.qzv"]),
    ("genus_export", ["exports/genus_relative_table"]),
    ("species_export", ["exports/species_relative_table"]),
]

OPTIONAL_OUTPUTS = {
    "shannon_group_significance",
    "bray_curtis_group_significance",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"parse_error": True}


def command_log_tail(path: Path, limit: int = 5) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"raw": line[-500:]})
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--result-glob", default="")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    if args.result_glob:
        candidates = sorted(Path(".").glob(args.result_glob))
        if candidates:
            result_dir = candidates[-1]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = load_json(result_dir / "validation_report.json")
    output_status = {}
    missing = []
    for key, rels in EXPECTED_OUTPUTS:
        candidates = [result_dir / rel for rel in rels]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        exists = path.exists()
        output_status[key] = {"exists": exists, "path": str(path)}
        if not exists:
            missing.append(key)

    errors = validation.get("errors", []) if isinstance(validation, dict) else []
    warnings = validation.get("warnings", []) if isinstance(validation, dict) else []
    last_commands = command_log_tail(result_dir / "command_log.jsonl")
    failed_commands = [r for r in last_commands if r.get("returncode") not in (None, 0)]

    required_missing = [key for key in missing if key not in OPTIONAL_OUTPUTS]
    optional_missing = [key for key in missing if key in OPTIONAL_OUTPUTS]

    if errors:
        progress_state = "failed_needs_patch"
        next_action = "Inspect validation_report.json and command_log.jsonl, then patch the smallest reproducible cause."
    elif not required_missing and optional_missing:
        progress_state = "analysis_outputs_ready_with_optional_warnings"
        next_action = "Summarize exported taxa tables and report rarefied QIIME2 group-significance visualizations as unavailable due low retained sample count."
    elif output_status["bray_curtis_group_significance"]["exists"] and output_status["genus_export"]["exists"]:
        progress_state = "analysis_outputs_ready"
        next_action = "Summarize taxa, diversity, group differences, and manuscript-facing interpretation."
    elif result_dir.exists():
        progress_state = "running_or_partial"
        next_action = "Let the runner continue; if this state is unchanged for more than one hour, inspect command_log.jsonl."
    else:
        progress_state = "not_started"
        next_action = "Ensure the job is allowlisted and picked up by the general runner."

    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": "PRJNA511633 ICPP gut 16S",
        "result_dir": str(result_dir),
        "progress_state": progress_state,
        "next_action": next_action,
        "missing_outputs": missing,
        "required_missing_outputs": required_missing,
        "optional_missing_outputs": optional_missing,
        "validation_errors": errors,
        "validation_warnings": warnings,
        "failed_recent_commands": failed_commands,
        "outputs": output_status,
    }
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# PRJNA511633 Amplicon Status",
        "",
        f"Generated at: {status['generated_at']}",
        "",
        f"Progress state: `{progress_state}`",
        "",
        "## Current Interpretation",
        "",
        f"- Next action: {next_action}",
        f"- Validation errors: {len(errors)}",
        f"- Validation warnings: {len(warnings)}",
        f"- Missing required outputs: {len(required_missing)}",
        f"- Missing optional outputs: {len(optional_missing)}",
        "",
        "## Required Outputs",
        "",
    ]
    for key, item in output_status.items():
        mark = "yes" if item["exists"] else "no"
        lines.append(f"- {key}: {mark}")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    if failed_commands:
        lines.extend(["", "## Recent Failed Command Stderr", ""])
        for record in failed_commands[-3:]:
            stderr = str(record.get("stderr_tail", "")).strip()
            if stderr:
                compact = " ".join(stderr.split())[-1200:]
                lines.append(f"- {compact}")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    (out_dir / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
