#!/usr/bin/env python3
"""Report whether unattended analysis is actively progressing or stalled."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_STATES = {"done", "failed", "rejected"}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write progress governor status")
    parser.add_argument("--jobs-dir", default="jobs")
    parser.add_argument("--state", default=".runner_state/runner_state.json")
    parser.add_argument("--public-dir", default="reports_public")
    parser.add_argument("--out-dir", default="reports_public/progress_governor")
    args = parser.parse_args()

    jobs_dir = Path(args.jobs_dir)
    public_dir = Path(args.public_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    state = load_json(Path(args.state))
    state_jobs = state.get("jobs", {}) if isinstance(state.get("jobs", {}), dict) else {}

    job_files = sorted(jobs_dir.glob("*.json")) if jobs_dir.exists() else []
    pending: list[str] = []
    failed: list[str] = []
    rejected: list[str] = []
    for job_path in job_files:
        job = load_json(job_path)
        job_id = str(job.get("job_id", job_path.stem))
        detail = state_jobs.get(job_id, {}) if isinstance(state_jobs.get(job_id, {}), dict) else {}
        status = str(detail.get("status", "pending"))
        if status not in FINAL_STATES:
            pending.append(job_id)
        elif status == "failed":
            failed.append(job_id)
        elif status == "rejected" and not job_id.startswith("2026-07-15-demo-metabolomics"):
            rejected.append(job_id)

    host_amr_summary = load_json(public_dir / "metagenome_host_amr_screen" / "summary.json")
    host_amr_done = int(host_amr_summary.get("runs_summarized", 0) or 0) >= 30
    amr_hits = int(host_amr_summary.get("amrfinder_hit_rows", 0) or 0)

    differential_summary_exists = (public_dir / "prjna1056765_group_differentials" / "summary.md").exists()
    clinical_summary_exists = (public_dir / "prjna1056765_clinical_groups" / "summary.md").exists()
    evidence_package_exists = (public_dir / "manuscript_evidence_package" / "short_project_plan.md").exists()
    manuscript_outline_exists = (public_dir / "manuscript_evidence_package" / "manuscript_outline_and_results.md").exists()
    wetlab_plan_exists = (public_dir / "manuscript_evidence_package" / "minimal_wetlab_validation_plan.md").exists()
    full_results_exists = (public_dir / "manuscript_evidence_package" / "full_results_section.md").exists()
    figure_caption_exists = (public_dir / "manuscript_evidence_package" / "tables_and_figure_captions.md").exists()
    discussion_abstract_exists = (
        public_dir / "manuscript_evidence_package" / "discussion_limitations_and_abstract.md"
    ).exists()

    if pending:
        progress_state = "running_or_queued"
        reason = f"{len(pending)} queued/non-final job(s) remain."
        next_action = "Let workstation runner continue; inspect failed jobs only if they appear."
    elif failed or rejected:
        progress_state = "stalled_failed_jobs"
        reason = f"{len(failed)} failed and {len(rejected)} rejected non-demo job(s) require repair."
        next_action = "Codex should inspect failed job metadata and patch the minimal repository-side cause."
    elif host_amr_done and differential_summary_exists and clinical_summary_exists and not evidence_package_exists:
        progress_state = "stalled_no_next_step"
        reason = (
            "All current compute jobs are final and host-AMR summary is complete; "
            "no downstream analysis/manuscript job is queued."
        )
        next_action = (
            "Codex should move from workstation compute to interpretation: integrate clinical groups, "
            "group differentials, deep-review stability, and host-AMR negatives into a manuscript-ready evidence package."
        )
    elif (
        host_amr_done
        and differential_summary_exists
        and clinical_summary_exists
        and evidence_package_exists
        and manuscript_outline_exists
        and wetlab_plan_exists
        and full_results_exists
        and figure_caption_exists
        and discussion_abstract_exists
    ):
        progress_state = "discussion_draft_ready"
        reason = (
            "Compute jobs are final; Results, Discussion/Limitations, abstract drafts, "
            "table/figure captions, and wet-lab plan are available."
        )
        next_action = (
            "Codex should assemble a manuscript skeleton with Methods and explicit figure/table callouts."
        )
    elif (
        host_amr_done
        and differential_summary_exists
        and clinical_summary_exists
        and evidence_package_exists
        and manuscript_outline_exists
        and wetlab_plan_exists
        and full_results_exists
        and figure_caption_exists
    ):
        progress_state = "results_draft_ready"
        reason = (
            "Compute jobs are final; evidence package, manuscript outline, full Results draft, "
            "table/figure captions, and wet-lab plan are available."
        )
        next_action = (
            "Codex should draft Discussion/Limitations and then prepare an abstract tailored to the target journal."
        )
    elif (
        host_amr_done
        and differential_summary_exists
        and clinical_summary_exists
        and evidence_package_exists
        and manuscript_outline_exists
        and wetlab_plan_exists
    ):
        progress_state = "manuscript_planning_ready"
        reason = "Compute jobs are final; evidence package, manuscript outline, results narrative, and wet-lab plan are available."
        next_action = "Codex should draft the full Results section and prepare publication-ready tables/figure captions."
    elif host_amr_done and differential_summary_exists and clinical_summary_exists and evidence_package_exists:
        progress_state = "interpretation_package_ready"
        reason = "Compute jobs and core public summaries are final; a short-project manuscript evidence package is available."
        next_action = (
            "Codex should draft the manuscript outline/results narrative and convert validation targets "
            "into a minimal wet-lab assay plan."
        )
    else:
        progress_state = "idle_with_missing_summary"
        reason = "No queued jobs remain, but one or more expected public summaries are missing."
        next_action = "Codex should add or repair the smallest summary-generation step."

    status = {
        "generated_at": utc_now(),
        "progress_state": progress_state,
        "reason": reason,
        "next_action": next_action,
        "job_files": len(job_files),
        "pending_jobs": pending[:50],
        "failed_jobs": failed[:50],
        "rejected_non_demo_jobs": rejected[:50],
        "host_amr_done": host_amr_done,
        "host_amr_hits": amr_hits,
        "clinical_summary_exists": clinical_summary_exists,
        "differential_summary_exists": differential_summary_exists,
        "evidence_package_exists": evidence_package_exists,
        "manuscript_outline_exists": manuscript_outline_exists,
        "wetlab_plan_exists": wetlab_plan_exists,
        "full_results_exists": full_results_exists,
        "figure_caption_exists": figure_caption_exists,
        "discussion_abstract_exists": discussion_abstract_exists,
    }
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Progress Governor Status",
        "",
        f"Generated at: {status['generated_at']}",
        f"Progress state: `{progress_state}`",
        "",
        "## Reason",
        "",
        f"- {reason}",
        "",
        "## Required Next Action",
        "",
        f"- {next_action}",
        "",
        "## Operational Counts",
        "",
        f"- Job files: {len(job_files)}",
        f"- Pending/non-final jobs: {len(pending)}",
        f"- Failed jobs: {len(failed)}",
        f"- Rejected non-demo jobs: {len(rejected)}",
        f"- Host-AMR complete: {host_amr_done}",
        f"- Host-AMR hit rows: {amr_hits}",
    ]
    if pending:
        lines.extend(["", "## Pending Jobs", ""])
        lines.extend(f"- {job_id}" for job_id in pending[:50])
    if failed:
        lines.extend(["", "## Failed Jobs", ""])
        lines.extend(f"- {job_id}" for job_id in failed[:50])
    (out_dir / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
