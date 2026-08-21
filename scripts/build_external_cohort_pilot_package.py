#!/usr/bin/env python3
"""Build the metadata-only external-cohort pilot package.

This script never downloads sequence reads and never computes biological outcomes.
It consumes repository metadata snapshots retrieved during the 2026-08-21 audit.
"""

from __future__ import annotations

import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from statistics import median
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports_public" / "prjna1056765_external_cohort_pilot_package"
MAN = OUT / "manifests"
CONTROLS = OUT / "controls"
PILOT = OUT / "pilot"


def tsv_read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def csv_read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def tsv_write(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def xlsx_rows(path: Path, sheet: str) -> list[list[str]]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        shared: list[str] = []
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for item in root.findall("x:si", ns):
            shared.append("".join(node.text or "" for node in item.iter("{" + ns["x"] + "}t")))
        root = ET.fromstring(archive.read("xl/worksheets/" + sheet))
        result: list[list[str]] = []
        for row in root.findall(".//x:row", ns):
            values: dict[int, str] = {}
            for cell in row.findall("x:c", ns):
                ref = cell.attrib["r"]
                letters = re.match(r"[A-Z]+", ref).group(0)
                column = 0
                for char in letters:
                    column = column * 26 + ord(char) - 64
                node = cell.find("x:v", ns)
                value = "" if node is None else (node.text or "")
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                values[column - 1] = value
            result.append([values.get(i, "") for i in range(max(values, default=-1) + 1)])
        return result


class GSATableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, object]] = []
        self.tr: dict[str, object] | None = None
        self.cell: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.tr = {"class": dict(attrs).get("class", ""), "cells": []}
        elif tag == "td" and self.tr is not None:
            self.cell = ""

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.cell is not None and self.tr is not None:
            self.tr["cells"].append(" ".join(self.cell.split()))
            self.cell = None
        elif tag == "tr" and self.tr is not None:
            self.rows.append(self.tr)
            self.tr = None


def cra034880_dna() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for source in [Path("/tmp/cra034880_all.html"), Path("/tmp/cra034880_all_p2.html")]:
        parser = GSATableParser()
        parser.feed(source.read_text(encoding="utf-8", errors="ignore"))
        experiment: list[str] | None = None
        for row in parser.rows:
            cells = row["cells"]
            if row["class"] == "experiment":
                experiment = cells
            elif row["class"] == "runTr" and experiment and not experiment[1].endswith("R"):
                records.append({
                    "run_accession": cells[0], "subject_id": experiment[1],
                    "experiment_accession": experiment[0], "biosample": experiment[-1],
                    "platform": experiment[-2], "file_name": cells[-1].replace("File: ", ""),
                })
    assert len(records) == 130
    return records


for directory in [OUT, MAN, CONTROLS, PILOT]:
    directory.mkdir(parents=True, exist_ok=True)

# PRJCA039020 / PRJDB36521: accession layer is exact; subject/group layer is not linked.
ena39 = tsv_read(Path("/tmp/PRJDB36521_ena.tsv"))
assert len(ena39) == 233
manifest39: list[dict[str, object]] = []
for row in ena39:
    match = re.search(r"(BALF_\d+) \((SAMC\d+)\)", row["sample_title"])
    alias, samc = match.groups() if match else (row["sample_title"], "")
    manifest39.append({
        "run_accession": row["run_accession"], "experiment_accession": row["experiment_accession"],
        "ena_biosample": row["sample_accession"], "secondary_sample": row["secondary_sample_accession"],
        "ngdc_biosample": samc, "submitted_sample_name": alias, "subject_id": "UNRESOLVED",
        "published_group": "UNRESOLVED", "group_evidence": "No direct run/BioSample-to-clinical-row key in public metadata",
        "specimen": "BALF", "site": "Zengcheng Branch of Nanfang Hospital, Southern Medical University",
        "platform": row["instrument_model"], "layout": row["library_layout"],
        "read_length": str(round(int(row["base_count"]) / int(row["read_count"]))) if int(row["read_count"]) else "",
        "compressed_bytes": row["fastq_bytes"], "md5": row["fastq_md5"], "fastq_ftp": row["fastq_ftp"],
        "host_depletion_provenance": "QUALIFIED_RAW: paper Data Availability calls deposit raw sequence data; wet-lab Benzonase occurred before library and SNAP hg38 was downstream analysis",
        "pilot_biological_eligibility": "NO",
    })
tsv_write(MAN / "PRJCA039020_exact_manifest.tsv", manifest39)
map39 = [{"run_accession": r["run_accession"], "ngdc_biosample": r["ngdc_biosample"],
          "submitted_sample_name": r["submitted_sample_name"], "subject_id": "UNRESOLVED",
          "group_raw": "UNRESOLVED", "mapping_status": "GROUP_MAPPING_UNRESOLVED",
          "biological_grouping_eligible": "NO"} for r in manifest39]
tsv_write(MAN / "PRJCA039020_subject_group_map.tsv", map39)
tsv_write(MAN / "PRJCA039020_exclusions.tsv", [{
    "scope": "all_233_public_runs", "count": 233,
    "reason": "No directly traceable run/BioSample -> subject -> CAP/severe-pneumonia mapping",
    "status": "EXCLUDE_FROM_BIOLOGICAL_GROUPING",
    "four_extra_public_biosamples": "UNIDENTIFIABLE_FROM_PUBLIC_EVIDENCE",
    "note": "Paper analyzed 229 after clinical-data exclusion; repository ordering was not used to guess the four records.",
}])

# PRJCA046985 / CRA034880: the run alias is the patient ID and Table S3 independently supplies group.
dna46 = cra034880_dna()
sheet3 = xlsx_rows(Path("/tmp/pmc12894345_supp/DataSheet2.xlsx"), "sheet3.xml")
headers46 = sheet3[1]
clinical46 = {r[0]: dict(zip(headers46, r)) for r in sheet3[2:] if r and r[0].startswith("M")}
assert len(clinical46) == 130
manifest46: list[dict[str, object]] = []
for row in dna46:
    c = clinical46[row["subject_id"]]
    head = Path("/tmp/cra034880_heads") / f'{row["run_accession"]}.txt'
    text = head.read_text(encoding="utf-8", errors="ignore")
    lengths = re.findall(r"(?im)^content-length:\s*(\d+)", text)
    etags = re.findall(r"(?im)^etag:\s*(.+)$", text)
    raw_reads, raw_bases = int(float(c["total_reads"])), int(float(c["total_bases"]))
    public_reads = int(float(c["unhost_reads"]))
    manifest46.append({
        **row, "group_raw": c["group"], "group_evidence": "Supplementary Table S3 patient ID equals GSA run alias",
        "specimen": "BALF", "site": "Xuzhou Hospital affiliated to Beijing Ditan Hospital, Capital Medical University",
        "layout": "SINGLE_FILE; pairing not declared in GSA", "approx_raw_read_length": round(raw_bases / raw_reads, 3),
        "public_unhost_reads": public_reads, "compressed_bytes": int(lengths[-1]),
        "checksum": "NOT_PUBLISHED", "file_identifier": row["file_name"], "http_etag": etags[-1].strip() if etags else "",
        "host_depletion_provenance": "Table S3 labels patient-level output unhost_reads; public file shares patient/run alias",
        "batch": "DNBSEQ-G99; further library-batch field not public",
    })
tsv_write(MAN / "PRJCA046985_exact_manifest.tsv", manifest46)
tsv_write(MAN / "PRJCA046985_subject_group_map.tsv", [{
    "run_accession": r["run_accession"], "biosample": r["biosample"], "subject_id": r["subject_id"],
    "group_raw": r["group_raw"], "group_harmonized": "DR-TB" if r["group_raw"] == "Drug_Resistance" else "DS-TB",
    "clinical_label_basis": "phenotypic or molecular drug-susceptibility testing reported in paper",
    "mapping_status": "DIRECT",
} for r in manifest46])
tsv_write(MAN / "PRJCA046985_exclusions.tsv", [{
    "run_accession": "NONE", "reason": "All 130 DNA aliases map directly to Table S3; 130 RNA runs with R suffix are excluded by modality",
    "excluded_count": 130, "excluded_modality": "metatranscriptomic RNA",
}])

# PRJNA977832 remains metadata-only: complete accession layer, no public clinical bridge.
ena97 = {r["run_accession"]: r for r in tsv_read(Path("/tmp/PRJNA977832_ena.tsv"))}
run97 = csv_read(Path("/tmp/PRJNA977832_runinfo_fresh.csv"))
assert len(ena97) == len(run97) == 718
manifest97: list[dict[str, object]] = []
for row in run97:
    ena = ena97[row["Run"]]
    manifest97.append({
        "run_accession": row["Run"], "experiment_accession": row["Experiment"], "biosample": row["BioSample"],
        "subject_id": "UNRESOLVED", "sample_name": row["SampleName"], "library_name": row["LibraryName"],
        "hiv_group": "UNRESOLVED", "group_evidence": "No HIV field or accession-linked clinical table in public record",
        "platform": row["Model"], "layout": row["LibraryLayout"], "read_length": row["avgLength"],
        "compressed_bytes": ena["fastq_bytes"], "md5": ena["fastq_md5"], "fastq_ftp": ena["fastq_ftp"],
        "center_repository": row["CenterName"], "host_depletion_status": "UNRESOLVED_AT_FILE_LEVEL",
        "repository_filename_signal": "unhost" if "unhost" in row["SampleName"].lower() else ("nonhuman_nonspike" if "nonhuman.nonspike" in row["SampleName"].lower() else "none"),
        "analysis_eligibility": "METADATA_ONLY",
    })
tsv_write(MAN / "PRJNA977832_exact_manifest.tsv", manifest97)
tsv_write(MAN / "PRJNA977832_subject_group_map.tsv", [{
    "run_accession": r["run_accession"], "biosample": r["biosample"], "subject_id": "UNRESOLVED",
    "hiv_group": "UNRESOLVED", "repeat_status": "No repeated BioSample among 718 runs; patient identity not recoverable",
    "mapping_status": "BLOCKED", "analysis_eligible": "NO",
} for r in manifest97])
write(MAN / "PRJNA977832_discrepancy_report.md", f"""
# PRJNA977832 discrepancy report

The paper reports 781 screened patients and 756 eligible patients: 476 HIV-positive and 280 HIV-negative. The public BioProject currently exposes 718 runs, 718 experiments and 718 unique BioSamples. Therefore 38 paper participants have no identifiable one-to-one public run under this BioProject. No duplicate BioSample occurs among the 718 runs, but subject identifiers are absent, so distinct BioSamples cannot be proven to represent distinct patients.

The public records contain no HIV field and the article supplement is an aggregate patient-characteristics table, not an accession key. Consequently, run-to-HIV-group mapping is **unresolved** and no 718-run subset can be assigned by filename, library number or ordering.

Repository metadata names the submitting centre as Zhongnan Hospital, Wuhan University. The paper describes retrospective BALF collection at the First Hospital of Changsha and lists both institutions among author affiliations. This is a provenance discrepancy, not evidence of a multicentre cohort.

The runs are single-end NovaSeq records: 648 have mean length 50 nt and 70 have mean length 40 nt. The 70 filenames include `unhost`; many 50-nt filenames include `nonhuman.nonspike`. These filename signals are not accepted as proof of deposited-file processing. File-level host-depletion provenance remains unresolved pending an explicit repository or submitter statement.

Exact ENA compressed total: {sum(int(r['compressed_bytes']) for r in manifest97):,} bytes ({sum(int(r['compressed_bytes']) for r in manifest97)/1e9:.3f} GB decimal). No raw-read retrieval is authorized. Status: **METADATA_ONLY**.
""")

# Control inventories: absence is reported, never imputed.
control_fields = ["control_accession", "control_type", "matched_batch", "extraction_control", "library_control", "blank_type", "read_count_if_available", "raw_data_available", "paper_description", "repository_description", "interpretability", "notes"]
for study, note in [
    ("PRJCA039020", "No public run or paper statement could be identified as a negative control."),
    ("PRJCA046985", "The 260 GSA runs map to 130 patient DNA and 130 patient RNA records; no public negative-control run was identified."),
    ("PRJNA977832", "No run is labelled as a negative control in RunInfo/ENA; the paper does not provide an accession-linked control inventory."),
]:
    tsv_write(CONTROLS / f"{study}_control_inventory.tsv", [{
        "control_accession": "NONE_IDENTIFIED", "control_type": "UNRESOLVED", "matched_batch": "UNRESOLVED",
        "extraction_control": "UNRESOLVED", "library_control": "UNRESOLVED", "blank_type": "UNRESOLVED",
        "read_count_if_available": "NA", "raw_data_available": "NO_CONTROL_IDENTIFIED",
        "paper_description": note, "repository_description": "No explicitly labelled control record",
        "interpretability": "LIMITATION", "notes": "No threshold will be borrowed from another cohort.",
    }], control_fields)

technical = [
    {"study": "PRJCA039020/PRJDB36521", "site": "Zengcheng Branch, Nanfang Hospital", "platform": "Illumina NextSeq 550", "library_layout": "single-end", "read_length": "40 nt", "host_depletion_status": "QUALIFIED_RAW: wet-lab depleted, computationally unfiltered deposit per paper ordering", "host_depletion_tool": "Tween/Benzonase before extraction; SNAP hg38 in paper", "host_reference": "hg38 (paper)", "technical_batch": "not public", "negative_controls": "none identified", "raw_or_host_depleted": "RAW with pre-library Benzonase", "taxonomy_compatibility": "Kraken2 conditional; Bracken compatibility unverified—execution stop"},
    {"study": "PRJCA046985/CRA034880", "site": "Xuzhou Hospital affiliated to Beijing Ditan Hospital", "platform": "DNBSEQ-G99", "library_layout": "single public FASTQ per DNA subject; pairing undeclared", "read_length": "~50/75 nt before host removal", "host_depletion_status": "public file linked to supplementary unhost_reads", "host_depletion_tool": "paper/supplement output terminology; exact tool pending", "host_reference": "UNRESOLVED", "technical_batch": "not public", "negative_controls": "none identified", "raw_or_host_depleted": "HOST-DEPLETED LIKELY; explicit file statement still desirable", "taxonomy_compatibility": "Kraken2 conditional; Bracken read-length adaptation likely required"},
    {"study": "PRJNA977832/SRP440548", "site": "paper: First Hospital of Changsha; repository submitter: Zhongnan Hospital", "platform": "Illumina NovaSeq 6000", "library_layout": "single-end", "read_length": "648 x 50 nt; 70 x 40 nt", "host_depletion_status": "UNRESOLVED at deposited-file level", "host_depletion_tool": "filename signals only, not accepted", "host_reference": "UNRESOLVED", "technical_batch": "library L1-L718; two read-length strata", "negative_controls": "none identified", "raw_or_host_depleted": "UNRESOLVED", "taxonomy_compatibility": "metadata-only; Bracken STOP at 40/50 nt unless matching redistributions exist"},
]
tsv_write(OUT / "technical_provenance_matrix.tsv", technical)

# A technical-only pilot may be frozen, but is not executable until every STOP clears.
sizes39 = sorted(int(r["compressed_bytes"]) for r in manifest39)
target = median(sizes39)
selected = min(manifest39, key=lambda r: abs(int(r["compressed_bytes"]) - target))
pilot_rows = [{
    "run_accession": selected["run_accession"], "subject_id": "UNRESOLVED", "group": "UNRESOLVED",
    "sample_role": "technical_compatibility_only", "layout": selected["layout"], "read_length": selected["read_length"],
    "compressed_bytes": selected["compressed_bytes"], "checksum_md5": selected["md5"],
    "reason_selected": "Run closest to cohort median compressed size; selection did not use microbial composition or inferred clinical group",
}]
tsv_write(PILOT / "PRJCA039020_pilot_manifest.tsv", pilot_rows)
pilot_bytes = sum(int(r["compressed_bytes"]) for r in pilot_rows)
caps = {
    "status": "FROZEN_NOT_AUTHORIZED", "scope": "technical compatibility only", "allowlisted_runs": [r["run_accession"] for r in pilot_rows],
    "max_runs": 1, "manifest_download_bytes": pilot_bytes, "max_bytes_per_run": min(20_000_000_000, max(int(r["compressed_bytes"]) for r in pilot_rows)),
    "max_total_download_bytes": min(40_000_000_000, pilot_bytes), "threads": 8, "max_threads": 16,
    "max_ram_gib": 128, "max_wall_hours": 24, "minimum_free_disk_bytes": max(5_000_000_000, pilot_bytes * 6),
    "resumable": True, "checksum_required": True, "substitution_allowed": False,
}
(PILOT / "PRJCA039020_resource_caps.json").write_text(json.dumps(caps, indent=2) + "\n", encoding="utf-8")

write(OUT / "hospital_pilot_compatibility_report.md", f"""
# Hospital pilot compatibility report

**Package-level verdict: DO_NOT_RUN.** The cohort-specific rows below are compatibility assessments, not execution authorization.

## Read-only evidence inventory

The established project pathway records Kraken2 and Bracken at `/home/suma/anaconda3/envs/mgshotgun/bin/` and the classifier database at `/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209`. Thirty completed anchor jobs explicitly used `database100mers.kmer_distrib`. This repository snapshot does not provide live executable versions, a database content hash, an exhaustive redistribution-file listing, current free disk, or current CPU/RAM availability. No hospital file or service was modified.

The required rule is conservative: absence of verified evidence for a matching Bracken redistribution is a STOP, not a reason to build one.

| Cohort | Verdict | Reason |
|---|---|---|
| PRJCA039020 | **STOP / adaptation required** | Kraken2 input is technically plausible, but 40-nt Bracken compatibility is unverified. The deposit is qualified RAW; clinical grouping remains unresolved. |
| PRJCA046985 | **CONDITIONAL** | Direct DR/DS mapping is complete and files are small. Public files correspond to `unhost_reads`, but layout, exact host-depletion implementation and compatible 50/75-mer Bracken redistribution require live confirmation. |
| PRJNA977832 | **STOP** | Metadata-only by design; HIV mapping and host state are unresolved, and 40/50-nt Bracken compatibility is not evidenced. |

Current pilot working-space floor from the frozen one-run manifest is {caps['minimum_free_disk_bytes']:,} bytes. Compatibility cannot be upgraded on historic command-path evidence alone. A future read-only workstation inventory must record `kraken2 --version`, `bracken -v`, executable hashes, database file inventory/hash/date, `database*mers.kmer_distrib`, `df`, CPU count and memory before raw-read execution. Host-state closure requires documentary provenance, not additional host filtering. A newly generated 40-mer redistribution would require separate validation and authorization and is outside this package.
""")

write(OUT / "external_cohort_analysis_template.md", """
# Frozen external-cohort analysis grammar template

This template fixes the decision grammar before community results are viewed; it does not copy the anchor v5 thresholds.

1. **Eligibility.** Include only BAL/BALF DNA runs with direct accession-to-subject-to-clinical-label evidence. Preserve raw labels. Exclude unresolved labels. Select one prespecified sample per subject using collection time and clinical eligibility, never microbial composition.
2. **Contrast.** Define one independently documented within-cohort primary contrast. PRJCA039020 remains undefined until CAP/severe mapping is direct. CRA034880 may use raw `Drug_Resistance` versus `Drug_Sensitive` labels. PRJNA977832 remains undefined.
3. **Covariates.** Admit only covariates available before sequence inspection and sufficiently complete within the cohort. Record missingness. Do not harmonize merely to enlarge groups.
4. **Permutations.** Use 9,999 permutations; restrict within center, subject or verified technical batch when the design requires and permits it. Stop if diagnosis is not independently estimable.
5. **Features.** Freeze a cohort-specific prevalence rule after inspecting metadata and technical detection summaries but before disease-labelled community outcomes. Report retained count. Do not import anchor 5/10/20% thresholds automatically.
6. **Geometry.** Primary CLR/Aitchison with a prespecified zero-replacement rule; Bray-Curtis is a comparator. Freeze all choices before group-labelled ordination or PERMANOVA.
7. **Inference.** Report PERMANOVA effect size and uncertainty with PERMDISP qualification. Never define success as significance or pool raw matrices across studies.
8. **QC sensitivity.** Separate universal integrity metrics from cohort-specific sensitivity populations. Missing negative controls are a limitation, not permission to reuse another cohort's contamination cutoff.
9. **Clustering.** Run only when sample size and feature support are adequate; report silhouette and cross-representation agreement across a frozen k range. Do not infer absence of all ecotypes from instability under tested representations.
10. **Cross-cohort synthesis.** Compare cohort-level estimates descriptively first. Formal pooling requires later justification of estimand comparability and explicit approval.
""")

write(OUT / "pilot_authorization_brief.md", f"""
# Bounded pilot authorization brief

**Current independent gate verdict: DO_NOT_RUN.** This is a frozen candidate package, not an execution authorization.

1. **First-pilot cohort:** PRJCA039020 / PRJDB36521, technical-only candidate.
2. **Frozen run:** `{selected['run_accession']}`.
3. **Role/group:** technical compatibility only; subject and CAP/severe group unresolved.
4. **Exact download:** {pilot_bytes:,} bytes ({pilot_bytes/1e9:.6f} GB decimal).
5. **Working-space floor:** {caps['minimum_free_disk_bytes']:,} bytes ({caps['minimum_free_disk_bytes']/1e9:.3f} GB decimal), checked again immediately before execution.
6. **Runtime:** bounded at 24 h; expected under 2 h for this sub-GB file if network and classifier are healthy, but no live benchmark is claimed.
7. **Compatibility:** **STOP / adaptation required** because 40-nt Bracken compatibility is unverified; only 100-mer use is evidenced.
8. **Host depletion:** qualified RAW. Paper Data Availability calls the deposit raw sequence data, with Benzonase before library construction and SNAP hg38 in downstream analysis.
9. **Negative controls:** none publicly identified; the frozen technical pilot contains no negative control.
10. **Stop conditions:** checksum mismatch; accession outside allowlist; size above manifest/cap; layout/read-length mismatch; unresolved host state at filtering stage; missing matching Bracken redistribution; insufficient disk/RAM; repeated download/tool failure; any request for biological inference.
11. **Can establish:** download integrity, FASTQ structure, observed read length, existing-host-state compatibility, Kraken2/Bracken executable compatibility if all STOPs clear, runtime/disk use, classified fraction and output layout.
12. **Cannot establish:** CAP/severe differences, diagnosis effect, taxa, biomarkers, PERMANOVA, biological replication, or cohort validity.

This package is not executable. Raw-read authorization must not be requested unless an independent gate review records `APPROVE_BOUNDED_PILOT` after the host-state and 40-mer compatibility blockers close.
""")

write(OUT / "deepseek_manifest_and_pilot_gate.md", """
# Live DeepSeek manifest and pilot gate

**Verdict: DO_NOT_RUN**

Model: `deepseek-v4-pro`
Live audit log: `/home/leonrenzhang/ai-supervisor/logs/session-2026-08-21T04-37-39-959Z-51086.jsonl`
Review completed: 2026-08-21

## Findings

- PRJCA039020 contains 233 exact public runs but no direct accession-to-subject-to-CAP/severe mapping. `DRR770839` is the exact median-size run and is frozen only as a technical candidate.
- The deposited-file host state is unresolved.
- Existing project evidence confirms use of `database100mers.kmer_distrib`; it does not establish a matching 40-nt Bracken redistribution.
- CRA034880 has a direct 130-subject mapping through the GSA alias and Supplementary Table S3: 49 `Drug_Resistance` and 81 `Drug_Sensitive`.
- PRJNA977832 has 718 public runs versus 756 eligible paper participants, lacks an accession-linked HIV map and remains metadata-only.

## Blocking issues

1. Obtain accession-level documentary evidence for the deposited-file host-depletion state of `DRR770839`.
2. Verify an existing 40-nt Bracken redistribution matching the exact Kraken database and installed Bracken version. Do not build one under this phase.
3. Complete a live read-only workstation inventory of executable versions/hashes, database identity, redistribution files, free disk, CPU and RAM.
4. CAP/severe mapping remains blocked for any biological use. It is not required for a strictly technical pilot after the execution blockers close.

No raw reads were downloaded and no hospital, database or environment state was changed.
""")

summary = {
    "prjca039020_runs": len(manifest39), "prjca039020_bytes": sum(int(r["compressed_bytes"]) for r in manifest39),
    "prjca046985_dna_runs": len(manifest46), "prjca046985_bytes": sum(int(r["compressed_bytes"]) for r in manifest46),
    "prjca046985_groups": {g: sum(r["group_raw"] == g for r in manifest46) for g in ["Drug_Resistance", "Drug_Sensitive"]},
    "prjna977832_runs": len(manifest97), "prjna977832_bytes": sum(int(r["compressed_bytes"]) for r in manifest97),
    "pilot_run": selected["run_accession"], "pilot_bytes": pilot_bytes,
}
(OUT / "manifest_closure_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
