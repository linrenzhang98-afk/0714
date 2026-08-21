#!/usr/bin/env python3
"""Build the metadata-only PRJCA046985 post-pilot read-length audit."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports_public/prjna1056765_external_cohort_pilot_package"
SOURCE = PACKAGE / "manifests/PRJCA046985_exact_manifest.tsv"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    source = read_tsv(SOURCE)
    output = []
    for row in source:
        run = row["run_accession"]
        nominal = str(int(float(row["approx_raw_read_length"])))
        observed = "UNVERIFIED"
        fixed_support = "NO_NOMINAL_AVERAGE_ONLY"
        compatibility = "UNVERIFIED_NO_OBSERVED_FIXED_LENGTH"
        evidence = "GSA file metadata + Supplementary Table S3 nominal/average pre-host-filter read length; no FASTQ observation"
        if run == "CRR2423962":
            observed = "FIXED_50"
            fixed_support = "YES_DIRECT_FASTQ_OBSERVATION"
            compatibility = "VALIDATED_50NT_KRAKEN2_BRACKEN"
            evidence = "bounded hospital pilot c929b8a1: 175080/175080 reads were 50 nt"
        elif run == "CRR2423909":
            observed = "VARIABLE_LENGTH"
            fixed_support = "NO_DIRECTLY_CONTRADICTED"
            compatibility = "INCOMPATIBLE_WITH_SINGLE_75NT_BRACKEN_REDISTRIBUTION"
            evidence = "bounded hospital pilot c929b8a1: 107300 reads, 57 lengths, 15-75 nt; 34865 reads at 75 nt"
        output.append({
            "run_accession": run,
            "subject_id": row["subject_id"],
            "clinical_group": row["group_raw"],
            "deposited_filename": row["file_name"],
            "expected_read_length_metadata": nominal,
            "layout": row["layout"],
            "expected_bytes": row["compressed_bytes"],
            "host_status": "HOST_DEPLETED",
            "processing_description": "Supplementary record labels deposited output as unhost_reads; exact host tool/reference not recovered",
            "fixed_length_supported_by_metadata": fixed_support,
            "observed_read_length_status": observed,
            "Bracken_compatibility_status": compatibility,
            "evidence_source": evidence,
        })
    fields = [
        "run_accession", "subject_id", "clinical_group", "deposited_filename",
        "expected_read_length_metadata", "layout", "expected_bytes", "host_status",
        "processing_description", "fixed_length_supported_by_metadata",
        "observed_read_length_status", "Bracken_compatibility_status", "evidence_source",
    ]
    write_tsv(PACKAGE / "prjca046985_read_length_audit.tsv", fields, output)
    write_tsv(
        PACKAGE / "replacement_pilot_candidate.tsv",
        ["candidate_status", "run_accession", "subject_id", "clinical_group", "expected_bytes", "expected_fixed_read_length", "matching_redistribution", "reason"],
        [{
            "candidate_status": "NO_DEFENSIBLE_FIXED_LENGTH_REPLACEMENT",
            "run_accession": "NONE",
            "subject_id": "NA",
            "clinical_group": "NA",
            "expected_bytes": "NA",
            "expected_fixed_read_length": "NA",
            "matching_redistribution": "NA",
            "reason": "Remaining 128 deposited FASTQs have nominal/average 50- or 75-nt metadata but no direct evidence of fixed deposited read length; nominal maximum/average is insufficient after the CRR2423909 discrepancy",
        }],
    )


if __name__ == "__main__":
    main()
