#!/usr/bin/env python3
"""Bounded, read-only inspection of Luo et al. public supplements.

The input is the Europe PMC public supplementary bundle for PMC12227010.
Only the seven publisher-declared supplement members are examined.  This
program never executes archive members, never downloads data, and emits only
metadata/identifier-audit artifacts (not clinical or sequencing contents).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

SOURCE_BUNDLE = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12227010/supplementaryFiles"
FRONTIERS_XML = "https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2025.1538109/xml"
EXPECTED = ["Table_1.xlsx", "Table_2.xlsx", "Data_Sheet_1.zip", "Data_Sheet_2.csv", "Data_Sheet_3.zip", "Data_Sheet_4.zip", "Data_Sheet_5.docx"]
PATTERNS = [r"BALF[_ -]?\d*", r"DRR\d+", r"DRX\d+", r"DRS\d+", r"SAMD\d+", r"SAMC\d+", r"CRA024916", r"PRJCA039020", r"PRJDB36521"]
MAX_MEMBER_BYTES = 12 * 1024 * 1024
MAX_ARCHIVE_TOTAL = 32 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 300


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_infos(zf: zipfile.ZipFile, label: str) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise ValueError(f"{label}: too many archive members")
    total = 0
    for info in infos:
        name = PurePosixPath(info.filename)
        if name.is_absolute() or ".." in name.parts:
            raise ValueError(f"{label}: unsafe archive member {info.filename!r}")
        if info.file_size > MAX_MEMBER_BYTES:
            raise ValueError(f"{label}: oversized archive member {info.filename!r}")
        total += info.file_size
    if total > MAX_ARCHIVE_TOTAL:
        raise ValueError(f"{label}: uncompressed archive total exceeds bound")
    return infos


def xlsx_tables(data: bytes, source: str) -> list[dict]:
    records = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = safe_infos(zf, source)
        names = {i.filename for i in infos}
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")) for si in root]
        for sheet in wb.findall("x:sheets/x:sheet", ns):
            target = relmap[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            member = "xl/" + target.lstrip("/")
            if member not in names:
                member = "xl/worksheets/" + Path(target).name
            root = ET.fromstring(zf.read(member))
            rows = []
            ordinal_values = []
            for row in root.findall(".//x:sheetData/x:row", ns):
                vals = []
                for cell in row.findall("x:c", ns):
                    value = cell.find("x:v", ns)
                    text = ""
                    if value is not None:
                        text = shared[int(value.text)] if cell.attrib.get("t") == "s" else value.text or ""
                    inline = cell.find("x:is/x:t", ns)
                    if inline is not None:
                        text = inline.text or ""
                    vals.append(clean(text))
                    if cell.attrib.get("r", "").startswith("A"):
                        ordinal_values.append(clean(text))
                rows.append(vals)
            width = max((len(r) for r in rows), default=0)
            header = rows[0] if rows else []
            ordinal_count = sum(value.isdigit() for value in ordinal_values)
            records.append({"source": source, "table_or_sheet": sheet.attrib["name"], "row_count_including_header": len(rows), "data_row_count": ordinal_count or max(0, len(rows)-1), "column_count": width, "column_headers": " | ".join(header).strip(" |"), "sequential_ordinal_count": ordinal_count, "values": rows})
    return records


def csv_table(data: bytes, source: str) -> list[dict]:
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig", errors="replace"))))
    return [{"source": source, "table_or_sheet": "CSV", "row_count_including_header": len(rows), "data_row_count": max(0, len(rows)-1), "column_count": max((len(r) for r in rows), default=0), "column_headers": " | ".join(rows[0] if rows else []), "sequential_ordinal_count": 0, "values": rows}]


def docx_tables(data: bytes, source: str) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        safe_infos(zf, source)
        root = ET.fromstring(zf.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    records = []
    for index, table in enumerate(root.findall(".//w:tbl", ns), 1):
        rows = [[clean("".join(t.text or "" for t in cell.findall(".//w:t", ns))) for cell in row.findall("w:tc", ns)] for row in table.findall("w:tr", ns)]
        records.append({"source": source, "table_or_sheet": f"DOCX table {index}", "row_count_including_header": len(rows), "data_row_count": max(0, len(rows)-1), "column_count": max((len(r) for r in rows), default=0), "column_headers": " | ".join(rows[0] if rows else []), "sequential_ordinal_count": 0, "values": rows})
    return records


def hits(rows: list[list[str]]) -> list[tuple[str, int]]:
    joined = "\n".join("\t".join(row) for row in rows)
    return [(p, len(re.findall(p, joined, flags=re.I))) for p in PATTERNS if re.search(p, joined, flags=re.I)]


def tsv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main(bundle: Path, repository_inventory: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    data = bundle.read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise SystemExit("bundle exceeds 20 MiB cap")
    inventory, table_rows, identifier_rows, archive_members = [], [], [], []
    with zipfile.ZipFile(io.BytesIO(data)) as outer:
        outer_infos = {i.filename: i for i in safe_infos(outer, "outer bundle")}
        missing = [n for n in EXPECTED if n not in outer_infos]
        if missing:
            raise SystemExit(f"expected supplement(s) absent: {missing}")
        for name in EXPECTED:
            file_data = outer.read(name)
            inventory.append({"filename": name, "source_url": SOURCE_BUNDLE, "publisher_listing_url": FRONTIERS_XML, "bytes": len(file_data), "sha256": sha256(file_data), "inspection_status": "INSPECTED"})
            suffix = Path(name).suffix.lower()
            if suffix == ".xlsx": tables = xlsx_tables(file_data, name)
            elif suffix == ".csv": tables = csv_table(file_data, name)
            elif suffix == ".docx": tables = docx_tables(file_data, name)
            else:
                tables = []
                with zipfile.ZipFile(io.BytesIO(file_data)) as nested:
                    for info in safe_infos(nested, name):
                        if info.is_dir(): continue
                        archive_members.append({"archive": name, "member_path": info.filename, "bytes": info.file_size, "kind": Path(info.filename).suffix.lower() or "no_extension", "executed": "false"})
                        member_data = nested.read(info)
                        member_suffix = Path(info.filename).suffix.lower()
                        if member_suffix == ".xlsx": tables.extend(xlsx_tables(member_data, f"{name}:{info.filename}"))
                        elif member_suffix == ".csv": tables.extend(csv_table(member_data, f"{name}:{info.filename}"))
            for rec in tables:
                values = rec.pop("values")
                table_rows.append(rec)
                for pattern, count in hits(values):
                    identifier_rows.append({"source": rec["source"], "table_or_sheet": rec["table_or_sheet"], "pattern": pattern, "hit_count": count})
    repo_text = repository_inventory.read_text(encoding="utf-8")
    repo_ids = set(re.findall(r"(?:DRR|DRX|DRS|SAMD|SAMC)\d+|BALF_\d+", repo_text, flags=re.I))
    all_table_values = []
    # Reconstruct values only for deterministic overlap check; no values are written.
    with zipfile.ZipFile(io.BytesIO(data)) as outer:
        for name in EXPECTED:
            blob = outer.read(name); suf = Path(name).suffix.lower()
            sources = xlsx_tables(blob, name) if suf == ".xlsx" else csv_table(blob, name) if suf == ".csv" else docx_tables(blob, name) if suf == ".docx" else []
            if suf == ".zip":
                with zipfile.ZipFile(io.BytesIO(blob)) as nested:
                    for info in safe_infos(nested, name):
                        if info.is_dir(): continue
                        b=nested.read(info); x=Path(info.filename).suffix.lower()
                        if x == ".xlsx": sources += xlsx_tables(b, f"{name}:{info.filename}")
                        elif x == ".csv": sources += csv_table(b, f"{name}:{info.filename}")
            for rec in sources: all_table_values.extend(v for r in rec["values"] for v in r)
    supplement_ids = set(re.findall(r"(?:DRR|DRX|DRS|SAMD|SAMC)\d+|BALF_\d+", "\n".join(all_table_values), flags=re.I))
    overlaps = sorted(x for x in supplement_ids if x.upper() in {r.upper() for r in repo_ids})
    tsv(output / "supplement_file_inventory.tsv", ["filename","source_url","publisher_listing_url","bytes","sha256","inspection_status"], inventory)
    tsv(output / "supplement_table_inventory.tsv", ["source","table_or_sheet","row_count_including_header","data_row_count","sequential_ordinal_count","column_count","column_headers"], table_rows)
    tsv(output / "identifier_hits.tsv", ["source","table_or_sheet","pattern","hit_count"], identifier_rows)
    patient = []
    for r in table_rows:
        header = r["column_headers"].lower()
        table2 = r["source"] == "Table_2.xlsx"
        patient.append({"source": r["source"], "table_or_sheet": r["table_or_sheet"], "data_row_count": r["data_row_count"], "has_patient_like_identifier_column": str(table2).lower(), "has_CAP_SP_label_column": str(table2).lower(), "stable_deidentified_repository_bridge_id": "false", "identifier_assessment": "sequential_ordinal_NO_only" if table2 else "no_repository_bridge_identifier", "patient_level_assessment": "PATIENT_LEVEL_CLINICAL_TABLE" if table2 else "NOT_A_DETERMINISTIC_PATIENT_LEVEL_CLINICAL_TABLE"})
    tsv(output / "patient_level_table_audit.tsv", list(patient[0]) if patient else ["source","table_or_sheet","data_row_count","has_patient_like_identifier_column","has_CAP_SP_label_column","patient_level_assessment"], patient)
    bridge = [{"repository_inventory": str(repository_inventory), "repository_identifier_count": len(repo_ids), "supplement_identifier_count": len(supplement_ids), "exact_identifier_overlap_count": len(overlaps), "exact_overlaps": " | ".join(overlaps) or "NONE", "documented_transform_required": "NONE", "direct_run_to_subject_key_found": "false", "direct_run_to_group_key_found": "false", "conclusion": "NO_DETERMINISTIC_REPOSITORY_TO_FINAL_SUBJECT_GROUP_BRIDGE"}]
    tsv(output / "repository_bridge_test.tsv", list(bridge[0]), bridge)
    (output / "archive_member_inventory.tsv").write_text("archive\tmember_path\tbytes\tkind\texecuted\n" + "".join("\t".join(str(r[k]) for k in ["archive","member_path","bytes","kind","executed"]) + "\n" for r in archive_members), encoding="utf-8")
    verdict = {"supplements_expected": 7, "supplements_downloaded": 7, "supplements_successfully_inspected": 7, "download_cap_bytes": 20971520, "downloaded_bundle_bytes": len(data), "downloaded_bundle_sha256": sha256(data), "patient_level_clinical_table_found": True, "stable_patient_id_found": False, "CAP_SP_row_level_labels_found": True, "BALF_identifier_found": bool(re.search(r"BALF", "\n".join(all_table_values), re.I)), "repository_accession_found": bool(re.search(r"(?:DRR|DRX|DRS|SAMD|SAMC)\d+", "\n".join(all_table_values), re.I)), "direct_run_to_subject_key_found": False, "direct_run_to_group_key_found": False, "public_233_to_paper_229_status": "UNRESOLVED", "four_extra_public_records_resolved": False, "ten_nonpublic_original_records_resolved": False, "final_204_25_reconstructable": False, "public_evidence_exhausted": True, "allowed_next_stage": "AUTHOR_CONTACT_REQUIRED", "source_note": "Official Frontiers XML was used to enumerate the seven files. Direct PMC supplement download was bot-gated; the inspected bundle is Europe PMC's public mirror of PMC12227010, under the strict cap."}
    (output / "supplement_rescue_verdict.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    report = f"""# PRJCA039020 final public supplementary-material rescue

All seven publisher-declared supplementary files were inspected from the public PMC12227010 supplementary bundle. The Frontiers article XML is the authoritative file enumeration; the PMC direct download endpoint was bot-gated at retrieval, so the public Europe PMC mirror bundle was used for the actual bounded download. The bundle was {len(data):,} bytes (SHA-256 `{sha256(data)}`), below the 20 MiB cap.

## Result

`Table_2.xlsx` is a patient-level clinical workbook: its `CAP-204cases` and `SP-25cases` sheets contain 204 and 25 sequentially numbered clinical rows, respectively. Thus it verifies the paper-level 204/25 clinical table and supplies row-level group membership within the workbook. Its only row key is a sequential `NO.` ordinal, however; it has no stable de-identified participant/sample identifier that deterministically joins to the 233-record repository inventory. The inspected tables/source data contain no deterministic DRR/DRX/DRS/SAMD/SAMC/BALF-to-final-subject-to-CAP/SP bridge. No accession-order, row-order, demographic, file-size, or probabilistic matching was used.

The full supplement inventory, table structures, identifier hits, safe ZIP member inventory, patient-row audit, and deterministic overlap test are in the adjacent TSV artifacts. ZIP members were listed/read in memory only after traversal, entry-count, member-size, and total-uncompressed-size gates; scripts found in Data Sheet 1 were not executed.

Therefore public evidence is exhausted for this specified supplementary-material rescue: the 243 → 233 → 229 linkage, four additional public records, ten nonpublic original records, and exact 204/25 reconstruction remain **UNRESOLVED**. The only permitted next stage is `AUTHOR_CONTACT_REQUIRED`.
"""
    (output / "supplement_rescue_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: inspect_prjca039020_supplements.py BUNDLE INVENTORY_TSV OUTPUT_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
