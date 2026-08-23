#!/usr/bin/env python3
"""Build separate cohort-native Kraken2 direct-assignment sensitivity layers.

This program is read-only with respect to Kraken2 reports. It does not invoke a
classifier, abundance estimator, trimmer, host-removal tool, or downloader.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


LAYER = "COMMON_NATIVE_KRAKEN2_CLASSIFIER_ASSIGNMENT_LAYER"
ANCHOR = "PRJNA1056765"
EXTERNAL = "PRJCA046985"
ANCHOR_N = 400
EXTERNAL_N = 130
PILOT_JOB = "20260822T120000Z-prjca046985-native-kraken2-pilot"
PRODUCTION_JOB = "20260822T175547Z-prjca046985-122-native-kraken2-recovery"
QC_JOB = "20260823T043904Z-prjca046985-122-native-kraken2-production-qc"
DB_IDENTITY = "6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3"
RANKS = ("S", "G")
PERMUTATIONS = 999


class LayerError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise LayerError(f"JSON object required: {path}")
    return value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clean_text(value: str) -> str:
    return " ".join(value.replace("\t", " ").replace("\r", " ").replace("\n", " ").split())


def parse_report(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise LayerError(f"report is missing, non-regular, or symlinked: {path}")
    taxa: dict[str, dict[int, tuple[str, int, int]]] = {rank: {} for rank in RANKS}
    root_classified: int | None = None
    unclassified: int | None = None
    parsed_lines = 0
    with path.open("r", encoding="utf-8", errors="strict") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            fields = raw.rstrip("\n").split("\t", 5)
            if len(fields) != 6:
                raise LayerError(f"malformed Kraken2 report line {line_number}: {path}")
            _percent, clade_raw, direct_raw, rank, taxid_raw, name_raw = fields
            try:
                clade = int(clade_raw)
                direct = int(direct_raw)
                taxid = int(taxid_raw)
            except ValueError as exc:
                raise LayerError(f"non-integer Kraken2 count/taxid at line {line_number}: {path}") from exc
            if min(clade, direct, taxid) < 0 or direct > clade:
                raise LayerError(f"invalid Kraken2 counts at line {line_number}: {path}")
            name = clean_text(name_raw)
            if not name:
                raise LayerError(f"empty scientific name at line {line_number}: {path}")
            parsed_lines += 1
            if taxid == 0 and "unclassified" in name.lower():
                if unclassified is not None:
                    raise LayerError(f"duplicate unclassified row: {path}")
                unclassified = clade
            if rank == "R" and taxid == 1:
                if root_classified is not None:
                    raise LayerError(f"duplicate root row: {path}")
                root_classified = clade
            if rank in taxa:
                if taxid in taxa[rank]:
                    raise LayerError(f"duplicate taxid {taxid} at rank {rank}: {path}")
                taxa[rank][taxid] = (name, direct, clade)
    if not parsed_lines or root_classified is None or unclassified is None:
        raise LayerError(f"report lacks required root/unclassified accounting: {path}")
    total = root_classified + unclassified
    if total <= 0:
        raise LayerError(f"zero total input reads: {path}")
    for rank in RANKS:
        if sum(row[1] for row in taxa[rank].values()) > root_classified:
            raise LayerError(f"direct {rank} counts exceed classified reads: {path}")
    return {
        "path": str(path),
        "total_input_reads": total,
        "classified_reads": root_classified,
        "unclassified_reads": unclassified,
        "classified_fraction": root_classified / total,
        "taxa": taxa,
    }


def matrix_taxa(samples: list[dict[str, Any]], rank: str) -> list[tuple[int, str]]:
    names: dict[int, str] = {}
    for sample in samples:
        for taxid, (name, _direct, _clade) in sample["report"]["taxa"][rank].items():
            if taxid in names and names[taxid] != name:
                raise LayerError(f"taxid/name ambiguity at rank {rank}: {taxid}")
            names[taxid] = name
    return sorted(names.items(), key=lambda row: (row[1].lower(), row[0]))


def fmt(value: float | int | None) -> str:
    if value is None:
        return "NA"
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        return "NA"
    return f"{value:.10g}"


def write_tsv(path: Path, header: list[str], rows: Iterable[Iterable[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([fmt(x) if isinstance(x, (int, float)) or x is None else clean_text(str(x)) for x in row])


def direct_count(sample: dict[str, Any], rank: str, taxid: int) -> int:
    row = sample["report"]["taxa"][rank].get(taxid)
    return row[1] if row else 0


def prevalence(samples: list[dict[str, Any]], rank: str, taxid: int) -> float:
    return sum(direct_count(sample, rank, taxid) > 0 for sample in samples) / len(samples)


def ecological_metrics(sample: dict[str, Any]) -> dict[str, float | int | None]:
    counts = [row[1] for row in sample["report"]["taxa"]["S"].values() if row[1] > 0]
    assigned = sum(counts)
    if not assigned:
        return {"species_direct_reads": 0, "richness": 0, "shannon": None, "gini_simpson": None, "dominance": None}
    proportions = [count / assigned for count in counts]
    return {
        "species_direct_reads": assigned,
        "richness": len(counts),
        "shannon": -sum(p * math.log(p) for p in proportions),
        "gini_simpson": 1 - sum(p * p for p in proportions),
        "dominance": max(proportions),
    }


def bray_curtis(vectors: list[list[float]]) -> list[list[float]]:
    n = len(vectors)
    result = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            numerator = sum(abs(a - b) for a, b in zip(vectors[i], vectors[j]))
            denominator = sum(a + b for a, b in zip(vectors[i], vectors[j]))
            value = numerator / denominator if denominator else 0.0
            result[i][j] = result[j][i] = value
    return result


def permanova_stat(distance: list[list[float]], labels: list[str]) -> tuple[float, float]:
    n = len(labels)
    groups = sorted(set(labels))
    if len(groups) < 2 or len(groups) >= n:
        raise LayerError("PERMANOVA requires at least two non-singleton groups")
    total_ss = sum(distance[i][j] ** 2 for i in range(n) for j in range(i)) / n
    within_ss = 0.0
    for group in groups:
        ids = [i for i, label in enumerate(labels) if label == group]
        if len(ids) < 2:
            raise LayerError("PERMANOVA singleton clinical group")
        within_ss += sum(distance[ids[a]][ids[b]] ** 2 for a in range(len(ids)) for b in range(a)) / len(ids)
    between_ss = max(total_ss - within_ss, 0.0)
    df_between = len(groups) - 1
    df_within = n - len(groups)
    pseudo_f = (between_ss / df_between) / (within_ss / df_within) if within_ss else math.inf
    r2 = between_ss / total_ss if total_ss else 0.0
    return pseudo_f, r2


def dispersion_stat(distance: list[list[float]], labels: list[str]) -> tuple[float, float]:
    groups = sorted(set(labels))
    z = [0.0] * len(labels)
    for group in groups:
        ids = [i for i, label in enumerate(labels) if label == group]
        n_group = len(ids)
        if n_group < 2:
            raise LayerError("PERMDISP singleton clinical group")
        pair_term = sum(distance[ids[a]][ids[b]] ** 2 for a in range(n_group) for b in range(a)) / (n_group * n_group)
        for i in ids:
            point_term = sum(distance[i][j] ** 2 for j in ids) / n_group
            z[i] = math.sqrt(max(point_term - pair_term, 0.0))
    grand = statistics.mean(z)
    ss_between = sum(sum(labels[i] == g for i in range(len(labels))) * (statistics.mean(z[i] for i in range(len(labels)) if labels[i] == g) - grand) ** 2 for g in groups)
    ss_within = sum((z[i] - statistics.mean(z[j] for j in range(len(labels)) if labels[j] == labels[i])) ** 2 for i in range(len(labels)))
    df_between = len(groups) - 1
    df_within = len(labels) - len(groups)
    f_value = (ss_between / df_between) / (ss_within / df_within) if ss_within else math.inf
    r2 = ss_between / (ss_between + ss_within) if ss_between + ss_within else 0.0
    return f_value, r2


def permutation_test(distance: list[list[float]], labels: list[str], fn, seed: int) -> tuple[float, float, float]:
    observed, effect = fn(distance, labels)
    rng = random.Random(seed)
    exceed = 0
    permuted = list(labels)
    for _ in range(PERMUTATIONS):
        rng.shuffle(permuted)
        value, _effect = fn(distance, permuted)
        if value >= observed - 1e-12:
            exceed += 1
    return observed, effect, (exceed + 1) / (PERMUTATIONS + 1)


def eta_squared(values: list[float], labels: list[str]) -> float | None:
    if len(values) < 2 or len(set(labels)) < 2:
        return None
    grand = statistics.mean(values)
    total = sum((x - grand) ** 2 for x in values)
    between = sum(sum(label == group for label in labels) * (statistics.mean(x for x, label in zip(values, labels) if label == group) - grand) ** 2 for group in set(labels))
    return between / total if total else 0.0


def hedges_g(values: list[float], labels: list[str], positive: str, negative: str) -> float | None:
    a = [x for x, label in zip(values, labels) if label == positive]
    b = [x for x, label in zip(values, labels) if label == negative]
    if len(a) < 2 or len(b) < 2:
        return None
    variance = ((len(a) - 1) * statistics.variance(a) + (len(b) - 1) * statistics.variance(b)) / (len(a) + len(b) - 2)
    if variance <= 0:
        return 0.0
    d = (statistics.mean(a) - statistics.mean(b)) / math.sqrt(variance)
    correction = 1 - 3 / (4 * (len(a) + len(b)) - 9)
    return d * correction


def cramers_v(detected: list[bool], labels: list[str]) -> float | None:
    groups = sorted(set(labels))
    n = len(labels)
    if n == 0 or len(groups) < 2:
        return None
    columns = [True, False]
    row_totals = {g: sum(label == g for label in labels) for g in groups}
    col_totals = {v: sum(x == v for x in detected) for v in columns}
    chi2 = 0.0
    for group in groups:
        for value in columns:
            observed = sum(label == group and x == value for label, x in zip(labels, detected))
            expected = row_totals[group] * col_totals[value] / n
            if expected:
                chi2 += (observed - expected) ** 2 / expected
    return math.sqrt(chi2 / n) if n else None


def log_odds_ratio(detected: list[bool], labels: list[str]) -> tuple[float | None, str]:
    a = sum(x and label == "Drug_Resistance" for x, label in zip(detected, labels))
    b = sum((not x) and label == "Drug_Resistance" for x, label in zip(detected, labels))
    c = sum(x and label == "Drug_Sensitive" for x, label in zip(detected, labels))
    d = sum((not x) and label == "Drug_Sensitive" for x, label in zip(detected, labels))
    if min(a, b, c, d) < 5:
        return None, f"inadequate event cells: {a},{b},{c},{d}"
    return math.log((a * d) / (b * c)), f"cells={a},{b},{c},{d}"


def validate_sources(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reconciliation = read_json(args.anchor_reconciliation)
    if not (reconciliation.get("native_400_exact") is True and reconciliation.get("native_kreport_files") == ANCHOR_N and reconciliation.get("native_kreport_unique_runs") == ANCHOR_N):
        raise LayerError("anchor reconciliation gate failed")
    anchor_meta = read_tsv(args.anchor_clinical)
    anchor_ids = [row.get("run", "") for row in anchor_meta]
    if len(anchor_ids) != ANCHOR_N or len(set(anchor_ids)) != ANCHOR_N:
        raise LayerError("anchor clinical membership is not exactly 400 unique runs")

    pilot_job = read_json(args.pilot_job)
    pilot_rows = pilot_job.get("params", {}).get("pilot_runs", [])
    pilot_ids = [row.get("run_accession", "") for row in pilot_rows]
    if pilot_job.get("job_id") != PILOT_JOB or len(pilot_ids) != 8 or len(set(pilot_ids)) != 8:
        raise LayerError("pilot membership gate failed")
    pilot_summary = read_json(args.pilot_summary)
    if pilot_summary.get("final_status") != "done" or {row.get("run_accession") for row in pilot_summary.get("runs", [])} != set(pilot_ids):
        raise LayerError("pilot completion gate failed")

    production = read_json(args.production_definition)
    production_ids = [row.get("id", "") for row in production.get("items", [])]
    if production.get("job_id") != PRODUCTION_JOB or production.get("acquire") is not False or len(production_ids) != 122 or len(set(production_ids)) != 122 or set(production_ids) & set(pilot_ids):
        raise LayerError("production membership gate failed")
    production_qc = read_json(args.production_qc)
    if production_qc.get("recovery_job_id") != PRODUCTION_JOB or production_qc.get("status") != "VERIFIED" or production_qc.get("verified_runs") != 122:
        raise LayerError("production QC gate failed")
    recovery_result = read_json(args.recovery_result)
    if recovery_result.get("job_id") != PRODUCTION_JOB or recovery_result.get("status") != "done":
        raise LayerError("production result gate failed")

    external_meta = read_tsv(args.external_manifest)
    external_by_id = {row.get("run_accession", ""): row for row in external_meta}
    expected_external = set(pilot_ids) | set(production_ids)
    if len(external_meta) != EXTERNAL_N or len(external_by_id) != EXTERNAL_N or set(external_by_id) != expected_external:
        raise LayerError("external 130-run manifest gate failed")

    anchor_samples: list[dict[str, Any]] = []
    for row in sorted(anchor_meta, key=lambda value: value["run"]):
        run = row["run"]
        candidates = list(args.anchor_results_root.glob(f"prjna1056765_production_descriptive_batch_*/kraken2/{run}.kreport"))
        if len(candidates) != 1 or "bracken" in candidates[0].name.lower():
            raise LayerError(f"anchor native report membership failure: {run} ({len(candidates)})")
        anchor_samples.append({"run": run, "group": row.get("diagnosis", ""), "report": parse_report(candidates[0])})

    external_samples: list[dict[str, Any]] = []
    for run in sorted(expected_external):
        if run in pilot_ids:
            report_path = args.external_results_root / PILOT_JOB / "native_kraken2" / f"{run}.native.kreport"
        else:
            report_path = args.external_results_root / f"{PRODUCTION_JOB}__{run}.native.kreport"
        external_samples.append({"run": run, "group": external_by_id[run].get("group_raw", ""), "report": parse_report(report_path)})
    return anchor_samples, external_samples


def write_cohort_outputs(out: Path, prefix: str, samples: list[dict[str, Any]]) -> dict[str, Any]:
    sample_ids = [sample["run"] for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise LayerError(f"duplicate sample IDs: {prefix}")
    metrics_by_run: dict[str, dict[str, Any]] = {}
    qc_rows = []
    for sample in samples:
        report = sample["report"]
        eco = ecological_metrics(sample)
        genus_direct = sum(row[1] for row in report["taxa"]["G"].values())
        metrics_by_run[sample["run"]] = {**eco, "classified_fraction": report["classified_fraction"], "total_reads": report["total_input_reads"], "classified_reads": report["classified_reads"]}
        qc_rows.append([
            sample["run"], sample["group"], report["total_input_reads"], report["classified_reads"], report["unclassified_reads"], report["classified_fraction"],
            eco["species_direct_reads"], genus_direct, eco["richness"], eco["shannon"], eco["gini_simpson"], eco["dominance"], report["path"],
        ])
    write_tsv(out / f"{prefix}_sample_qc.tsv", ["run", "clinical_group", "total_input_reads", "classified_reads", "unclassified_reads", "classified_fraction", "species_direct_reads", "genus_direct_reads", "richness", "shannon", "gini_simpson", "dominance", "report_path"], qc_rows)

    rank_taxa: dict[str, list[tuple[int, str]]] = {}
    for rank, label in (("S", "species"), ("G", "genus")):
        taxa = matrix_taxa(samples, rank)
        rank_taxa[rank] = taxa
        prevalence_by_taxid = {taxid: prevalence(samples, rank, taxid) for taxid, _name in taxa}
        base_header = ["taxid", "rank", "scientific_name", "prevalence", "present_5pct", "present_10pct", "present_20pct", *sample_ids]
        metadata = lambda taxid, name: [taxid, rank, name, prevalence_by_taxid[taxid], prevalence_by_taxid[taxid] >= 0.05, prevalence_by_taxid[taxid] >= 0.10, prevalence_by_taxid[taxid] >= 0.20]
        write_tsv(out / f"{prefix}_{label}_direct_counts.tsv", base_header, (metadata(taxid, name) + [direct_count(sample, rank, taxid) for sample in samples] for taxid, name in taxa))
        write_tsv(out / f"{prefix}_{label}_fraction_all_reads.tsv", base_header, (metadata(taxid, name) + [direct_count(sample, rank, taxid) / sample["report"]["total_input_reads"] for sample in samples] for taxid, name in taxa))
        write_tsv(out / f"{prefix}_{label}_fraction_classified_reads.tsv", base_header, (metadata(taxid, name) + [direct_count(sample, rank, taxid) / sample["report"]["classified_reads"] if sample["report"]["classified_reads"] else 0.0 for sample in samples]))

    species_10 = [taxid for taxid, _name in rank_taxa["S"] if prevalence_by_rank(samples, "S", taxid) >= 0.10]
    vectors = [[direct_count(sample, "S", taxid) / sample["report"]["total_input_reads"] for taxid in species_10] for sample in samples]
    distance = bray_curtis(vectors)
    labels = [sample["group"] for sample in samples]
    permanova = permutation_test(distance, labels, permanova_stat, 1056765 if prefix == "anchor" else 460985)
    permdisp = permutation_test(distance, labels, dispersion_stat, 2056765 if prefix == "anchor" else 1460985)
    return {"samples": samples, "taxa": rank_taxa, "metrics": metrics_by_run, "permanova": permanova, "permdisp": permdisp, "species_10_taxids": species_10}


def prevalence_by_rank(samples: list[dict[str, Any]], rank: str, taxid: int) -> float:
    return prevalence(samples, rank, taxid)


def build(args: argparse.Namespace) -> dict[str, Any]:
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    anchor_samples, external_samples = validate_sources(args)
    if len(anchor_samples) != ANCHOR_N or len(external_samples) != EXTERNAL_N:
        raise LayerError("valid report count gate failed")
    anchor = write_cohort_outputs(out, "anchor", anchor_samples)
    external = write_cohort_outputs(out, "external", external_samples)

    dictionary: dict[tuple[str, int], dict[str, Any]] = {}
    for cohort_name, cohort in (("anchor", anchor), ("external", external)):
        for rank in RANKS:
            for taxid, name in cohort["taxa"][rank]:
                key = (rank, taxid)
                if key in dictionary and dictionary[key]["name"] != name:
                    raise LayerError(f"cross-cohort taxid/name ambiguity: {rank}/{taxid}")
                dictionary.setdefault(key, {"name": name, "anchor": False, "external": False})[cohort_name] = True
    write_tsv(out / "taxon_dictionary.tsv", ["taxid", "rank", "scientific_name", "observed_anchor", "observed_external"], ([taxid, rank, row["name"], row["anchor"], row["external"]] for (rank, taxid), row in sorted(dictionary.items(), key=lambda x: (x[0][0], x[1]["name"].lower(), x[0][1]))))

    overlap_rows = []
    common_counts = {"S": 0, "G": 0}
    for (rank, taxid), row in sorted(dictionary.items(), key=lambda x: (x[0][0], x[1]["name"].lower(), x[0][1])):
        pa = prevalence(anchor_samples, rank, taxid)
        pe = prevalence(external_samples, rank, taxid)
        common = pa >= 0.10 and pe >= 0.10
        common_counts[rank] += int(common)
        overlap_rows.append([taxid, rank, row["name"], pa, pe, pa >= 0.10, pe >= 0.10, common])
    write_tsv(out / "cross_cohort_taxon_overlap.tsv", ["taxid", "rank", "name", "anchor_prevalence", "external_prevalence", "present_anchor_10pct", "present_external_10pct", "common_10pct"], overlap_rows)

    metric_names = ["richness", "shannon", "gini_simpson", "dominance", "classified_fraction"]
    effect_rows = []
    for prefix, cohort in (("anchor", anchor), ("external", external)):
        labels = [sample["group"] for sample in cohort["samples"]]
        for metric in metric_names:
            pairs = [(cohort["metrics"][sample["run"]][metric], sample["group"]) for sample in cohort["samples"] if cohort["metrics"][sample["run"]][metric] is not None]
            values = [float(value) for value, _label in pairs]
            kept_labels = [label for _value, label in pairs]
            if prefix == "anchor":
                effect_type, effect = "eta_squared_four_group", eta_squared(values, kept_labels)
            else:
                effect_type, effect = "hedges_g_Drug_Resistance_minus_Drug_Sensitive", hedges_g(values, kept_labels, "Drug_Resistance", "Drug_Sensitive")
            effect_rows.append([prefix, metric, len(values), "|".join(sorted(set(kept_labels))), effect_type, effect, "cohort-specific; no cross-contrast pooling"])
        for test_name, result in (("Bray-Curtis PERMANOVA", cohort["permanova"]), ("Bray-Curtis PERMDISP", cohort["permdisp"])):
            effect_rows.append([prefix, test_name, len(labels), "|".join(sorted(set(labels))), "R2", result[1], f"pseudo_F={fmt(result[0])}; permutations={PERMUTATIONS}; p={fmt(result[2])}"])

    common_species = [row for row in overlap_rows if row[1] == "S" and row[7] is True]
    for taxid, rank, name, _pa, _pe, _a10, _e10, _common in common_species:
        for prefix, cohort in (("anchor", anchor), ("external", external)):
            detected = [direct_count(sample, rank, taxid) > 0 for sample in cohort["samples"]]
            labels = [sample["group"] for sample in cohort["samples"]]
            if prefix == "anchor":
                effect_type, effect, detail = "cramers_v_four_group_prevalence", cramers_v(detected, labels), "omnibus four-group association"
            else:
                effect_type = "log_odds_ratio_Drug_Resistance_vs_Drug_Sensitive"
                effect, detail = log_odds_ratio(detected, labels)
            effect_rows.append([prefix, f"species prevalence taxid={taxid} {name}", len(labels), "|".join(sorted(set(labels))), effect_type, effect, detail])
    write_tsv(out / "cohort_effect_estimates.tsv", ["cohort", "estimand", "n", "clinical_groups", "effect_type", "effect_size", "detail"], effect_rows)

    statistic_rows = []
    for prefix, cohort in (("anchor", anchor), ("external", external)):
        for test_name, result in (("PERMANOVA", cohort["permanova"]), ("PERMDISP", cohort["permdisp"])):
            statistic_rows.append([prefix, "Bray-Curtis on cohort-specific >=10% species direct/all-read fractions", test_name, len(cohort["samples"]), len(set(sample["group"] for sample in cohort["samples"])), result[0], result[1], result[2], PERMUTATIONS])
    write_tsv(out / "within_cohort_statistics.tsv", ["cohort", "feature_space", "test", "n", "groups", "statistic", "R2", "permutation_p", "permutations"], statistic_rows)

    estimands = [
        ("Shannon diversity difference", "Species direct-count subcomposition; four-level diagnosis omnibus eta-squared", "Same metric; DR minus DS Hedges g"),
        ("Richness difference", "Direct species with count >0; four-level diagnosis omnibus eta-squared", "Same metric; DR minus DS Hedges g"),
        ("Gini-Simpson difference", "Species direct-count subcomposition; four-level diagnosis omnibus eta-squared", "Same metric; DR minus DS Hedges g"),
        ("Dominance difference", "Maximum species direct-count share; four-level diagnosis omnibus eta-squared", "Same metric; DR minus DS Hedges g"),
        ("Beta-dispersion difference", "Bray-Curtis PERMDISP on anchor-specific 10% species layer", "Bray-Curtis PERMDISP on external-specific 10% species layer"),
        ("Classified fraction difference", "Technical Kraken2 classified/all-input fraction; four-level diagnosis", "Technical Kraken2 classified/all-input fraction; DR versus DS"),
        ("Prevalence of common taxa", "Four-group Cramer's V", "DR-versus-DS log odds ratio when all cells >=5"),
        ("Direction/effect of shared >=10% taxa", "Four-group omnibus prevalence effect has no single direction", "Binary prevalence direction available where cells adequate"),
    ]
    estimand_rows = [[name, adef, edef, True, True, True, False, False, "Metric can be computed identically, but the clinical contrasts are not equivalent; no formal meta-analysis."] for name, adef, edef in estimands]
    write_tsv(out / "common_estimand_audit.tsv", ["estimand", "anchor_definition", "external_definition", "anchor_effect_available", "external_effect_available", "same_estimand", "same_contrast", "meta_analysis_ready", "reason"], estimand_rows)

    anchor_classified = statistics.median(sample["report"]["classified_fraction"] for sample in anchor_samples)
    external_classified = statistics.median(sample["report"]["classified_fraction"] for sample in external_samples)
    validation = {
        "layer": LAYER,
        "status": "VERIFIED",
        "anchor_valid_reports": len(anchor_samples),
        "external_valid_reports": len(external_samples),
        "anchor_unique_runs": len({sample["run"] for sample in anchor_samples}),
        "external_unique_runs": len({sample["run"] for sample in external_samples}),
        "species_taxa_anchor": len(anchor["taxa"]["S"]),
        "species_taxa_external": len(external["taxa"]["S"]),
        "species_taxa_common_10pct": common_counts["S"],
        "genus_taxa_anchor": len(anchor["taxa"]["G"]),
        "genus_taxa_external": len(external["taxa"]["G"]),
        "genus_taxa_common_10pct": common_counts["G"],
        "anchor_classified_fraction_median": anchor_classified,
        "external_classified_fraction_median": external_classified,
        "common_estimands_identified": len(estimands),
        "formal_meta_analysis_ready": False,
        "prevalence_thresholds": [0.05, 0.10, 0.20],
        "prevalence_computed_within_cohort": True,
        "pooled_530_matrix_created": False,
        "direct_and_clade_counts_parsed_separately": True,
        "primary_matrix_count_field": "direct_assigned_reads",
        "fractions": ["fraction_all_reads", "fraction_classified_reads"],
        "permanova_paired_with_permdisp": True,
        "permutations": PERMUTATIONS,
        "database_identity": DB_IDENTITY,
        "kraken2_rerun": False,
        "bracken_rerun": False,
        "host_removal": False,
        "raw_data_downloaded": False,
    }
    (out / "matrix_validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = f"""# Common native Kraken2 classifier-assignment layer

Status: **VERIFIED**

- Layer: `{LAYER}`
- Anchor: {ANCHOR}, {len(anchor_samples)}/400 valid native reports
- External: {EXTERNAL}, {len(external_samples)}/130 valid native reports
- Primary matrices: direct S/G assignments; clade counts were parsed and validated separately, never substituted
- Fractions: direct assignments divided by all input reads (primary) and by classified reads (retained sensitivity)
- Prevalence: 5%, 10%, and 20% calculated separately within each cohort
- Bray-Curtis: cohort-specific 10% species layer; PERMANOVA paired with PERMDISP ({PERMUTATIONS} permutations)
- Pooled 530-sample matrix: not created
- Formal meta-analysis ready: no; clinical contrasts differ

Species taxa: anchor {len(anchor['taxa']['S'])}, external {len(external['taxa']['S'])}, common at 10% {common_counts['S']}.
Genus taxa: anchor {len(anchor['taxa']['G'])}, external {len(external['taxa']['G'])}, common at 10% {common_counts['G']}.

Classified fraction is technical classifier behavior and is not bacterial load. Diversity metrics are computed from the direct-species subcomposition and remain sensitivity/ecological descriptors. No supervised dysbiosis index was trained; such a model requires discovery, a frozen specification, and external validation.
"""
    (out / "common_layer_summary.md").write_text(summary, encoding="utf-8")
    (out / "README.md").write_text("""# Common Kraken2 assignment layer artifacts

These files were derived read-only from existing native Kraken2 reports. Matrix rows are taxa and columns are samples. Counts are reads assigned directly at the named rank; clade counts were parsed separately for validation and are not substituted. Zero means absent from a valid report. A missing or invalid report fails the complete job and is never encoded as zero.

No pooled 530-sample matrix, raw reads, Kraken2 rerun, Bracken rerun, trimming, or host removal is included.
""", encoding="utf-8")
    return validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-reconciliation", type=Path, required=True)
    parser.add_argument("--anchor-clinical", type=Path, required=True)
    parser.add_argument("--external-manifest", type=Path, required=True)
    parser.add_argument("--pilot-job", type=Path, required=True)
    parser.add_argument("--pilot-summary", type=Path, required=True)
    parser.add_argument("--production-definition", type=Path, required=True)
    parser.add_argument("--production-qc", type=Path, required=True)
    parser.add_argument("--recovery-result", type=Path, required=True)
    parser.add_argument("--anchor-results-root", type=Path, required=True)
    parser.add_argument("--external-results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        result = build(parse_args())
        print(json.dumps(result, sort_keys=True))
    except (LayerError, OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        raise SystemExit(f"SAFE_STOP: {clean_text(str(exc))}")
