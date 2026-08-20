#!/usr/bin/env python3
"""Run the immutable PRJNA1056765 robustness grid defined on 2026-08-20.

This script writes new sensitivity outputs only. It never overwrites the frozen
400-run formal analysis. The plan and script hashes must match the constants
below or execution aborts.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "frozen_sensitivity_plan.md"
PLAN_LOCK = ROOT / "frozen_sensitivity_plan.sha256"
QC = ROOT / "reports_public/metagenome_400_formal/qc/cohort_qc.tsv"
QC_SHA256 = "e3e4cfbdaf412d20bd9ee6dd82e1e811d12046556b176adf0678c34c6373f790"
MATRIX = ROOT / "reports_public/metagenome_production/bracken_species_fraction_matrix.tsv"
MATRIX_SHA256 = "0c7ad6930c4e2db5fd3ec0a58861850274eb75dd31350ab00f4428a41a6ad20d"
CLINICAL = ROOT / "reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv"
CLINICAL_SHA256 = "3de4e218e8f0e9e32545cead271e6750c39ac0dea4c47df291123175292400be"
ANCHOR_SPECIES = ROOT / "frozen_anchor_species.tsv"
ANCHOR_SPECIES_SHA256 = "1fea6bdb0199c9ab218c1f1f098b524a4f1f9a774a93f4cdef7b11ee1a655833"
OUT = ROOT / "reports_public/metagenome_400_sensitivity_v2"
HEADER = [
    "population", "prevalence_threshold", "prevalence_count", "metric",
    "pseudocount_rule", "pseudocount_value", "is_anchor_replay", "n",
    "retained_features", "permanova_F", "permanova_R2", "permanova_p",
    "permdisp_F", "permdisp_R2", "permdisp_p", "permutations",
    "permanova_seed", "permdisp_seed", "matrix_sha256", "qc_sha256",
    "clinical_sha256", "plan_sha256", "script_sha256",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module():
    path = ROOT / "scripts/analyze_prjna1056765_metagenome_400.py"
    spec = importlib.util.spec_from_file_location("frozen400", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def read_qc_membership() -> set[str]:
    if sha256(QC) != QC_SHA256:
        raise SystemExit("QC membership file hash changed")
    with QC.open(encoding="utf-8", newline="") as stream:
        return {row["run"] for row in csv.DictReader(stream, delimiter="\t")
                if row["sensitivity_included"] == "True"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--permutations", type=int, default=9999, choices=[9999])
    args = parser.parse_args()
    plan_sha256 = sha256(PLAN)
    if not PLAN_LOCK.is_file() or PLAN_LOCK.read_text(encoding="utf-8").strip() != plan_sha256:
        raise SystemExit("frozen plan hash gate failed")
    expected_hashes = {"matrix": MATRIX_SHA256, "clinical": CLINICAL_SHA256,
                       "qc": QC_SHA256, "anchor_species": ANCHOR_SPECIES_SHA256}
    observed_hashes = {"matrix": sha256(MATRIX), "clinical": sha256(CLINICAL),
                       "qc": sha256(QC), "anchor_species": sha256(ANCHOR_SPECIES)}
    if observed_hashes != expected_hashes:
        raise SystemExit(f"input hash gate failed: {observed_hashes} != {expected_hashes}")
    module = load_module()
    runs, taxa, raw = module.load_matrix(MATRIX)
    clinical_rows = module.read_tsv(CLINICAL)
    clinical = {row["run"]: row for row in clinical_rows}
    if len(runs) != 400 or set(runs) != set(clinical):
        raise SystemExit("400-run membership gate failed")
    keep = [i for i, taxon in enumerate(taxa)
            if not any(token in taxon.lower() for token in module.BACKGROUND)]
    names = [taxa[i] for i in keep]
    data = module.normalize_rows([[row[i] for i in keep] for row in raw])
    diagnosis = [clinical[run]["diagnosis"] for run in runs]
    strata = [clinical[run]["cohort"] for run in runs]
    qc_ids = read_qc_membership()
    if len(qc_ids) != 119:
        raise SystemExit("strict-QC membership is not the frozen n=119 set")
    qc_counts = Counter(clinical[run]["diagnosis"] for run in qc_ids)
    expected_qc_counts = {"Bacterial infection": 42, "Fungal infection": 19,
                          "Lung cancer": 36, "Pulmonary tuberculosis": 22}
    if dict(qc_counts) != expected_qc_counts or min(qc_counts.values()) < 15:
        raise SystemExit(f"strict-QC diagnosis-count gate failed: {dict(qc_counts)}")
    prevalence = module.prevalence(data)
    rows = []
    cell_index = 0
    # Mandatory first operation: exact integrity replay before any other cell.
    anchor_selected = [j for j, value in enumerate(prevalence) if value >= 40]
    with ANCHOR_SPECIES.open(encoding="utf-8", newline="") as stream:
        frozen_anchor_names = [row["species"] for row in csv.DictReader(stream, delimiter="\t")]
    if [names[j] for j in anchor_selected] != frozen_anchor_names:
        raise SystemExit("exact anchor species membership/order gate failed")
    anchor_filtered = [[row[j] for j in anchor_selected] for row in data]
    anchor_minimum = min(value for row in anchor_filtered for value in row if value > 0)
    anchor_pseudocount = anchor_minimum / 2
    if len(anchor_selected) != 30 or anchor_pseudocount != 1.0097644219603566e-05:
        raise SystemExit("primary anchor feature/pseudocount gate failed")
    anchor_clr = module.clr(anchor_filtered, anchor_pseudocount)
    anchor_distance = module.distance_matrix(anchor_clr, "euclidean")
    _, _, anchor_gower = module.pcoa(anchor_distance)
    anchor_pa = module.permanova(anchor_gower, diagnosis, strata, args.permutations, 1056965)
    anchor_pd = module.permdisp(anchor_distance, diagnosis, strata, args.permutations, 1056966)
    expected = {"F": 2.612771519062346, "R2": 0.019409536625522597,
                "p": 0.0001, "disp_F": 0.8066530620728115,
                "disp_R2": 0.006073890452579873, "disp_p": 0.487}
    observed = {"F": anchor_pa["pseudo_F"], "R2": anchor_pa["R2"],
                "p": anchor_pa["p_value"], "disp_F": anchor_pd["F"],
                "disp_R2": anchor_pd["R2"], "disp_p": anchor_pd["p_value"]}
    if observed != expected:
        raise SystemExit(f"exact anchor replay mismatch: {observed} != {expected}")
    anchor_replay_verified = True
    for threshold, count in ((0.05, 20), (0.10, 40), (0.20, 80)):
        selected = [j for j, value in enumerate(prevalence) if value >= count]
        selected_names = [names[j] for j in selected]
        filtered = [[row[j] for j in selected] for row in data]
        minimum = min(value for row in filtered for value in row if value > 0)
        metric_specs = (("Aitchison", "P1_half_minimum", minimum / 2),
                        ("Aitchison", "P2_tenth_minimum", minimum / 10),
                        ("Bray-Curtis", "not_applicable", None))
        for metric, rule, pseudocount in metric_specs:
            transformed = module.clr(filtered, pseudocount) if metric == "Aitchison" else filtered
            distance = module.distance_matrix(transformed, "euclidean" if metric == "Aitchison" else "bray")
            for population in ("full", "strict_QC"):
                ids = list(range(400)) if population == "full" else [i for i, run in enumerate(runs) if run in qc_ids]
                subdist = [[distance[i][j] for j in ids] for i in ids]
                _, _, gower = module.pcoa(subdist, 2)
                labels = [diagnosis[i] for i in ids]
                blocks = [strata[i] for i in ids]
                primary = population == "full" and threshold == 0.10 and metric == "Aitchison" and rule == "P1_half_minimum"
                permanova_seed = 1056965 if primary else 2100000 + cell_index * 10
                permdisp_seed = 1056966 if primary else permanova_seed + 1
                if primary:
                    pa, pd = anchor_pa, anchor_pd
                else:
                    pa = module.permanova(gower, labels, blocks, args.permutations, permanova_seed)
                    pd = module.permdisp(subdist, labels, blocks, args.permutations, permdisp_seed)
                rows.append([population, threshold, count, metric, rule,
                             "" if pseudocount is None else pseudocount, primary, len(ids), len(selected),
                             pa["pseudo_F"], pa["R2"], pa["p_value"], pd["F"], pd["R2"],
                             pd["p_value"], args.permutations, permanova_seed, permdisp_seed,
                             sha256(MATRIX), QC_SHA256, sha256(CLINICAL), plan_sha256,
                             sha256(Path(__file__))])
                cell_index += 1
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "frozen_sensitivity_grid.tsv"
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    manifest = {"output": str(output.relative_to(ROOT)), "output_sha256": sha256(output),
                "rows": len(rows), "plan_sha256": plan_sha256,
                "script_sha256": sha256(Path(__file__)), "schema": HEADER,
                "anchor_replay_verified_exactly": anchor_replay_verified,
                "anchor_expected": expected, "anchor_observed": observed,
                "input_hashes_expected": expected_hashes,
                "input_hashes_observed": observed_hashes,
                "input_hashes_verified_exactly": True}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
