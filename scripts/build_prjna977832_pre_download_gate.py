#!/usr/bin/env python3
"""Build the PRJNA977832 metadata-only pre-download audit.

This consumes two small, externally retrieved public metadata tables.  It
never opens a sequence file and does not perform any biological processing.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports_public/prjna977832_pre_download_gate"
RUNINFO = Path("/tmp/prjna977832_runinfo_current.csv")
ENA = Path("/tmp/prjna977832_ena_current.tsv")


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    if not RUNINFO.is_file() or not ENA.is_file():
        raise SystemExit("EVIDENCE_REQUIRED: current SRA RunInfo and ENA file reports are required")
    runs = list(csv.DictReader(RUNINFO.open(encoding="utf-8")))
    ena = {row["run_accession"]: row for row in csv.DictReader(ENA.open(encoding="utf-8"), delimiter="\t")}
    if len(runs) != 718 or len(ena) != 718 or {r["Run"] for r in runs} != set(ena):
        raise SystemExit("EVIDENCE_REQUIRED: current public run inventory is not exactly 718 matched SRA/ENA records")
    OUT.mkdir(parents=True, exist_ok=True)
    fastq_bytes = sum(int(ena[r["Run"]]["fastq_bytes"] or 0) for r in runs)
    sra_bytes = sum(int(float(r["size_MB"] or 0) * 1024 * 1024) for r in runs)
    # Exact SRA `size_MB` sum is 939373 MiB; retain this as a distinct archive-size metric.
    run_rows = []
    map_rows = []
    for r in sorted(runs, key=lambda x: x["Run"]):
        e = ena[r["Run"]]
        url = "https://" + e["fastq_ftp"] if e["fastq_ftp"] else "UNRESOLVED"
        state = "SUPPORTED_COMPUTATIONALLY_HOST_DEPLETED" if ("unhost" in r["SampleName"].lower() or "nonhuman" in r["SampleName"].lower()) else "UNRESOLVED_AT_FILE_LEVEL"
        run_rows.append({
            "run_accession": r["Run"], "experiment_accession": r["Experiment"],
            "biosample": r["BioSample"], "sra_sample": r["Sample"],
            "sample_alias": e["sample_alias"], "submitted_sample_name": r["SampleName"],
            "library_name": r["LibraryName"], "group_phenotype_fields": "NONE; Subject_ID/Disease/Affection_Status empty in current RunInfo",
            "platform": r["Model"], "layout": r["LibraryLayout"], "read_length_nt": r["avgLength"],
            "spots": r["spots"], "bases": r["bases"], "sra_size_mib": r["size_MB"],
            "compressed_bytes_ena_fastq": e["fastq_bytes"], "download_url": url,
            "fastq_md5": e["fastq_md5"], "host_depletion_status": state,
            "source": "NCBI RunInfo and ENA read_run filereport retrieved 2026-08-24",
        })
        map_rows.append({
            "run_accession": r["Run"], "biosample": r["BioSample"], "sample_alias": e["sample_alias"],
            "subject_id": "UNRESOLVED", "hiv_group": "UNRESOLVED", "mapping_evidence": "No accession-linked HIV/phenotype field in SRA RunInfo or ENA current read_run report; paper supplement is aggregate ART table.",
            "repeat_sampling_status": "UNRESOLVED", "technical_replicate_status": "UNRESOLVED", "analysis_eligible": "NO",
        })
    write_tsv(OUT / "public_run_inventory.tsv", run_rows, list(run_rows[0]))
    write_tsv(OUT / "sample_group_mapping.tsv", map_rows, list(map_rows[0]))
    covariates = [
        ("HIV status", "VERIFIED paper-level; medical-record variable", "No public run-level link", "primary exposure only after accession bridge"),
        ("age", "VERIFIED aggregate Table 1", "No public run-level link", "potential sensitivity covariate"),
        ("sex", "VERIFIED aggregate Table 1", "No public run-level link", "potential sensitivity covariate"),
        ("ART status/date", "VERIFIED for HIV-positive aggregate / Table S1", "No public run-level link", "potential HIV-positive sensitivity only"),
        ("antibiotic use within 3 months", "VERIFIED aggregate Table 1", "No public run-level link", "potential sensitivity covariate"),
        ("immunosuppressive therapy within 3 months", "VERIFIED aggregate Table 1", "No public run-level link", "potential sensitivity covariate"),
        ("HIV viral load", "VERIFIED aggregate HIV-positive Table 1", "No public run-level link", "potential HIV-positive sensitivity only"),
        ("CD4 count", "VERIFIED aggregate HIV-positive Table 1", "No public run-level link", "potential HIV-positive sensitivity only"),
        ("ICU/severity/comorbidities", "UNRESOLVED", "No accession-linked public table found", "not prespecifiable"),
    ]
    write_tsv(OUT / "clinical_covariate_inventory.tsv", [dict(zip(["variable", "paper_evidence", "sample_level_linkage", "preanalysis_role"], x)) for x in covariates], ["variable", "paper_evidence", "sample_level_linkage", "preanalysis_role"])
    write(OUT / "study_evidence_summary.md", """
# PRJNA977832 / SRP440548 pre-download gate

Study: Tan et al., *Microbiology Spectrum* 2023, DOI `10.1128/spectrum.00005-23`, PMID `37436163`, BioProject `PRJNA977832` / SRA study `SRP440548`.

## Verified paper cohort

The paper reports retrospective BALF mNGS at the First Hospital of Changsha from January 2019 to June 2022. Among 781 reviewed pulmonary-infection patients, exclusions were 17 unknown HIV-status, 6 aged under 18, and 2 pregnant; 756 remained (476 HIV-infected, 280 HIV-uninfected). HIV status was extracted from medical records, so it is an exposure defined independently of mNGS. Pulmonary-infection eligibility, however, was decided by two senior clinicians using clinical presentation, laboratory/imaging and conventional tests **plus positive BALF mNGS and response to antibiotic therapy**. It is therefore not an independent outcome label for microbiome ecology.

BALF DNA was extracted with TIANamp Micro DNA kit. The paper reports library preparation followed by BGISEQ-50/MGISEQ-2000 sequencing, low-quality-read removal, computational human subtraction against hg19 with BWA, and low-complexity removal before PMDB classification. Current SRA metadata instead labels the instrument Illumina NovaSeq 6000; this unresolved platform discrepancy is recorded as a technical-provenance blocker rather than silently harmonized.

## Public inventory result

Current official NCBI RunInfo and ENA read-run reports each contain 718 mutually matching runs/experiments/BioSamples. Every run is SINGLE; 648 have mean length 50 nt and 70 have mean length 40 nt. The 718 distinct BioSamples do not prove 718 distinct people because no participant field is populated. All SRA `Subject_ID`, `Disease`, `Sex`, `Body_Site`, and `Affection_Status` fields are blank.

Sources: [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10434007/), [NCBI BioProject](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA977832), [NCBI RunInfo](https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=PRJNA977832), and [ENA read-run report](https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA977832&result=read_run&fields=run_accession,experiment_accession,sample_accession,secondary_sample_accession,sample_alias,study_accession,library_name,instrument_model,library_layout,base_count,read_count,fastq_bytes,fastq_md5,fastq_ftp&format=tsv&limit=0). No sequence data were opened or downloaded.
""")
    write(OUT / "paper_public_reconciliation.md", """
# Paper-to-public reconciliation

**PAPER_756_TO_PUBLIC_718_STATUS: UNRESOLVED.** The paper flow accounts for 25 exclusions from 781 to 756, but no public accession-linked table states why only 718 SRA runs/BioSamples are deposited. The 38-person arithmetic difference is a discrepancy, not an identity map. It cannot be attributed to non-deposition, technical failure, duplicates, non-BALF specimens, or other modality on the presently auditable evidence.

The only official supplementary item is Table S1 (11.4 KB DOCX), an aggregate comparison of ART and no-ART patients; it does not contain accession, sample alias, subject ID, or a 756-row clinical table. Therefore it cannot bridge any public run to either HIV group. No accession-order, library-number, filename, or demographic matching was used.

The 718 public records have 718 distinct run, experiment, BioSample, SRA-sample and sample-alias values. This establishes one public record per deposited BioSample, but not one BALF specimen or one participant per record. Repeat sampling and technical replication are **UNRESOLVED**, not absent.
""")
    write(OUT / "institution_provenance.md", """
# Institution provenance

**CLINICAL_SITE_STATUS: VERIFIED_SINGLE_CENTER_FIRST_HOSPITAL_OF_CHANGSHA.** The paper says BALF patients were retrospectively reviewed at the First Hospital of Changsha and describes the study as a single referral center. Ethics approval is from that hospital (202128).

**SUBMITTER_SITE_STATUS: VERIFIED_ZHONGNAN_HOSPITAL_WUHAN_UNIVERSITY.** Every current RunInfo record names Zhongnan Hospital, Wuhan University as the repository center; the BioProject submission is also from Zhongnan Hospital.

**SITE_DISCREPANCY_EXPLANATION: SUPPORTED_COLLABORATING_SUBMITTER_AFFILIATION; CLINICAL_ROLE_NOT_EXPLICITLY_DOCUMENTED.** The paper’s author affiliations include both institutions. That supports a collaborating/submitting institution interpretation and does not establish a second clinical recruitment site, sequencing laboratory, or a metadata error. It must not be labelled multicenter without patient-level recruitment evidence.
""")
    write(OUT / "technical_provenance.md", """
# Technical read provenance

Current public SRA/ENA metadata: 718 single-end records, all labelled Illumina NovaSeq 6000; 648 average 50 nt and 70 average 40 nt. ENA reports one gzip FASTQ and MD5 per run. ENA gzip FASTQ bytes total **504,633,902,336** (470.0 GiB). NCBI RunInfo `size_MB` sums to **939,373 MiB = 985,003,982,848 bytes = 917.36 GiB**; this is the SRA archive/container-size metric, not the ENA gzip-FASTQ sum. The public BioProject displays 0.99 Tbytes (rounding convention unspecified).

The paper specifies computational human subtraction against hg19 using BWA after low-quality filtering; no wet-lab host-depletion step is reported. Deposited aliases include `unhost` and `nonhuman.nonspike`, consistent with upstream host depletion, but there is no per-run processing manifest. Thus deposited data are classified **NOT_NATIVE_BUT_USABLE_AS_COHORT_SPECIFIC** if future sample-level identity and technical validation pass. They are not admissible now to the common native Kraken2 layer: pre-classifier human filtering, upstream trimming, and short 40/50-nt read provenance differ from the native anchor.

No FASTQ was downloaded, sampled, parsed, or otherwise read. The audit did not attempt Kraken2 or Bracken. A future bounded pilot, if separately authorized after mapping closure, would need to establish classified fraction, actual read-length distribution and short-read suitability; Bracken cannot be assumed valid without a suitable redistribution/read-length method.
""")
    write(OUT / "storage_value_assessment.md", """
# Storage and scientific-value assessment

**FULL_ACQUISITION_SCIENTIFIC_VALUE: MODERATE.** The paper-level cohort is a large, independent lower-airway HIV-status contrast and HIV is clinically independent of mNGS. It could eventually support classified fraction, alpha diversity, richness, dominance, prevalence and Aitchison beta diversity with PERMANOVA plus mandatory PERMDISP. Any differential abundance would be secondary/exploratory.

**FULL_ACQUISITION_RECOMMENDED: false.** Acquisition of approximately 917.36 GiB SRA-container storage (or 470.0 GiB ENA gzip FASTQ) is not justified until a deterministic public-run-to-HIV map exists and the 756-to-718 deposit discrepancy has an inclusion provenance. The paper reports substantial age, sex, antibiotic-use, immune-status, ART, viral-load and CD4 differences, but public sample-level covariate linkage is absent. A maximal adjustment model would also be inappropriate: ART/CD4/viral load can be downstream of HIV status and require estimand-specific causal justification.

If metadata rescue succeeds, a separately approved bounded pilot may assess throughput and short-read classification only. It must not use inferred group labels or treat mNGS-informed pulmonary-infection adjudication as an independent outcome.
""")
    verdict = {
        "study": "Tan et al. 2023; PRJNA977832/SRP440548; DOI:10.1128/spectrum.00005-23; PMID:37436163",
        "paper_n": 756, "paper_hiv_positive_n": 476, "paper_hiv_negative_n": 280,
        "public_run_n": 718, "public_total_compressed_bytes": fastq_bytes,
        "public_total_compressed_bytes_definition": "sum of ENA fastq_bytes (gzip FASTQ); distinct NCBI SRA size_MB total is 985003982848 bytes / 917.36 GiB",
        "sra_archive_bytes": sra_bytes, "unique_public_subjects": "unresolved",
        "unique_public_biosamples": 718, "paper_756_to_public_718_status": "UNRESOLVED",
        "run_to_hiv_group_status": "UNRESOLVED", "public_hiv_positive_n": "unresolved", "public_hiv_negative_n": "unresolved", "unmapped_public_n": 718,
        "repeat_sampling_present": "unresolved", "technical_replicates_present": "unresolved",
        "clinical_site_status": "VERIFIED_SINGLE_CENTER_FIRST_HOSPITAL_OF_CHANGSHA",
        "submitter_site_status": "VERIFIED_ZHONGNAN_HOSPITAL_WUHAN_UNIVERSITY",
        "site_discrepancy_explanation": "SUPPORTED_COLLABORATING_SUBMITTER_AFFILIATION; CLINICAL_ROLE_NOT_EXPLICITLY_DOCUMENTED",
        "layout": "SINGLE", "read_length": {"40_nt": 70, "50_nt": 648},
        "host_depletion_status": "SUPPORTED_COMPUTATIONAL_HUMAN_SUBTRACTION_HG19_BWA; PER_RUN_DEPOSITED_STATE_NOT_FULLY_MANIFESTED",
        "common_native_kraken2_compatibility": "NOT_NATIVE_BUT_USABLE_AS_COHORT_SPECIFIC",
        "primary_estimand_validity": "HIV status-associated lower-airway community variation is clinically independent at paper level but NOT ACCESSION-ESTIMABLE while run-to-HIV mapping is unresolved",
        "full_acquisition_scientific_value": "MODERATE", "full_acquisition_recommended": False,
        "major_blockers": ["No deterministic run-to-HIV group bridge; all 718 public runs are unmapped.", "Unresolved 756 analysed participants versus 718 deposited runs/BioSamples.", "No public participant/specimen linkage, so repeat sampling and technical replicates cannot be determined.", "Short, computationally host-depleted deposited reads and a paper-versus-SRA instrument discrepancy preclude a common native Kraken2 layer without later technical qualification."],
        "fatal_flaws_if_any": [], "recommended_next_stage": "METADATA_RESCUE",
        "overall_verdict": "PARK_COHORT_PENDING_METADATA_RESCUE: do not acquire approximately 1 TB until an auditable run-to-HIV bridge and public-subset inclusion provenance are recovered.",
        "raw_reads_downloaded": False, "kraken2_run": False, "bracken_run": False, "biological_analysis_executed": False, "deepseek_invoked": False,
    }
    (OUT / "audit_verdict.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
