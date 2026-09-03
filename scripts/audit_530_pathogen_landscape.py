#!/usr/bin/env python3
"""Bounded descriptive pathogen-detection landscape audit for two BALF cohorts.

This program reads existing species-level direct Kraken2 assignment matrices. It
does not transform compositions, run distance-based tests, or perform DA.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


EXPECTED = {
    "anchor": {
        "samples": 400,
        "features": 5198,
        "groups": {
            "Bacterial infection": 114,
            "Fungal infection": 78,
            "Lung cancer": 122,
            "Pulmonary tuberculosis": 86,
        },
    },
    "external": {
        "samples": 130,
        "features": 4888,
        "groups": {"Drug_Resistance": 49, "Drug_Sensitive": 81},
    },
}
MATRIX_METADATA = {
    "taxid", "rank", "scientific_name", "prevalence",
    "present_5pct", "present_10pct", "present_20pct",
}
MIN_CODETECTION_SUPPORT = 5

# Existing repository curation from summarize_prjna1056765_group_differentials.py,
# extended only by examples explicitly named in the user-authorized audit.
CONFIRMED_PATHOGENS = {
    "Pseudomonas aeruginosa", "Klebsiella pneumoniae", "Staphylococcus aureus",
    "Haemophilus influenzae", "Streptococcus pneumoniae",
    "Mycobacterium tuberculosis", "Cryptococcus neoformans",
    "Aspergillus fumigatus", "Moraxella catarrhalis", "Pneumocystis jirovecii",
}
OPPORTUNISTS = {
    "Acinetobacter baumannii", "Stenotrophomonas maltophilia",
    "Candida albicans", "Escherichia coli",
}
BACKGROUND = {
    "Homo sapiens", "Toxoplasma gondii", "Arabidopsis thaliana",
    "Benincasa hispida", "Camelina sativa", "Cucurbita pepo",
}
COMMENSALS = {
    "Prevotella melaninogenica", "Prevotella intermedia", "Prevotella jejuni",
    "Rothia mucilaginosa", "Streptococcus mitis", "Streptococcus oralis",
    "Veillonella parvula", "Fusobacterium nucleatum",
}
PANEL_NAMES = CONFIRMED_PATHOGENS | OPPORTUNISTS


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {key: None for key in ("minimum", "q1", "median", "q3", "maximum")}
    ordered = sorted(values)

    def q(probability: float) -> float:
        position = (len(ordered) - 1) * probability
        lower, upper = math.floor(position), math.ceil(position)
        if lower == upper:
            return float(ordered[lower])
        return float(ordered[lower] * (upper - position) + ordered[upper] * (position - lower))

    return {"minimum": q(0), "q1": q(0.25), "median": q(0.5), "q3": q(0.75), "maximum": q(1)}


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_matrix(path: Path, cohort: str) -> dict[str, Any]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        sample_ids = [field for field in fields if field not in MATRIX_METADATA]
        if len(fields) != len(set(fields)) or len(sample_ids) != EXPECTED[cohort]["samples"]:
            raise ValueError(f"{cohort} sample header contract failed")
        taxa, seen_taxids = [], set()
        for line, row in enumerate(reader, 2):
            taxid = row.get("taxid", "").strip()
            name = " ".join(row.get("scientific_name", "").split())
            if row.get("rank") != "S" or not taxid or taxid in seen_taxids or not name:
                raise ValueError(f"{cohort} species identity contract failed at line {line}")
            seen_taxids.add(taxid)
            counts = []
            for sample in sample_ids:
                raw = row[sample].strip()
                value = int(raw)
                if raw != str(value) or value < 0:
                    raise ValueError(f"{cohort} nonnegative integer contract failed at line {line}")
                counts.append(value)
            taxa.append({"taxid": taxid, "scientific_name": name, "counts": counts})
    if len(taxa) != EXPECTED[cohort]["features"] or len(set(sample_ids)) != len(sample_ids):
        raise ValueError(f"{cohort} frozen dimensions failed")
    name_taxids: dict[str, set[str]] = defaultdict(set)
    for taxon in taxa:
        name_taxids[taxon["scientific_name"]].add(taxon["taxid"])
    return {"sample_ids": sample_ids, "taxa": taxa, "ambiguous_names": {k for k, v in name_taxids.items() if len(v) > 1}}


def read_groups(path: Path, cohort: str) -> dict[str, str]:
    run_field, group_field = ("run", "diagnosis") if cohort == "anchor" else ("run_accession", "group_raw")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    mapping = {row[run_field]: row[group_field] for row in rows}
    if len(mapping) != len(rows) or Counter(mapping.values()) != Counter(EXPECTED[cohort]["groups"]):
        raise ValueError(f"{cohort} metadata/group contract failed")
    return mapping


def relevance(name: str) -> str:
    if name in CONFIRMED_PATHOGENS:
        return "confirmed_known_respiratory_pathogen"
    if name in OPPORTUNISTS:
        return "plausible_opportunist"
    if name in BACKGROUND or name in COMMENSALS:
        return "likely_commensal_or_background"
    return "uncertain"


def taxon_metrics(taxon: dict[str, Any], totals: list[int], n: int) -> dict[str, Any]:
    counts = taxon["counts"]
    positive = [value for value in counts if value > 0]
    fractions = [counts[i] / totals[i] for i in range(n) if counts[i] > 0 and totals[i] > 0]
    return {
        "taxid": taxon["taxid"],
        "scientific_name": taxon["scientific_name"],
        "positive_sample_count": len(positive),
        "detection_prevalence": len(positive) / n,
        "total_direct_assigned_reads": sum(counts),
        "median_direct_assigned_reads_among_positive": statistics.median(positive) if positive else 0,
        "median_fraction_species_reads_among_positive": statistics.median(fractions) if fractions else 0,
        "clinical_pathogen_relevance_flag": relevance(taxon["scientific_name"]),
    }


def ranked(metrics: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(metrics, key=lambda row: (-row[key], -row["positive_sample_count"], row["scientific_name"], row["taxid"]))[:30]


def audit_cohort(cohort: str, matrix: dict[str, Any], groups: dict[str, str]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    sample_ids, taxa = matrix["sample_ids"], matrix["taxa"]
    if set(sample_ids) != set(groups):
        raise ValueError(f"{cohort} matrix/metadata identities differ")
    n = len(sample_ids)
    totals = [sum(taxon["counts"][i] for taxon in taxa) for i in range(n)]
    detected = [sum(taxon["counts"][i] > 0 for taxon in taxa) for i in range(n)]
    if any(total <= 0 for total in totals):
        raise ValueError(f"{cohort} has zero species direct-count total")
    top1, top3 = [], []
    for i, total in enumerate(totals):
        ordered = sorted((taxon["counts"][i] for taxon in taxa), reverse=True)
        top1.append(ordered[0] / total)
        top3.append(sum(ordered[:3]) / total)

    metrics = [taxon_metrics(taxon, totals, n) for taxon in taxa]
    metric_by_taxid = {row["taxid"]: row for row in metrics}
    panel_taxa = [taxon for taxon in taxa if taxon["scientific_name"] in PANEL_NAMES and any(taxon["counts"])]
    panel_taxa.sort(key=lambda row: (row["scientific_name"], row["taxid"]))
    sample_rows, dominant_rows = [], []
    profile_counts: Counter[tuple[str, ...]] = Counter()
    pair_counts: Counter[tuple[str, ...]] = Counter()
    triplet_counts: Counter[tuple[str, ...]] = Counter()
    structure_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    dominant_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for i, sample in enumerate(sample_ids):
        positives = [(taxon["scientific_name"], taxon["counts"][i]) for taxon in panel_taxa if taxon["counts"][i] > 0]
        names = tuple(sorted(name for name, _ in positives))
        category = "no_panel_pathogen_detected" if not names else "single_panel_pathogen" if len(names) == 1 else "two_panel_pathogens" if len(names) == 2 else "three_or_more_panel_pathogens"
        group = groups[sample]
        structure_by_group[group][category] += 1
        if names:
            profile_counts[names] += 1
            for pair in combinations(names, 2):
                pair_counts[pair] += 1
            for triplet in combinations(names, 3):
                triplet_counts[triplet] += 1
            maximum = max(value for _, value in positives)
            leaders = sorted(name for name, value in positives if value == maximum)
            dominant = ";".join(leaders)
            dominant_by_group[group][dominant] += 1
        else:
            maximum, leaders, dominant = 0, [], ""
        sample_rows.append({
            "cohort": cohort, "sample_id": sample, "clinical_group": group,
            "detected_species": detected[i], "species_direct_assigned_reads": totals[i],
            "top1_dominance": top1[i], "top3_dominance": top3[i],
            "candidate_panel_positive_count": len(names), "candidate_panel_category": category,
        })
        dominant_rows.append({
            "cohort": cohort, "sample_id": sample, "clinical_group": group,
            "candidate_panel_positive_count": len(names), "dominant_candidate_pathogen": dominant,
            "dominant_direct_assigned_reads": maximum, "tie": len(leaders) > 1,
        })

    group_rows, feasibility_rows = [], []
    for taxon in panel_taxa:
        metric = metric_by_taxid[taxon["taxid"]]
        positives_by_group = {}
        for group in EXPECTED[cohort]["groups"]:
            indices = [i for i, sample in enumerate(sample_ids) if groups[sample] == group]
            values = [taxon["counts"][i] for i in indices]
            positive_indices = [i for i in indices if taxon["counts"][i] > 0]
            positive = [taxon["counts"][i] for i in positive_indices]
            relative = [taxon["counts"][i] / totals[i] for i in positive_indices]
            q = quantiles([float(value) for value in positive])
            positives_by_group[group] = len(positive)
            group_rows.append({
                "cohort": cohort, "taxid": taxon["taxid"], "scientific_name": taxon["scientific_name"],
                "clinical_group": group, "positive_n": len(positive), "group_n": len(indices),
                "prevalence": len(positive) / len(indices), "positive_signal_median": q["median"],
                "positive_signal_q1": q["q1"], "positive_signal_q3": q["q3"],
                "positive_relative_signal_median": statistics.median(relative) if relative else None,
                "exploratory_test": "NOT_RUN_DESCRIPTIVE_AUDIT",
            })
        positive_values = [value for value in taxon["counts"] if value > 0]
        q = quantiles([float(value) for value in positive_values])
        feasibility_rows.append({
            "cohort": cohort, "taxid": taxon["taxid"], "scientific_name": taxon["scientific_name"],
            "total_positives": len(positive_values),
            "positives_by_group": json.dumps(positives_by_group, sort_keys=True, separators=(",", ":")),
            "positive_signal_median": q["median"], "positive_signal_q1": q["q1"], "positive_signal_q3": q["q3"],
            "proportion_positive_with_one_read": sum(value == 1 for value in positive_values) / len(positive_values) if positive_values else None,
            "adequate_for_future_group_comparison": len(positive_values) >= 20 and min(positives_by_group.values()) >= 5,
            "adequacy_rule": "total positives >=20 and every clinical group >=5 positives",
        })

    bins = Counter()
    for count in detected:
        bins["0" if count == 0 else "1" if count == 1 else "2" if count == 2 else "3" if count == 3 else "4-5" if count <= 5 else ">5"] += 1
    structure_total = Counter(row["candidate_panel_category"] for row in sample_rows)
    codetection_rows = []
    for kind, counter in (("profile", profile_counts), ("pair", pair_counts), ("triplet", triplet_counts)):
        for names, support in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            if support >= MIN_CODETECTION_SUPPORT and (kind != "profile" or len(names) == 1):
                codetection_rows.append({"cohort": cohort, "pattern_type": kind, "pathogens": ";".join(names), "support_n": support, "minimum_support": MIN_CODETECTION_SUPPORT})

    cohort_summary = {
        "n": n,
        "prefilter_species": len(taxa),
        "detected_species_per_sample": quantiles([float(value) for value in detected]),
        "species_direct_assigned_reads_per_sample": quantiles([float(value) for value in totals]),
        "top1_dominance": quantiles(top1), "top3_dominance": quantiles(top3),
        "detected_species_bins": {key: {"n": bins[key], "proportion": bins[key] / n} for key in ("0", "1", "2", "3", "4-5", ">5")},
        "candidate_panel_size": len(panel_taxa),
        "panel_structure": {key: {"n": structure_total[key], "proportion": structure_total[key] / n} for key in ("no_panel_pathogen_detected", "single_panel_pathogen", "two_panel_pathogens", "three_or_more_panel_pathogens")},
        "panel_structure_by_group": {group: dict(counter) for group, counter in sorted(structure_by_group.items())},
        "dominant_pathogen_by_group": {group: dict(counter) for group, counter in sorted(dominant_by_group.items())},
        "top_pathogens_by_panel_prevalence": [row["scientific_name"] for row in sorted((metric_by_taxid[t["taxid"]] for t in panel_taxa), key=lambda row: (-row["detection_prevalence"], -row["total_direct_assigned_reads"], row["scientific_name"]))[:5]],
    }
    tables = {
        "sample": sample_rows, "dominant": dominant_rows, "group": group_rows,
        "feasibility": feasibility_rows, "codetection": codetection_rows,
        "top_prevalence": ranked(metrics, "detection_prevalence"),
        "top_reads": ranked(metrics, "total_direct_assigned_reads"),
        "top_median": ranked(metrics, "median_direct_assigned_reads_among_positive"),
        "metrics": metrics, "panel_taxa": panel_taxa,
    }
    return cohort_summary, tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-counts", type=Path, required=True)
    parser.add_argument("--external-counts", type=Path, required=True)
    parser.add_argument("--anchor-metadata", type=Path, required=True)
    parser.add_argument("--external-metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists():
        raise RuntimeError("audit output already exists")
    args.output_dir.mkdir(parents=True)
    inputs = {
        "anchor": (args.anchor_counts, args.anchor_metadata),
        "external": (args.external_counts, args.external_metadata),
    }
    summaries, tables = {}, {}
    matrices = {}
    for cohort, (counts, metadata) in inputs.items():
        matrices[cohort] = read_matrix(counts, cohort)
        summaries[cohort], tables[cohort] = audit_cohort(cohort, matrices[cohort], read_groups(metadata, cohort))

    panel_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for cohort in ("anchor", "external"):
        for taxon in tables[cohort]["panel_taxa"]:
            key = (taxon["taxid"], taxon["scientific_name"])
            row = panel_by_key.setdefault(key, {
                "taxid": taxon["taxid"], "scientific_name": taxon["scientific_name"],
                "clinical_pathogen_relevance_flag": relevance(taxon["scientific_name"]),
                "curation_source": "existing_repository_target_priority_or_user_specified_candidate",
                "taxonomic_ambiguity": "none_observed_for_exact_taxid_name",
                "observed_anchor": False, "observed_external": False,
                "panel_status": "candidate_for_scientific_review",
            })
            row[f"observed_{cohort}"] = True
            if taxon["scientific_name"] in matrices[cohort]["ambiguous_names"]:
                row["taxonomic_ambiguity"] = "scientific_name_maps_to_multiple_taxids"
    panel_rows = sorted(panel_by_key.values(), key=lambda row: (row["scientific_name"], row["taxid"]))

    sample_rows = tables["anchor"]["sample"] + tables["external"]["sample"]
    dominant_rows = tables["anchor"]["dominant"] + tables["external"]["dominant"]
    group_rows = tables["anchor"]["group"] + tables["external"]["group"]
    feasibility_rows = tables["anchor"]["feasibility"] + tables["external"]["feasibility"]
    codetection_rows = tables["anchor"]["codetection"] + tables["external"]["codetection"]

    for label, table_key, filename in (
        ("detection_prevalence", "top_prevalence", "top_species_prevalence.json"),
        ("total_direct_assigned_reads", "top_reads", "top_species_reads.json"),
        ("median_signal_among_positive", "top_median", "top_species_median_positive.json"),
    ):
        rows = []
        for cohort in ("anchor", "external"):
            rows.extend({"cohort": cohort, "ranking": label, "rank": rank, **row} for rank, row in enumerate(tables[cohort][table_key], 1))
        write_json_rows(args.output_dir / filename, rows)

    write_json_rows(args.output_dir / "sample_detection_summary.json", sample_rows)
    write_json_rows(args.output_dir / "candidate_pathogen_panel.json", panel_rows)
    write_json_rows(args.output_dir / "group_pathogen_detection.json", group_rows)
    write_json_rows(args.output_dir / "pathogen_codetection.json", codetection_rows)
    write_json_rows(args.output_dir / "dominant_pathogen.json", dominant_rows)
    write_json_rows(args.output_dir / "signal_feasibility.json", feasibility_rows)

    background_rows = []
    seen = set()
    for cohort in ("anchor", "external"):
        top_union = tables[cohort]["top_prevalence"] + tables[cohort]["top_reads"] + tables[cohort]["top_median"]
        for row in top_union:
            key = (cohort, row["taxid"])
            if key in seen:
                continue
            seen.add(key)
            name = row["scientific_name"]
            reasons = []
            action = "manual_literature_or_clinical_review_before_panel_inclusion"
            if name in BACKGROUND:
                reasons.append("existing_repository_background_or_low_specificity_flag")
                action = "retain_for_QC_review;exclude_only_under_documented_rule"
            if name in COMMENSALS:
                reasons.append("existing_repository_oral_respiratory_commensal_context")
            if row["median_direct_assigned_reads_among_positive"] <= 1:
                reasons.append("median_positive_signal_is_one_direct_read")
            if name in matrices[cohort]["ambiguous_names"]:
                reasons.append("scientific_name_maps_to_multiple_taxids")
            if relevance(name) == "uncertain":
                reasons.append("clinical_relevance_not_locally_curated")
            if reasons:
                background_rows.append({
                    "cohort": cohort, "taxid": row["taxid"], "scientific_name": name,
                    "reason_for_flag": ";".join(reasons), "frequency": row["positive_sample_count"],
                    "detection_prevalence": row["detection_prevalence"],
                    "typical_read_level": row["median_direct_assigned_reads_among_positive"],
                    "recommended_action_for_review": action,
                })
    write_json_rows(args.output_dir / "background_flag_review.json", background_rows)

    jaccard_reason = "NOT_RUN_WITH_REASON: candidate pathogen panel is provisional and requires scientific/manual review before confirmatory profile-distance testing"
    summary = {
        "schema_version": 1,
        "analysis": "REAL_530_PATHOGEN_DETECTION_LANDSCAPE_AUDIT",
        "cohorts_analyzed_independently": True,
        "input_hashes": {f"{cohort}_{kind}": sha256(path) for cohort, paths in inputs.items() for kind, path in zip(("direct_species_counts", "metadata"), paths)},
        "cohorts": summaries,
        "candidate_pathogen_panel_size_union": len(panel_rows),
        "candidate_panel_is_final_clinical_definition": False,
        "codetection_minimum_support": MIN_CODETECTION_SUPPORT,
        "exploratory_pathogen_tests": "NOT_RUN",
        "jaccard_profile_analysis": {"status": "NOT_RUN", "reason": jaccard_reason},
        "methods_not_executed": ["CZM", "CLR/Aitchison", "ANCOM-BC2", "ALDEx2", "PERMANOVA", "PERMDISP", "Bray-Curtis", "regression"],
        "network_acquisition_performed": False,
        "package_installation_performed": False,
        "kraken2_rerun": False,
        "bracken_executed": False,
        "deepseek_invoked": False,
    }
    (args.output_dir / "pathogen_landscape_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = f"""# Manuscript utility assessment: pathogen-detection landscape

This bounded audit supports a pathogen-profile framing, not a generic high-diversity microbiome claim. The anchor cohort offers the strongest scientific angle: disease-associated lower-airway pathogen detection spectra across four clinically labeled pulmonary groups. The external cohort adds a distinct, focused within-TB drug-resistance landscape and must not be described as replication or validation of the anchor contrast.

The weakest point is that direct classifier detections—especially low-count and broadly recurrent taxa—cannot establish etiology and lack matched negative-control or wet-lab confirmation. The two cohorts can support one paper if analyzed and interpreted as separate estimands. External-cohort value is **MODERATE**. A third cohort is not currently required for a descriptive landscape paper, but independent clinical or wet-lab validation would materially strengthen generalizability and etiologic interpretation.

## Proposed main figures

1. Study design, cohort structure, and per-sample detection/richness and dominance distributions.
2. Top pathogen prevalence and dominant candidate-pathogen profiles across anchor diagnosis groups.
3. No/single/multiple panel-pathogen structure and supported co-detection patterns (support ≥{MIN_CODETECTION_SUPPORT}; no interaction claims).
4. Candidate-panel presence/absence profile analysis only after panel review; currently `{jaccard_reason}`.
5. External within-TB drug-resistance pathogen landscape, explicitly separate from anchor inference.
6. Selected pathogen detection and positive-signal feasibility with low-count/background flags.

Total species direct-assigned reads are technical classifier signal and are not interpreted as microbial biomass. No taxon was removed by this audit.
"""
    (args.output_dir / "manuscript_utility.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
