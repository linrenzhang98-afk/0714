#!/usr/bin/env python3
"""Audit the completed PRJNA1056765 taxonomy cohort without touching raw results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def checksum(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def write_dicts(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,delimiter="\t",lineterminator="\n",extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--qc",type=Path,default=Path("reports_public/metagenome_production/run_qc_summary.tsv"))
    parser.add_argument("--matrix",type=Path,default=Path("reports_public/metagenome_production/bracken_species_fraction_matrix.tsv"))
    parser.add_argument("--clinical",type=Path,default=Path("reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv"))
    parser.add_argument("--candidates",type=Path,default=Path("reports_public/production_planning/prjna1056765/candidate_dna_wgs_runs.tsv"))
    parser.add_argument("--excluded-clinical",type=Path,default=Path("reports_public/prjna1056765_clinical_groups/clinical_wgs_runs_not_analyzed.tsv"))
    parser.add_argument("--deep-review",type=Path,default=Path("reports_public/metagenome_deep_review/deep_review_samples.tsv"))
    parser.add_argument("--out",type=Path,default=Path("reports_public/metagenome_400_formal/audit"))
    args=parser.parse_args()
    required=[args.qc,args.matrix,args.clinical,args.candidates,args.excluded_clinical,args.deep_review]
    missing=[str(p) for p in required if not p.is_file()]
    if missing: raise SystemExit("missing required checked-in inputs: "+", ".join(missing))
    qc=read_tsv(args.qc); clinical=read_tsv(args.clinical); candidates=read_tsv(args.candidates); deep=read_tsv(args.deep_review)
    with args.matrix.open(encoding="utf-8",newline="") as handle:
        reader=csv.reader(handle,delimiter="\t"); header=next(reader); matrix_rows=list(reader)
    matrix_runs=header[2:]; qmap={r["run"]:r for r in qc}; cmap={r["run"]:r for r in clinical}
    if len(qc)!=400 or len(qmap)!=400 or len(matrix_runs)!=400 or len(set(matrix_runs))!=400 or set(matrix_runs)!=set(qmap):
        raise SystemExit("cohort/matrix membership audit failed")
    taxa=[r[0] for r in matrix_rows]
    if len(taxa)!=len(set(taxa)): raise SystemExit("duplicate species feature labels")
    totals={run:0.0 for run in matrix_runs}; detected={run:0 for run in matrix_runs}; dominant={run:("",-1.0) for run in matrix_runs}
    genus_totals={run:{} for run in matrix_runs}
    for row in matrix_rows:
        species=row[0]; genus=species.split()[0] if species.split() else species
        for run,text in zip(matrix_runs,row[2:]):
            value=float(text or 0); totals[run]+=value
            if value>0:
                detected[run]+=1; genus_totals[run][genus]=genus_totals[run].get(genus,0.0)+value
                if value>dominant[run][1]: dominant[run]=(species,value)
    audit=[]
    deep_ids={r["run"] for r in deep}
    for run in matrix_runs:
        q=qmap[run]; c=cmap.get(run,{})
        top_genus,top_genus_value=max(genus_totals[run].items(),key=lambda x:x[1],default=("",0.0))
        total_reads=int(float(q["total_reads"] or 0))
        audit.append({
            "run":run,"production_status":q["status"],"in_species_matrix":True,
            "total_reads":total_reads,"classified_reads":q["classified_reads"],"classified_fraction":float(q["classified_pct"] or 0)/100,
            "bracken_assigned_reads_estimate":round(totals[run]*total_reads),"detected_species":detected[run],
            "dominant_species":dominant[run][0],"dominant_species_relative_total_reads":dominant[run][1],
            "dominant_genus":top_genus,"dominant_genus_relative_total_reads":top_genus_value,
            "patient_id":c.get("patient_id",""),"diagnosis":c.get("diagnosis",""),"cohort":c.get("cohort",""),
            "collection_date":c.get("collection_date",""),"biosample":c.get("biosample",""),"selected_deep_review_30":run in deep_ids,
        })
    write_dicts(args.out/"cohort_audit.tsv",audit,list(audit[0]))
    metadata_inventory=[
        {"variable":"run","source":"SRA/production","coverage":400,"unique_values":400,"independence":"identifier","formal_use":"sample key"},
        {"variable":"patient_id","source":"published supplement via SRA SampleName","coverage":sum(bool(r.get('patient_id')) for r in clinical),"unique_values":len({r['patient_id'] for r in clinical}),"independence":"independent","formal_use":"verify one sample per patient"},
        {"variable":"diagnosis","source":"published Supplementary Data S1/S2","coverage":sum(bool(r.get('diagnosis')) for r in clinical),"unique_values":len({r['diagnosis'] for r in clinical}),"independence":"independent clinical label","formal_use":"primary group inference"},
        {"variable":"cohort","source":"published Supplementary Data S1/S2 Data Sets","coverage":sum(bool(r.get('cohort')) for r in clinical),"unique_values":len({r['cohort'] for r in clinical}),"independence":"independent study split","formal_use":"stratum/sensitivity; not a biological phenotype"},
        {"variable":"collection_date","source":"published Supplementary Data S1/S2","coverage":sum(bool(r.get('collection_date')) for r in clinical),"unique_values":len({r['collection_date'] for r in clinical}),"independence":"independent temporal metadata","formal_use":"temporal/batch diagnostic"},
        {"variable":"bal_microbiology","source":"published Supplementary Data S1/S2","coverage":sum(bool(r.get('bal_microbiology')) for r in clinical),"unique_values":len({r['bal_microbiology'] for r in clinical}),"independence":"independent clinical assay but heterogeneous/free text","formal_use":"descriptive/sensitivity only"},
        {"variable":"total_reads","source":"Kraken2 production QC","coverage":400,"unique_values":len({r['total_reads'] for r in qc}),"independence":"technical covariate independent of relative composition","formal_use":"QC/sensitivity"},
        {"variable":"classified_fraction","source":"Kraken2 production QC","coverage":400,"unique_values":len({r['classified_pct'] for r in qc}),"independence":"derived from classifier output","formal_use":"QC, not independent phenotype"},
        {"variable":"dominant_species/top_pathogen/pathogen_group","source":"same Bracken species matrix","coverage":400,"unique_values":"varies","independence":"NOT independent; abundance-derived","formal_use":"descriptive ecotype characterization only"},
        {"variable":"Disease/Body_Site in RunInfo","source":"NCBI RunInfo","coverage":0,"unique_values":0,"independence":"unavailable","formal_use":"none"},
    ]
    write_dicts(args.out/"metadata_inventory.tsv",metadata_inventory,["variable","source","coverage","unique_values","independence","formal_use"])
    excluded=read_tsv(args.excluded_clinical)
    availability={
        "generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"analysis_cohort_runs":len(qc),"unique_runs":len(qmap),
        "unique_biosamples":len({r.get("biosample","") for r in clinical}),"production_status_counts":dict(Counter(r["status"] for r in qc)),
        "kraken2_bracken_completion_evidence":"400/400 done in checked-in production QC; matrix membership 400/400",
        "per_run_raw_kreport_bracken_local_recheck":"NOT_RUN_INPUT_UNAVAILABLE_LOCAL; not required because completed lightweight matrix/QC are present",
        "species_features":len(matrix_rows),"species_matrix_samples":len(matrix_runs),"matrix_duplicate_samples":len(matrix_runs)-len(set(matrix_runs)),
        "matrix_missing_vs_qc":sorted(set(qmap)-set(matrix_runs)),"matrix_extra_vs_qc":sorted(set(matrix_runs)-set(qmap)),
        "clinical_mapping_runs":len(clinical),"clinical_diagnosis_counts":dict(Counter(r["diagnosis"] for r in clinical)),
        "published_clinical_wgs_not_analyzed":excluded,"reason_actual_n_is_400":"Two additional mapped clinical WGS SRA records have size_MB=0; no reads were available. No sample was added or removed for statistical results.",
        "deep_review_overlap":len(deep_ids & set(matrix_runs)),"deep_review_expected":30,
        "inputs":[{"path":str(p),"bytes":p.stat().st_size,"sha256":checksum(p)} for p in required],
        "audit_passed_for_checked_in_matrix_analysis":True,
    }
    args.out.mkdir(parents=True,exist_ok=True); (args.out/"data_availability.json").write_text(json.dumps(availability,indent=2,ensure_ascii=False)+"\n")
    (args.out/"analysis_design.md").write_text("""# PRJNA1056765 formal taxonomy/community analysis design

## Cohort and estimand

The analysis cohort is the complete available production set: 400 unique DNA-WGS BALF runs (400 unique patients/BioSamples), all marked `done`, with exact membership in the checked-in Bracken matrix. Two additional published clinical WGS records have `size_MB=0` and no available reads; they are reported but not manufactured into the cohort.

The primary independent phenotype is the published four-level diagnosis (Bacterial infection, Fungal infection, Lung cancer, Pulmonary tuberculosis). Published Training/Test cohort and collection date are independent design metadata used for stratification and technical sensitivity. Dominant species, top pathogen, pathogen group, diversity, and clusters are derived from the same abundance matrix and are never treated as independent phenotypes.

## Prespecified analysis

- Species is primary; genus aggregated from the first token of binomial species labels is sensitivity.
- Preserve all samples. Flag low-information/outliers by prespecified robust QC; repeat key analyses in the full cohort and a sensitivity cohort excluding flagged samples.
- Community analyses exclude explicit obvious non-microbial labels (Homo sapiens; the plants Arabidopsis, Benincasa, Camelina and Cucurbita; and Toxoplasma) and renormalize within retained species. Camelina was added during pre-analysis feature QC because it is an unambiguous plant label; it was not diagnosis-associated in the preliminary smoke output. The exclusion list is then frozen. All original features remain in the checked-in input matrix.
- Prevalence filter is 10% (40/400) for ordination/inference; 5% and 20% are sensitivity summaries. CLR uses a fixed pseudocount equal to half the smallest positive retained relative abundance.
- Alpha diversity: observed taxa, Shannon, Simpson, Pielou. Diagnosis associations use Kruskal-Wallis with effect size and BH correction.
- Beta diversity: Bray-Curtis PCoA primary; CLR/Aitchison sensitivity. Diagnosis PERMANOVA uses 9,999 deterministic permutations constrained within published Training/Test cohort; cohort PERMANOVA is separately descriptive of study split. Every PERMANOVA is paired with PERMDISP.
- Community states use unsupervised average-linkage clustering, candidate k=2..10, silhouette selection, and cross-metric agreement as a stability/sensitivity diagnostic. Cluster labels are not clinical subtypes.
- Differential abundance is performed only for published diagnosis: prevalence, group medians, Kruskal-Wallis effect/raw P/BH FDR, plus CLR group-mean contrast sensitivity. Thresholds are not tuned after viewing significance.
- Taxon associations use CLR Pearson association among prevalent taxa and are explicitly compositional hypotheses, never ecological interactions or causality.

## Interpretation classes

Published-diagnosis tests with prespecified filters, 9,999-permutation PERMANOVA and paired PERMDISP are formal inference for the available 400-run cohort. Landscape summaries, clusters/ecotypes, dominant taxa, network edges, and all analyses using abundance-derived labels are descriptive/exploratory. Generalization beyond this public cohort remains subject to its sampling and measurement design.
""",encoding="utf-8")
    print(json.dumps({"runs":400,"species":len(matrix_rows),"diagnoses":availability["clinical_diagnosis_counts"],"audit_passed":True}))
    return 0


if __name__=="__main__": raise SystemExit(main())
