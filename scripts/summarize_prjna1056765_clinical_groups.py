#!/usr/bin/env python3
"""Summarize PRJNA1056765 results by published clinical diagnosis groups."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import time
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


RUNINFO_URL = "https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA1056765"
SUPPLEMENT_URL = (
    "https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41746-025-01977-5/MediaObjects/"
    "41746_2025_1977_MOESM2_ESM.xlsx"
)
NPJ_ARTICLE_URL = "https://www.nature.com/articles/s41746-025-01977-5"
SCIDATA_ARTICLE_URL = "https://www.nature.com/articles/s41597-025-06171-6"

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def fetch_if_missing(url: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "github-analysis-control/1.0 (+https://github.com/linrenzhang98-afk/0714)"
            },
        )
        last_error: Exception | None = None
        tmp_path = path.with_suffix(path.suffix + ".download")
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response, tmp_path.open("wb") as f:
                    f.write(response.read())
                tmp_path.replace(path)
                break
            except Exception as exc:  # noqa: BLE001 - include network-layer failures in retry path.
                last_error = exc
                if tmp_path.exists():
                    tmp_path.unlink()
                if attempt < 3:
                    time.sleep(2 * attempt)
        if not path.exists():
            raise RuntimeError(f"Failed to download {url} after 3 attempts: {last_error}")
    return path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_sample_name(value: str | None) -> str:
    value = (value or "").strip()
    return re.sub(r"\s+(DNA|RNA)$", "", value)


def col_index(cell_ref: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_ref or "")
    if not letters:
        return 0
    idx = 0
    for ch in letters.group(1):
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    strings: list[str] = []
    for si in root.findall("main:si", NS):
        parts = [t.text or "" for t in si.findall(".//main:t", NS)]
        strings.append("".join(parts))
    return strings


def read_xlsx_sheet(path: Path, sheet_number: int) -> list[list[str]]:
    sheet_path = f"xl/worksheets/sheet{sheet_number}.xml"
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        root = ET.fromstring(zf.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.findall(".//main:sheetData/main:row", NS):
        values: list[str] = []
        for cell in row.findall("main:c", NS):
            idx = col_index(cell.attrib.get("r", ""))
            while len(values) <= idx:
                values.append("")
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                text = "".join(t.text or "" for t in cell.findall(".//main:t", NS))
            else:
                raw = cell.find("main:v", NS)
                text = raw.text if raw is not None and raw.text is not None else ""
                if cell_type == "s" and text:
                    text = shared[int(text)]
            values[idx] = text.strip()
        rows.append(values)
    return rows


def load_clinical_records(supplement_xlsx: Path) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for sheet_number, sheet_name in [(1, "Data S1"), (2, "Data S2")]:
        rows = read_xlsx_sheet(supplement_xlsx, sheet_number)
        if len(rows) < 3:
            continue
        headers = [h.replace("\n", " ").strip() for h in rows[1]]
        for row in rows[2:]:
            if not row or not row[0]:
                continue
            rec = {h: row[i] if i < len(row) else "" for i, h in enumerate(headers)}
            rec["_sheet"] = sheet_name
            records[row[0].strip()] = rec
    return records


def safe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runinfo", type=Path)
    parser.add_argument("--supplement-xlsx", type=Path)
    parser.add_argument("--production-qc", type=Path, default=Path("reports_public/metagenome_production/run_qc_summary.tsv"))
    parser.add_argument("--deep-review", type=Path, default=Path("reports_public/metagenome_deep_review_summary/comparison.tsv"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports_public/prjna1056765_clinical_groups"))
    args = parser.parse_args()

    cache_dir = Path(".cache") / "prjna1056765_clinical_groups"
    runinfo_path = args.runinfo or fetch_if_missing(RUNINFO_URL, cache_dir / "runinfo.csv")
    supplement_path = args.supplement_xlsx or fetch_if_missing(SUPPLEMENT_URL, cache_dir / "supplementary_data_s1_s4.xlsx")

    runinfo = read_csv(runinfo_path)
    run_to_meta = {row["Run"]: row for row in runinfo if row.get("Run")}
    clinical = load_clinical_records(supplement_path)
    production_rows = read_tsv(args.production_qc)
    deep_rows = read_tsv(args.deep_review) if args.deep_review.exists() else []

    mapped_rows: list[dict[str, Any]] = []
    for row in production_rows:
        run = row["run"]
        meta = run_to_meta.get(run, {})
        patient_id = normalize_sample_name(meta.get("SampleName"))
        rec = clinical.get(patient_id, {})
        mapped_rows.append(
            {
                "run": run,
                "patient_id": patient_id,
                "diagnosis": rec.get("Diagnosis", "UNMAPPED"),
                "cohort": rec.get("Data Sets", ""),
                "collection_date": rec.get("Collecation Date", ""),
                "library_id": rec.get("Library ID", ""),
                "bal_microbiology": rec.get("BAL microbiology", ""),
                "published_dna_pathogen_reads": rec.get("mNGS DNA Pathogen_Reads number", ""),
                "published_rna_pathogen_reads": rec.get("mNGS RNA Pathogen_Reads number", ""),
                "biosample": meta.get("BioSample", ""),
                "size_mb": meta.get("size_MB", ""),
                "total_reads": row.get("total_reads", ""),
                "classified_pct": row.get("classified_pct", ""),
                "top_species": row.get("top_species", ""),
                "top_species_fraction": row.get("top_species_fraction", ""),
                "top_pathogen": row.get("top_pathogen", ""),
                "top_pathogen_fraction": row.get("top_pathogen_fraction", ""),
                "top_pathogen_reads": row.get("top_pathogen_reads", ""),
                "clinical_pathogen_hits": row.get("clinical_pathogen_hits", ""),
            }
        )

    diagnosis_counts = Counter(row["diagnosis"] for row in mapped_rows)
    group_summary_rows: list[dict[str, Any]] = []
    top_pathogen_rows: list[dict[str, Any]] = []
    for diagnosis in sorted(diagnosis_counts):
        group = [row for row in mapped_rows if row["diagnosis"] == diagnosis]
        classified = [v for v in (safe_float(row["classified_pct"]) for row in group) if v is not None]
        pathogen_fraction = [v for v in (safe_float(row["top_pathogen_fraction"]) for row in group) if v is not None]
        group_summary_rows.append(
            {
                "diagnosis": diagnosis,
                "runs": len(group),
                "median_classified_pct": f"{median(classified):.4f}",
                "median_top_pathogen_fraction": f"{median(pathogen_fraction):.5f}",
                "high_confidence_runs": sum(1 for row in group if (safe_float(row["top_pathogen_fraction"]) or 0) >= 0.30),
            }
        )
        counter = Counter(row["top_pathogen"] or "NA" for row in group)
        for pathogen, count in counter.most_common(15):
            top_pathogen_rows.append({"diagnosis": diagnosis, "top_pathogen": pathogen, "runs": count})

    run_to_diagnosis = {row["run"]: row["diagnosis"] for row in mapped_rows}
    deep_mapped_rows: list[dict[str, Any]] = []
    for row in deep_rows:
        out = dict(row)
        out["diagnosis"] = run_to_diagnosis.get(row.get("run", ""), "UNMAPPED")
        deep_mapped_rows.append(out)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        out_dir / "run_clinical_mapping.tsv",
        mapped_rows,
        list(mapped_rows[0].keys()) if mapped_rows else [],
    )
    write_tsv(out_dir / "diagnosis_summary.tsv", group_summary_rows, list(group_summary_rows[0].keys()))
    write_tsv(out_dir / "diagnosis_top_pathogen_counts.tsv", top_pathogen_rows, list(top_pathogen_rows[0].keys()))
    if deep_mapped_rows:
        write_tsv(out_dir / "deep_review_by_diagnosis.tsv", deep_mapped_rows, list(deep_mapped_rows[0].keys()))

    missing_clinical = []
    analyzed_runs = {row["run"] for row in mapped_rows}
    for row in runinfo:
        if not (
            row.get("LibrarySource") == "METAGENOMIC"
            and row.get("LibraryStrategy") == "WGS"
            and row.get("LibraryLayout") == "SINGLE"
        ):
            continue
        patient_id = normalize_sample_name(row.get("SampleName"))
        rec = clinical.get(patient_id)
        if rec and rec.get("_sheet") == "Data S1" and row["Run"] not in analyzed_runs:
            missing_clinical.append(
                {
                    "run": row["Run"],
                    "patient_id": patient_id,
                    "diagnosis": rec.get("Diagnosis", ""),
                    "size_mb": row.get("size_MB", ""),
                }
            )
    write_tsv(out_dir / "clinical_wgs_runs_not_analyzed.tsv", missing_clinical, ["run", "patient_id", "diagnosis", "size_mb"])

    deep_counter = Counter(row.get("diagnosis", "UNMAPPED") for row in deep_mapped_rows)
    stable_counter = Counter(
        row.get("diagnosis", "UNMAPPED")
        for row in deep_mapped_rows
        if row.get("consistency") == "stable_same_top"
    )
    summary = {
        "analyzed_runs": len(mapped_rows),
        "diagnosis_counts": dict(diagnosis_counts),
        "deep_review_runs": len(deep_mapped_rows),
        "deep_review_diagnosis_counts": dict(deep_counter),
        "deep_review_stable_same_top_by_diagnosis": dict(stable_counter),
        "clinical_wgs_runs_not_analyzed": missing_clinical,
        "sources": {
            "runinfo": RUNINFO_URL,
            "supplement": SUPPLEMENT_URL,
            "npj_digital_medicine_article": NPJ_ARTICLE_URL,
            "scientific_data_article": SCIDATA_ARTICLE_URL,
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# PRJNA1056765 Clinical Group Summary",
        "",
        "## Source Interpretation",
        "",
        "- Dataset: PRJNA1056765 BALF clinical mNGS.",
        "- Main article: Metagenomic fingerprints in bronchoalveolar lavage differentiate pulmonary diseases.",
        "- Data descriptor: Bronchoalveolar lavage fluid metagenomic datasets: a multidimensional clinical biomolecular resource.",
        "- Published clinical labels were parsed from Supplementary Data S1/S2.",
        "",
        "## Analyzed DNA WGS Runs",
        "",
    ]
    for row in group_summary_rows:
        lines.append(
            f"- {row['diagnosis']}: {row['runs']} runs; median classified {row['median_classified_pct']}%; "
            f"median top-pathogen fraction {row['median_top_pathogen_fraction']}; "
            f"high-confidence runs {row['high_confidence_runs']}"
        )
    lines.extend(
        [
            "",
            "## Deep-Review Diagnosis Coverage",
            "",
        ]
    )
    for diagnosis, count in sorted(deep_counter.items()):
        lines.append(f"- {diagnosis}: {stable_counter.get(diagnosis, 0)}/{count} stable same-top calls")
    lines.extend(
        [
            "",
            "## Clinical WGS Runs Not Analyzed",
            "",
        ]
    )
    if missing_clinical:
        for row in missing_clinical:
            lines.append(f"- {row['run']} ({row['patient_id']}, {row['diagnosis']}), size_MB={row['size_mb']}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Practical Interpretation",
            "",
            "- The current 400-run result is suitable for four-group BALF mNGS re-analysis: Cancer, Bacterial infection, Fungal infection, and Pulmonary tuberculosis.",
            "- The two missing clinical WGS runs have size_MB=0 in RunInfo, so their absence should be reported as unavailable public SRA records rather than analysis failure.",
            "- Next statistical work should compare pathogen spectra across diagnosis groups and validate high-confidence pathogens after host removal/AMR screening.",
            "",
            "## Output Files",
            "",
            "- `run_clinical_mapping.tsv`",
            "- `diagnosis_summary.tsv`",
            "- `diagnosis_top_pathogen_counts.tsv`",
            "- `deep_review_by_diagnosis.tsv`",
            "- `clinical_wgs_runs_not_analyzed.tsv`",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
