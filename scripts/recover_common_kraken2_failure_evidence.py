#!/usr/bin/env python3
"""Recover bounded metadata from the failed common-layer diagnostic job."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SOURCE_JOB_ID = "20260823T110000Z-prjna1056765-prjca046985-common-kraken2-layer-diagnostic"
SOURCE_ITEM_ID = "CRR2423908"
STATE_NAME = SOURCE_JOB_ID + ".execution.json"
HANDOFF_NAME = SOURCE_JOB_ID + "-handoff"
EXEC_FIELDS = ("job_item_id", "status", "returncode", "stdout_tail", "stderr_tail", "started_at", "finished_at", "command_hash")
DIAG_FIELDS = ("stage", "exception_type", "exception_message", "traceback",
               "first_failing_path_if_any", "first_failing_run_if_any", "expected_path",
               "observed_path", "source_gate_status")

def _bounded(value: Any) -> Any:
    return value[-4000:] if isinstance(value, str) else value

def recover(state_root: Path, output_dir: Path) -> dict[str, Any]:
    state_path = state_root / STATE_NAME
    handoff = state_root / HANDOFF_NAME
    diag_path = handoff / "diagnostic.json"
    txt_path = handoff / "diagnostic.txt"
    state_present = state_path.is_file()
    diag_present = diag_path.is_file()
    txt_present = txt_path.is_file()
    state: dict[str, Any] = {}
    if state_present:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    # etty_bounded_job persists per-item execution records under the exact item ID.
    item_state = state.get("items", {}).get(SOURCE_ITEM_ID, {}) if isinstance(state.get("items"), dict) else {}
    execution = {key: _bounded(item_state.get(key)) for key in EXEC_FIELDS}
    execution["job_item_id"] = item_state.get("job_item_id", item_state.get("id"))
    diagnostic: dict[str, Any] = {key: None for key in DIAG_FIELDS}
    if diag_present:
        raw = json.loads(diag_path.read_text(encoding="utf-8"))
        diagnostic = {key: _bounded(raw.get(key)) for key in DIAG_FIELDS}
    stderr = execution.get("stderr_tail") or ""
    stdout = execution.get("stdout_tail") or ""
    evidence = (str(stderr) + "\n" + str(stdout)).lower()
    if diagnostic.get("stage"):
        failure_stage = diagnostic["stage"]
    elif evidence:
        failure_stage = "unknown (execution-state stream only)"
    else:
        failure_stage = "unknown"
    likely = "not identified by recovered evidence"
    if diagnostic.get("exception_message"):
        likely = "parser exception: " + str(diagnostic["exception_message"])
    elif "no such file" in evidence or "not found" in evidence:
        likely = "missing path or executable indicated by stderr"
    elif item_state.get("returncode") not in (None, 0):
        likely = "command returned nonzero; specific cause not identified by recovered evidence"
    result = {
        "source_job_id": SOURCE_JOB_ID,
        "execution_state_present": state_present,
        "diagnostic_json_present": diag_present,
        "diagnostic_txt_present": txt_present,
        "execution": execution,
        "diagnostic": diagnostic,
        "inference": {
            "failure_stage": failure_stage,
            "likely_root_cause": likely,
            "technical_fix_possible": None,
            "biological_method_change_required": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "recovered_failure_evidence.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [f"source_job_id={SOURCE_JOB_ID}", f"execution_state_present={state_present}",
             f"diagnostic_json_present={diag_present}", f"diagnostic_txt_present={txt_present}",
             f"failure_stage={failure_stage}", f"likely_root_cause={likely}",
             "technical_fix_possible=" + str(result["inference"]["technical_fix_possible"]),
             "biological_method_change_required=" + str(result["inference"]["biological_method_change_required"])]
    for section in ("execution", "diagnostic"):
        for key, value in result[section].items():
            lines.append(f"{section}.{key}={value}")
    (output_dir / "recovered_failure_evidence.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", type=Path, default=Path("/mnt/disk1/0714_control/state"))
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    recover(args.state_root, args.output_dir)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
