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
    amplicon_retry_jobs: list[str] = []
    for job_path in job_files:
        job = load_json(job_path)
        job_id = str(job.get("job_id", job_path.stem))
        if "prjna511633" in job_id and "16s" in job_id:
            amplicon_retry_jobs.append(job_id)
        detail = state_jobs.get(job_id, {}) if isinstance(state_jobs.get(job_id, {}), dict) else {}
        status = str(detail.get("status", "pending"))
        if status not in FINAL_STATES:
            pending.append(job_id)
        elif status == "failed":
            failed.append(job_id)
        elif status == "rejected" and not job_id.startswith("2026-07-15-demo-metabolomics"):
            rejected.append(job_id)

    if amplicon_retry_jobs:
        latest_amplicon_job = sorted(amplicon_retry_jobs)[-1]
        failed = [
            job_id
            for job_id in failed
            if not ("prjna511633" in job_id and "16s" in job_id) or job_id == latest_amplicon_job
        ]

    host_amr_summary = load_json(public_dir / "metagenome_host_amr_screen" / "summary.json")
    host_amr_done = int(host_amr_summary.get("runs_summarized", 0) or 0) >= 30
    amr_hits = int(host_amr_summary.get("amrfinder_hit_rows", 0) or 0)
    amplicon_status = load_json(public_dir / "amplicon_precocious_puberty_prjna511633" / "status.json")
    amplicon_ready = str(amplicon_status.get("progress_state", "")).startswith("analysis_outputs_ready")
    if amplicon_ready:
        failed = [job_id for job_id in failed if not ("prjna511633" in job_id and "16s" in job_id)]
    functional_summary = load_json(public_dir / "metagenome_functional_profile" / "summary.json")
    functional_state = str(functional_summary.get("state", "not_started") or "not_started")
    functional_done = functional_state == "done"
    functional_blocked = functional_state.startswith("blocked") or functional_state == "done_with_failures"
    functional_running = functional_state in {"initializing", "running", "starting"}

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
    manuscript_skeleton_exists = (public_dir / "manuscript_evidence_package" / "manuscript_skeleton.md").exists()
    reproducible_methods_exists = (
        public_dir / "manuscript_evidence_package" / "reproducible_methods_detail.md"
    ).exists()
    journal_readiness_exists = (
        public_dir / "manuscript_evidence_package" / "target_journal_readiness_checklist.md"
    ).exists()
    full_manuscript_exists = (
        public_dir / "manuscript_evidence_package" / "journal_neutral_full_manuscript_draft.md"
    ).exists()
    target_strategy_exists = (
        public_dir / "manuscript_evidence_package" / "target_journal_and_short_validation_strategy.md"
    ).exists()
    public_data_variant_exists = (
        public_dir / "manuscript_evidence_package" / "manuscript_variant_public_data_only.md"
    ).exists()
    qpcr_variant_exists = (
        public_dir / "manuscript_evidence_package" / "manuscript_variant_minimal_qpcr_validation.md"
    ).exists()
    qpcr_template_exists = (
        public_dir / "manuscript_evidence_package" / "minimal_qpcr_validation_data_template.md"
    ).exists()
    public_data_submission_package_exists = (
        public_dir / "manuscript_evidence_package" / "public_data_submission_package.md"
    ).exists()

    if functional_running:
        progress_state = "metagenome_functional_profile_running"
        reason = (
            "Shotgun functional profiling is active or being initialized; "
            f"{functional_summary.get('done_count', 0)} of {functional_summary.get('sample_count', 0)} sample(s) are done."
        )
        next_action = "Let the workstation continue HUMAnN/MetaPhlAn functional profiling; Codex should inspect logs only if it becomes blocked."
    elif functional_blocked:
        progress_state = "stalled_metagenome_functional_profile"
        reason = (
            "Shotgun functional profiling did not complete: "
            f"{functional_summary.get('reason', 'see metagenome_functional_profile summary')}"
        )
        next_action = (
            "Codex should inspect reports_public/metagenome_functional_profile/summary.md, "
            "runner_status.txt, worker.nohup.log, and patch the smallest repository-side cause."
        )
    elif pending:
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
        and functional_done
        and differential_summary_exists
        and clinical_summary_exists
        and evidence_package_exists
        and manuscript_outline_exists
        and wetlab_plan_exists
        and full_results_exists
        and figure_caption_exists
        and discussion_abstract_exists
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
        and full_manuscript_exists
        and target_strategy_exists
        and public_data_variant_exists
        and qpcr_variant_exists
        and qpcr_template_exists
        and public_data_submission_package_exists
    ):
        progress_state = "public_data_submission_ready"
        reason = (
            "Compute jobs and the shotgun functional profile stage are final; "
            "the public-data-only manuscript route is selected and the submission package is available."
        )
        next_action = (
            "Proceed with public-data manuscript polishing, figure/table finalization, and target-journal formatting; "
            "qPCR validation is optional follow-up, not a current blocker."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
        and full_manuscript_exists
        and target_strategy_exists
        and public_data_variant_exists
        and qpcr_variant_exists
        and qpcr_template_exists
    ):
        progress_state = "minimal_qpcr_validation_ready"
        reason = (
            "Compute jobs are final; submission variants and minimal qPCR validation data template are available."
        )
        next_action = (
            "Author can collect local qPCR validation results using the template; no workstation compute is pending."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
        and full_manuscript_exists
        and target_strategy_exists
        and public_data_variant_exists
        and qpcr_variant_exists
    ):
        progress_state = "submission_variants_ready"
        reason = (
            "Compute jobs are final; public-data-only and minimal-qPCR manuscript variants are available."
        )
        next_action = (
            "Author should choose whether to submit the public-data-only version now or add short qPCR validation first."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
        and full_manuscript_exists
        and target_strategy_exists
    ):
        progress_state = "target_strategy_ready"
        reason = (
            "Compute jobs are final; full manuscript draft and target-journal/short-validation strategy are available."
        )
        next_action = (
            "Codex should prepare two manuscript variants: public-data-only and public-data-plus-minimal-qPCR."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
        and full_manuscript_exists
    ):
        progress_state = "full_manuscript_draft_ready"
        reason = (
            "Compute jobs are final; a journal-neutral full manuscript draft and supporting readiness files are available."
        )
        next_action = (
            "Author should choose target journal or provide wet-lab validation status; Codex can then format and polish the draft."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
        and journal_readiness_exists
    ):
        progress_state = "journal_readiness_ready"
        reason = (
            "Compute jobs are final; manuscript skeleton, reproducible Methods, and target-journal readiness checklist are available."
        )
        next_action = (
            "Codex should prepare a journal-neutral full manuscript draft; author should later choose a target journal for final formatting."
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
        and manuscript_skeleton_exists
        and reproducible_methods_exists
    ):
        progress_state = "methods_reproducibility_ready"
        reason = (
            "Compute jobs are final; manuscript skeleton and reproducible Methods detail are available."
        )
        next_action = (
            "Codex should prepare a target-journal readiness checklist and identify remaining author decisions."
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
        and manuscript_skeleton_exists
    ):
        progress_state = "manuscript_skeleton_ready"
        reason = (
            "Compute jobs are final; manuscript skeleton, Results, Discussion/Limitations, "
            "abstract drafts, table/figure captions, and wet-lab plan are available."
        )
        next_action = (
            "Codex should refine Methods for reproducibility and prepare target-journal formatting once a journal is selected."
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
        "functional_profile_state": functional_state,
        "functional_profile_done": functional_done,
        "clinical_summary_exists": clinical_summary_exists,
        "differential_summary_exists": differential_summary_exists,
        "evidence_package_exists": evidence_package_exists,
        "manuscript_outline_exists": manuscript_outline_exists,
        "wetlab_plan_exists": wetlab_plan_exists,
        "full_results_exists": full_results_exists,
        "figure_caption_exists": figure_caption_exists,
        "discussion_abstract_exists": discussion_abstract_exists,
        "manuscript_skeleton_exists": manuscript_skeleton_exists,
        "reproducible_methods_exists": reproducible_methods_exists,
        "journal_readiness_exists": journal_readiness_exists,
        "full_manuscript_exists": full_manuscript_exists,
        "target_strategy_exists": target_strategy_exists,
        "public_data_variant_exists": public_data_variant_exists,
        "qpcr_variant_exists": qpcr_variant_exists,
        "qpcr_template_exists": qpcr_template_exists,
        "public_data_submission_package_exists": public_data_submission_package_exists,
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
        f"- Functional profile state: {functional_state}",
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
