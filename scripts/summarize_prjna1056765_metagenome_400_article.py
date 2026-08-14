#!/usr/bin/env python3
"""Build article-level interpretation files from completed formal outputs."""

from __future__ import annotations

import argparse
import csv
import json
import hashlib
import shutil
from pathlib import Path


def rows(path:Path):
    with path.open(encoding="utf-8",newline="") as h:return list(csv.DictReader(h,delimiter="\t"))


def write(path:Path,data,header):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=header,delimiter="\t",lineterminator="\n");w.writeheader();w.writerows(data)


def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("reports_public/metagenome_400_formal"));args=p.parse_args();root=args.root
    perm=rows(root/"statistics/permanova_permdisp.tsv");selection={x["metric"]:x for x in rows(root/"integration_30/selection_bias_metrics.tsv")};diff=rows(root/"associations/diagnosis_species_differential.tsv");sig=[x for x in diff if float(x["BH_q"])<.05];stable=[x for x in sig if float(x["QC_sensitivity_BH_q"])<.05];h=json.loads((root/"integration_30/humann_publication_review/summary.json").read_text());hperm=rows(root/"integration_30/humann_publication_review/statistics/permanova_permdisp.tsv")
    lookup={(x["metric"],x["sample_set"]):x for x in perm};a=lookup[("Aitchison","full")];b=lookup[("Bray-Curtis","full")]
    findings=[
        {"finding":"Published diagnosis is associated with microbial composition, but effect size is small.","evidence_class":"FORMAL_INFERENCE","support":f"Aitchison PERMANOVA R2={float(a['PERMANOVA_R2']):.4f}, p={a['PERMANOVA_p']}; PERMDISP p={a['PERMDISP_p']}; replicated in QC-sensitivity cohort.","allowed_claim":"Diagnosis explains a small fraction of composition in this available cohort.","prohibited_overstatement":"Diagnoses form distinct microbiome types or enable diagnosis."},
        {"finding":"Bray-Curtis diagnosis association is dispersion-confounded.","evidence_class":"FORMAL_TEST_WITH_CAUSAL_INTERPRETATION_BLOCKED","support":f"PERMANOVA R2={float(b['PERMANOVA_R2']):.4f}, p={b['PERMANOVA_p']}; PERMDISP p={b['PERMDISP_p']}.","allowed_claim":"Bray distributions differ by diagnosis in location and/or dispersion.","prohibited_overstatement":"Bray centroids differ independently of dispersion."},
        {"finding":f"Five sparse oral-associated species pass full-cohort FDR; {len(stable)} pass strict sensitivity FDR.","evidence_class":"FORMAL_INFERENCE_WITH_SPARSITY_CAUTION","support":", ".join(x["species"] for x in sig),"allowed_claim":"Prespecified diagnosis-associated candidates with small effects and CLR sensitivity.","prohibited_overstatement":"Biomarkers, causal organisms, or clinically validated discriminators."},
        {"finding":"No metric-stable ecotype solution was identified.","evidence_class":"DESCRIPTIVE_EXPLORATORY","support":"Bray silhouette maximum occurs at k=10 boundary; Bray/Aitchison adjusted Rand approximately zero for k=2..10.","allowed_claim":"Metric-dependent exploratory community states.","prohibited_overstatement":"Validated clinical subtypes or natural disease classes."},
        {"finding":"The fixed 30 are strongly selected and not functionally representative.","evidence_class":"FORMAL_SELECTION_BIAS_QUANTIFICATION","support":f"Classified-fraction Cliff delta={float(selection['classified_fraction']['cliffs_delta_selected_vs_other']):.3f}, p={selection['classified_fraction']['mann_whitney_p']}; dominance delta={float(selection['dominant_species_abundance']['cliffs_delta_selected_vs_other']):.3f}, p={selection['dominant_species_abundance']['mann_whitney_p']}; one 7.5% major state absent.","allowed_claim":"The deep-review subset enriches high-classification, strongly dominated communities.","prohibited_overstatement":"The 30 represent functional properties of all 400."},
        {"finding":"HUMAnN pathway results are annotation-detectability and dispersion sensitive.","evidence_class":"SELECTED_30_EXPLORATORY","support":f"Six zero-biological-pathway samples; n30→n24→n23 stable pathways={h['pathway_stable_candidates_n30_n24_n23']}; all six functional PERMANOVA analyses have PERMDISP p<0.05.","allowed_claim":"Selected functional hypotheses and technical sensitivity patterns.","prohibited_overstatement":"Cohort-wide functional differences or mechanism."},
    ];write(root/"tables/article_findings.tsv",findings,["finding","evidence_class","support","allowed_claim","prohibited_overstatement"])
    (root/"methods/article_strategy.md").write_text(f"""# Defensible manuscript strategy

## Recommended main line

Lead with the complete available 400-run BALF taxonomy/community landscape and the modest published-diagnosis association under compositional analysis. The most defensible inferential result is Aitchison PERMANOVA (R²={float(a['PERMANOVA_R2']):.4f}, p={a['PERMANOVA_p']}) with non-significant PERMDISP (p={a['PERMDISP_p']}) and replication in the prespecified QC-sensitivity cohort. Present effect size before significance and emphasize substantial within-diagnosis heterogeneity.

Use the {len(sig)} diagnosis-associated species as sparse, small-effect candidates, not biomarkers. Present raw prevalence/distributions, full-cohort and sensitivity FDR, and CLR group means. Treat Bray-Curtis, clustering and the CLR network as secondary characterization because Bray dispersion is significant and clusters are not stable across metrics.

## Role of the fixed 30 HUMAnN data

HUMAnN can be a supplementary selected deep-review case series. It supports method/annotation observations and generates hypotheses, but its taxonomy-derived groups are not independent and all gene/pathway PERMANOVA results have significant PERMDISP. Six samples have pathway annotation dropout, and n=30→24→23 changes the pathway candidate set materially. Do not merge these results into the 400-run formal inference.

## Should HUMAnN be expanded to 400?

Not for the proposed taxonomy/community paper: the main scientific question is already addressed without a large functional rerun. If cohort-wide functional inference becomes a central claim, the current 30 cannot answer it; a prespecified full eligible cohort or independent validation functional study would then be required. That is a new large-compute design decision and is not recommended or authorized by this analysis.

## Claims that must not appear

- Dominant-pathogen groups independently validate taxa derived from the same matrix.
- Bray PERMANOVA proves diagnosis centroid separation despite significant PERMDISP.
- k=10 clusters are clinical subtypes, stable ecotypes, or disease classes.
- The five taxa are diagnostic biomarkers, causes, ecological interactions, or treatment targets.
- CLR correlations are microbial interactions or causal networks.
- The fixed 30 represent the 400-run functional landscape.
- HUMAnN pathway differences remain biological conclusions when they disappear across n=30→24→23 annotation-dropout sensitivity.
""",encoding="utf-8")
    shutil.copyfile(root/"beta/bray_pcoa.tsv",root/"figures/plot_source_bray_pcoa.tsv")
    shutil.copyfile(root/"beta/aitchison_pcoa.tsv",root/"figures/plot_source_aitchison_pcoa.tsv")
    manifest=[]
    for path in sorted(x for x in root.rglob("*") if x.is_file() and x.name!="manifest.tsv"):
        digest=hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda:handle.read(1024*1024),b""):digest.update(chunk)
        manifest.append({"path":str(path.relative_to(root)),"bytes":path.stat().st_size,"sha256":digest.hexdigest()})
    write(root/"methods/manifest.tsv",manifest,["path","bytes","sha256"])
    return 0


if __name__=="__main__":raise SystemExit(main())
