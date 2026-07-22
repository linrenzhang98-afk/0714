#!/usr/bin/env python3
"""Write a compact platform status summary for unattended checks."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"jobs": {}}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"event": "unparsed_log_line", "raw": line[:500]})
    return events


def list_decision_requests(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(p for p in path.glob("*.md") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Write platform status Markdown")
    parser.add_argument("--state", default=".runner_state/runner_state.json")
    parser.add_argument("--log", default=".runner_logs/runner.jsonl")
    parser.add_argument("--decision-dir", default="decision_requests")
    parser.add_argument("--out", default="reports/platform_status.md")
    parser.add_argument("--tail", type=int, default=80)
    args = parser.parse_args()

    state_path = Path(args.state)
    log_path = Path(args.log)
    decision_dir = Path(args.decision_dir)
    out_path = Path(args.out)
    state = load_state(state_path)
    jobs = state.get("jobs", {})
    if not isinstance(jobs, dict):
        jobs = {}
    events = load_jsonl_tail(log_path, args.tail)
    decisions = list_decision_requests(decision_dir)

    status_counts = Counter(str(v.get("status", "unknown")) for v in jobs.values() if isinstance(v, dict))
    event_counts = Counter(str(e.get("event", "unknown")) for e in events)

    lines = [
        "# Platform Status",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Job Status Counts",
        "",
    ]
    if status_counts:
        for key, count in sorted(status_counts.items()):
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- No job state found.")

    lines.extend(["", "## Recent Event Counts", ""])
    if event_counts:
        for key, count in sorted(event_counts.items()):
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- No runner log found.")

    lines.extend(["", "## Decision Requests", ""])
    if decisions:
        for path in decisions:
            lines.append(f"- {path}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Recent Jobs", ""])
    if jobs:
        for job_id, detail in sorted(jobs.items()):
            if not isinstance(detail, dict):
                continue
            status = detail.get("status", "unknown")
            task = detail.get("task", "")
            updated = detail.get("updated_at", "")
            error = detail.get("error", "")
            line = f"- {job_id}: {status}"
            if task:
                line += f" ({task})"
            if updated:
                line += f", updated {updated}"
            if error:
                line += f", error: {error}"
            lines.append(line)
    else:
        lines.append("- No jobs recorded.")

    lines.extend(["", "## Last Events", ""])
    for event in events[-20:]:
        event_name = event.get("event", "unknown")
        ts = event.get("ts", "")
        job_id = event.get("job_id", "")
        status = event.get("status", "")
        error = event.get("error", "")
        line = f"- {ts} {event_name}"
        if job_id:
            line += f" job={job_id}"
        if status:
            line += f" status={status}"
        if error:
            line += f" error={error}"
        lines.append(line)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
