#!/usr/bin/env python3
"""Build manuscript-facing notes from PRJNA511633 public amplicon summaries."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def clean_taxon(taxon: str) -> str:
    parts = [part for part in taxon.split(";") if part and not part.endswith("__")]
    if not parts:
        return taxon
    last = parts[-1]
    return last.split("__", 1)[-1] if "__" in last else last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-dir", required=True, type=Path)
    parser.add_argument("--depth-qc", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    alpha = read_tsv(args.summary_dir / "alpha_diversity_group_summary.tsv")
    genus = read_tsv(args.summary_dir / "genus_group_differentials.tsv")
    species = read_tsv(args.summary_dir / "species_group_differentials.tsv")
    depth = read_tsv(args.depth_qc / "sampling_depth_recommendations.tsv")
    summary_json = {}
    summary_path = args.summary_dir / "summary.json"
    if summary_path.exists():
        summary_json = json.loads(summary_path.read_text(encoding="utf-8"))

    alpha_sig = [row for row in alpha if float(row.get("q_value", "1") or 1) < 0.05]
    genus_sig = [row for row in genus if float(row.get("q_value", "1") or 1) < 0.05]
    genus_trend = [row for row in genus if float(row.get("q_value", "1") or 1) < 0.10]

    depth_choice = "5000"
    for row in depth:
        if row.get("depth") == "10000" and float(row.get("retained_fraction", "0")) >= 0.95:
            depth_choice = "10000"
            break

    figure_lines = [
        "# PRJNA511633 Figure And Table Plan",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Main Figures",
        "",
        "1. Study workflow and QC: public SRA retrieval, reverse-read DADA2 rescue, and retained-depth summary.",
        f"2. Alpha diversity boxplots at rarefaction depth {depth_choice}: Shannon, observed features, and evenness by group.",
        "3. Beta diversity ordination: Bray-Curtis PCoA with group-significance visualization from QIIME2.",
        "4. Genus-level composition: stacked relative-abundance bar plot for top genera plus 'Other'.",
        "5. Differential candidate panel: effect-direction plot for FDR-significant or near-significant genera.",
        "",
        "## Tables",
        "",
        "1. Sample metadata and group assignment table.",
        "2. DADA2 depth/QC table.",
        "3. Alpha diversity group summary.",
        "4. Genus-level differential candidate table.",
        "5. qPCR validation target table.",
        "",
        "## Notes",
        "",
        "- Use genus-level conclusions as primary because V3-V4 16S species labels are not definitive.",
        "- State clearly that reverse reads were used after paired/forward analyses retained too few samples.",
        "- Include rarefaction sensitivity: 5000 retains 48/48; 10000 retains 47/48.",
    ]
    (out_dir / "figure_table_plan.md").write_text("\n".join(figure_lines) + "\n", encoding="utf-8")

    top_genus_lines = []
    for row in genus_sig[:8]:
        name = clean_taxon(row["taxon"])
        delta = float(row.get("mean_delta_g2_minus_g1", "0") or 0)
        direction = "higher in ICPP" if delta > 0 else "lower in ICPP"
        top_genus_lines.append(f"- {name}: {direction}, delta={delta:.4f}, q={row.get('q_value')}")

    results_lines = [
        "# PRJNA511633 Results Interpretation Draft",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Analysis Status",
        "",
        "- The current analyzable dataset is the reverse-read DADA2 result.",
        f"- The summary includes {summary_json.get('samples', 48)} samples: 23 healthy controls and 25 ICPP samples.",
        f"- A rarefaction depth of {depth_choice} reads is defensible for primary diversity analysis; 5000 reads retains all 48 samples and 10000 reads retains 47 samples.",
        "",
        "## Core Findings",
        "",
        "- Alpha diversity is consistently higher in ICPP across Shannon diversity, observed features, and evenness.",
    ]
    for row in alpha_sig:
        results_lines.append(
            f"- {row['metric']}: control median {row['healthy_control_median']}, "
            f"ICPP median {row['idiopathic_central_precocious_puberty_median']}, q={row['q_value']}."
        )
    results_lines.extend([
        "",
        "## Genus-Level Signals",
        "",
        *top_genus_lines,
        "",
        "## Conservative Interpretation",
        "",
        "- The public-data result supports an association between ICPP and altered fecal microbial diversity/composition.",
        "- The analysis should not claim causality or diagnostic performance without independent validation.",
        "- Species-level outputs should be framed as exploratory because the dataset is 16S V3-V4 rather than shotgun metagenomics.",
    ])
    (out_dir / "results_interpretation_draft.md").write_text("\n".join(results_lines) + "\n", encoding="utf-8")

    validation_rows = []
    for row in genus_sig[:6] + genus_trend[:4]:
        taxon = clean_taxon(row["taxon"])
        if taxon in {item["target_taxon"] for item in validation_rows}:
            continue
        delta = float(row.get("mean_delta_g2_minus_g1", "0") or 0)
        validation_rows.append({
            "target_taxon": taxon,
            "direction_in_icpp": "higher" if delta > 0 else "lower",
            "screening_q_value": row.get("q_value", ""),
            "wetlab_assay": "genus-targeted qPCR on independent fecal DNA",
            "priority": "high" if float(row.get("q_value", "1") or 1) < 0.05 else "medium",
        })
    with (out_dir / "wetlab_validation_targets.tsv").open("w", encoding="utf-8", newline="") as f:
        fields = ["target_taxon", "direction_in_icpp", "screening_q_value", "wetlab_assay", "priority"]
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(validation_rows)

    risk_lines = [
        "# PRJNA511633 Review Risk Notes",
        "",
        f"Generated at: {generated_at}",
        "",
        "- The biggest methods risk is the need to justify reverse-read-only analysis. Explain that paired and forward-only DADA2 retained only 2/48 samples, whereas reverse reads retained analyzable depth across the cohort.",
        "- The rarefaction choice should be presented with sensitivity: 5000 for all samples, 10000 for 47/48 samples.",
        "- Avoid overclaiming species-level biology from 16S.",
        "- Treat qPCR validation as a short-cycle follow-up, not as mandatory for a public-data-only short communication.",
        "- Target journals: Frontiers in Medicine or Journal of Clinical Medicine are more realistic than a microbiome-specialist journal unless validation data are added.",
    ]
    (out_dir / "review_risk_notes.md").write_text("\n".join(risk_lines) + "\n", encoding="utf-8")

    manifest = {
        "generated_at": generated_at,
        "depth_choice": depth_choice,
        "alpha_significant_metrics": len(alpha_sig),
        "genus_fdr_significant": len(genus_sig),
        "genus_q_lt_0_10": len(genus_trend),
        "files": [
            "figure_table_plan.md",
            "results_interpretation_draft.md",
            "wetlab_validation_targets.tsv",
            "review_risk_notes.md",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
