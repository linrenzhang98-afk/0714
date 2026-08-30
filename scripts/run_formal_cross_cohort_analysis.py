#!/usr/bin/env python3
"""Production entry point for one frozen cohort at a time.

This command does not discover inputs and never pools cohorts. It is prepared
for later ETYY use but must not be run against biological matrices until the
runtime gate and analysis authorization are complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shotgun_analysis.czm import exact_czm
from shotgun_analysis.io import load_common_layer_direct_species_counts, load_tsv, validate_cohort_manifest, validate_sample_alignment
from shotgun_analysis.pipeline import analyze_cohort, pseudocount_backend
from shotgun_analysis.results import write_compact_tsv, write_json


COHORTS = {
    "anchor": {
        "project": "PRJNA1056765",
        "groups": {"Bacterial infection": 114, "Fungal infection": 78, "Lung cancer": 122, "Pulmonary tuberculosis": 86},
        "stratum": "published_split",
        "manifest_columns": {"sample": "run", "run": "run", "group": "diagnosis", "stratum": "cohort"},
        "seeds": (105676510, 105676511),
        "secondary_contrasts": [
            ("Lung cancer", "Bacterial infection"),
            ("Lung cancer", "Fungal infection"),
            ("Lung cancer", "Pulmonary tuberculosis"),
        ],
    },
    "external": {
        "project": "PRJCA046985",
        "groups": {"Drug_Resistance": 49, "Drug_Sensitive": 81},
        "stratum": None,
        "manifest_columns": {"sample": "run_accession", "run": "run_accession", "group": "group_raw", "stratum": None},
        "seeds": (46985010, 46985011),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=sorted(COHORTS), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--sample-qc", type=Path, required=True)
    parser.add_argument("--r-library", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prevalence", type=float, choices=(0.05, 0.10, 0.20), default=0.10)
    parser.add_argument("--zero-method", choices=("czm", "pseudocount_0.5"), default="czm")
    parser.add_argument("--permutations", type=int, default=9999)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = COHORTS[args.cohort]
    manifest = load_tsv(args.manifest)
    columns = contract["manifest_columns"]
    required = [columns["stratum"]] if columns["stratum"] else []
    validate_cohort_manifest(
        manifest, contract["groups"], sample_column=columns["sample"], run_column=columns["run"],
        group_column=columns["group"], required_columns=required,
    )
    manifest_ids = [row[columns["sample"]] for row in manifest]
    count_table = load_common_layer_direct_species_counts(args.counts, sorted(manifest_ids))
    validate_sample_alignment(manifest_ids, count_table.sample_ids)
    qc_rows = load_tsv(args.sample_qc)
    qc_lookup = {row["run"]: row for row in qc_rows}
    validate_sample_alignment(manifest_ids, list(qc_lookup))
    manifest_by_id = {row[columns["sample"]]: row for row in manifest}
    manifest = [manifest_by_id[sample_id] for sample_id in count_table.sample_ids]
    manifest_ids = count_table.sample_ids
    matrix = count_table.matrix
    groups = [row[columns["group"]] for row in manifest]
    strata = [row[columns["stratum"]] for row in manifest] if columns["stratum"] else None
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    if args.zero_method == "czm":
        if args.r_library is None:
            raise SystemExit("--r-library is required for exact CZM")
        replacement = lambda x: exact_czm(x, r_library=args.r_library)
        zero_label = "zCompositions::cmultRepl(method=CZM), version 1.6.2"
        seed_offset = 0 if args.prevalence == 0.10 else int(args.prevalence * 10000)
    else:
        replacement = pseudocount_backend(0.5)
        zero_label = "fixed direct-read pseudocount 0.5 sensitivity"
        seed_offset = 100000 + int(args.prevalence * 10000)
    result = analyze_cohort(
        cohort_id=contract["project"], sample_ids=manifest_ids, groups=groups, counts=matrix,
        feature_names=count_table.feature_names,
        total_reads=[float(qc_lookup[sample_id]["total_input_reads"]) for sample_id in manifest_ids],
        classified_reads=[float(qc_lookup[sample_id]["classified_reads"]) for sample_id in manifest_ids],
        prevalence=args.prevalence, zero_method=zero_label,
        zero_replacement=replacement,
        permanova_seed=contract["seeds"][0] + seed_offset, permdisp_seed=contract["seeds"][1] + seed_offset,
        permutations=args.permutations, strata=strata,
        secondary_contrasts=contract.get("secondary_contrasts", []),
        provenance={
            "python": platform.python_version(), "manifest_sha256": sha256(args.manifest),
            "counts_sha256": sha256(args.counts), "sample_qc_sha256": sha256(args.sample_qc),
            "czm_adapter_sha256": sha256(Path(__file__).resolve().parents[1] / "shotgun_analysis/run_czm.R"),
        },
    )
    if result["analysis_status"] != "BIOLOGICAL":
        raise RuntimeError("production entry point received synthetic IDs")
    args.output.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "reports_public/formal_cross_cohort_analysis/result_schema.json"
    write_json(args.output / "result.json", result, schema)
    fields = ["sample_id", "group", "richness", "shannon", "gini_simpson", "dominance", "classified_fraction"]
    write_compact_tsv(args.output / "sample_metrics.tsv", result["sample_metrics"], fields)
    beta_rows = []
    for test_name in ("permanova", "permdisp"):
        test = result["beta_diversity"][test_name]
        beta_rows.append({"cohort": result["cohort"], "test": test_name.upper(), **{key: test[key] for key in ("statistic", "effect_size", "p_value", "permutations", "seed", "df_between", "df_within")}})
    write_compact_tsv(args.output / "beta_statistics.tsv", beta_rows, ["cohort", "test", "statistic", "effect_size", "p_value", "permutations", "seed", "df_between", "df_within"])
    write_compact_tsv(args.output / "feature_filter.tsv", [{"cohort": result["cohort"], **{key: result["feature_filter"][key] for key in ("threshold", "input_features", "retained_features")}}], ["cohort", "threshold", "input_features", "retained_features"])
    secondary_rows = [{"cohort": result["cohort"], "endpoint": endpoint, **values} for endpoint, values in result["secondary_endpoints"].items()]
    secondary_fields = sorted({key for row in secondary_rows for key in row}, key=lambda key: (key not in {"cohort", "endpoint", "test"}, key))
    for row in secondary_rows:
        for field in secondary_fields:
            row.setdefault(field, "")
    write_compact_tsv(args.output / "secondary_statistics.tsv", secondary_rows, secondary_fields)
    if result["secondary_contrasts"]:
        contrast_fields = sorted({key for row in result["secondary_contrasts"] for key in row}, key=lambda key: (key not in {"endpoint", "contrast", "test"}, key))
        write_compact_tsv(args.output / "secondary_contrasts.tsv", result["secondary_contrasts"], contrast_fields)
    (args.output / "execution_parameters.json").write_text(json.dumps(vars(args), default=str, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
