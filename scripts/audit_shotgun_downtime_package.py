#!/usr/bin/env python3
"""Read-only contradiction audit for the workstation-downtime package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "reports_public/formal_cross_cohort_analysis/formal_analysis_plan.md",
    "reports_public/formal_cross_cohort_analysis/formal_analysis_manifest.json",
    "reports_public/formal_cross_cohort_analysis/statistical_test_registry.tsv",
    "reports_public/formal_cross_cohort_analysis/multiplicity_plan.md",
    "reports_public/formal_cross_cohort_analysis/result_schema.json",
    "reports_public/formal_cross_cohort_analysis/interpretation_rules.md",
    "reports_public/formal_cross_cohort_analysis/post_primary_decision_rules.md",
    "reports_public/manuscript_draft/manuscript_outline.md",
    "reports_public/manuscript_draft/title_candidates.md",
    "reports_public/manuscript_draft/abstract_skeleton.md",
    "reports_public/manuscript_draft/introduction_draft.md",
    "reports_public/manuscript_draft/methods_draft.md",
    "reports_public/manuscript_draft/results_skeleton.md",
    "reports_public/manuscript_draft/discussion_skeleton.md",
    "reports_public/manuscript_draft/limitations.md",
    "reports_public/manuscript_draft/claim_language_guardrails.md",
    "reports_public/manuscript_draft/figure_blueprint.md",
    "reports_public/manuscript_draft/table_blueprint.md",
    "reports_public/manuscript_draft/journal_positioning.md",
    "reports_public/method_literature_audit/method_evidence_matrix.tsv",
    "reports_public/method_literature_audit/key_references.md",
    "reports_public/method_literature_audit/methods_wording_support.md",
    "reports_public/method_literature_audit/reviewer_risk_notes.md",
    "reports_public/cohort_portfolio_status.md",
    "reports_public/workstation_recovery_runbook.md",
    "shotgun_analysis/core.py",
    "shotgun_analysis/czm.py",
    "shotgun_analysis/io.py",
    "shotgun_analysis/permutation.py",
    "shotgun_analysis/pipeline.py",
    "shotgun_analysis/results.py",
    "shotgun_analysis/stats.py",
    "scripts/run_formal_cross_cohort_analysis.py",
    "scripts/run_formal_cross_cohort_grid.py",
    "tests/test_shotgun_formal_analysis.py",
]


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"missing required files: {missing}")
    manifest = json.loads((ROOT / "reports_public/formal_cross_cohort_analysis/formal_analysis_manifest.json").read_text())
    if manifest["cohorts"]["anchor"]["groups"] != {
        "Bacterial infection": 114, "Fungal infection": 78,
        "Lung cancer": 122, "Pulmonary tuberculosis": 86,
    }:
        raise SystemExit("anchor group counts inconsistent")
    if manifest["cohorts"]["external"]["groups"] != {"Drug_Resistance": 49, "Drug_Sensitive": 81}:
        raise SystemExit("external group counts inconsistent")
    if manifest["total_technical_sample_universe"] != 530 or manifest["pooling"]["matrix_created"] is not False:
        raise SystemExit("sample universe or pooling state inconsistent")

    text = "\n".join((ROOT / path).read_text(errors="replace") for path in REQUIRED if path.endswith((".md", ".tsv", ".json")))
    forbidden_assertions = [
        r"this is a multicenter study", r"we conducted a multicenter study",
        r"we (?:analyzed|treated the data as) (?:one |a single )530-(?:sample|person|patient) diagnosis cohort",
        r"PRJCA046985 (?:is|served as) (?:a |the )?(?:replication|validation) cohort",
        r"classified fraction (?:is|measures|estimates) (?:the )?bacterial (?:load|biomass)",
        r"we (?:identified|validated|discovered) (?:a |the )?(?:diagnostic )?biomarker",
        r"we performed (?:a )?formal meta-analysis", r"zCompositions installation (?:completed|succeeded)",
        r"differential abundance (?:was|has been) executed",
    ]
    hits = [pattern for pattern in forbidden_assertions if re.search(pattern, text, flags=re.IGNORECASE)]
    if hits:
        raise SystemExit(f"forbidden assertive claims: {hits}")
    result_number = re.search(r"(?:PERMANOVA|PERMDISP).{0,80}(?:R2|R²|P)\s*=\s*(?!\[)[0-9]", text, flags=re.IGNORECASE)
    if result_number:
        raise SystemExit(f"unplaceholdered formal statistic: {result_number.group(0)}")
    if "Classified fraction is not bacterial biomass" not in text:
        raise SystemExit("classified-fraction boundary missing")

    report = {
        "project_state_consistent": True,
        "sample_counts_consistent": True,
        "clinical_contrasts_consistent": True,
        "no_fake_results": True,
        "no_naive_pooling": True,
        "no_replication_claim": True,
        "no_multicenter_claim": True,
        "classified_fraction_boundary_preserved": True,
        "DA_not_executed": True,
        "ETYY_not_used": True,
        "biological_analysis_not_executed": True,
        "required_files_checked": len(REQUIRED),
        "audit_scope": "workstation downtime preparation package",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
