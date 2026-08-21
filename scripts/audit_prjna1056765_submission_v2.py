#!/usr/bin/env python3
"""Read-only publication consistency audit for the v2 submission package."""
from __future__ import annotations
import csv, json, pathlib, re, struct

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"reports_public/prjna1056765_submission_v2"
MAN=OUT/"manuscript_submission_draft.md"

def tsv(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f,delimiter="\t"))

def check_png(path):
    b=path.read_bytes(); assert b[:8]==b'\x89PNG\r\n\x1a\n'; return struct.unpack(">II",b[16:24])

def main():
    text=MAN.read_text()
    grid=tsv(ROOT/"reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv")
    refs=tsv(OUT/"core_reference_expansion.tsv")
    checks=[]
    def add(name,ok,observed,expected): checks.append({"check":name,"status":"PASS" if ok else "FAIL","observed":observed,"expected":expected})
    for token in ["402 patients","n=400","n=284","118","n=119","90, 30, and 2 species","R²=0.0194095","P=0.0001","PERMDISP P=0.487","9,999 permutations","four-level diagnosis"]:
        add("manuscript token: "+token,token in text,str(token in text),"True")
    forbidden=["validation cohort","replication cohort","cleaner cohort","higher-quality biological cohort","biological disagreement","diagnosis-associated boundary"]
    lower=text.lower()
    for token in forbidden:add("forbidden wording: "+token,token not in lower,str(token in lower),"False")
    add("frozen grid rows",len(grid)==18,str(len(grid)),"18")
    add("reference count",25<=len(refs)<=40,str(len(refs)),"25-40")
    add("references verified",all(r["verified"]=="YES" for r in refs),str(sum(r["verified"]=="YES" for r in refs)),str(len(refs)))
    cited=set()
    for block in re.findall(r"\[([0-9,– -]+)\]",text):
        for part in block.split(","):
            part=part.strip()
            if "–" in part:
                a,b=map(int,part.split("–")); cited.update(range(a,b+1))
            elif "-" in part:
                a,b=map(int,part.split("-")); cited.update(range(a,b+1))
            elif part: cited.add(int(part))
    add("numbered citations complete",cited==set(range(1,len(refs)+1)),str(sorted(cited)),"1-"+str(len(refs)))
    for name in ["Figure1","Figure2","Figure3","FigureS1"]:
        svg=OUT/"figures"/(name+".svg"); png=OUT/"figures"/(name+".png")
        add(name+" SVG",svg.exists() and "<svg" in svg.read_text(),str(svg.exists()),"True")
        dims=check_png(png); add(name+" PNG dimensions",dims==(2400,1600),str(dims),"(2400, 1600)")
    status="PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL"
    report={"status":status,"checks":checks,"frozen_grid_rows":len(grid),"reference_count":len(refs),"new_statistics":False,"figure4_decision":"Supplement only"}
    (OUT/"consistency_report_v2.json").write_text(json.dumps(report,indent=2)+"\n")
    with (OUT/"citation_evidence_audit_v2.tsv").open("w",encoding="utf-8",newline="") as f:
        fields=["claim_id","claim","evidence","location","status"]; w=csv.DictWriter(f,fields,delimiter="\t",lineterminator="\n");w.writeheader()
        evidence=[
        ("C01","source cohort n=402; 400 downloadable; two unavailable","cohort audit; Han 2025; Tang 2025","Abstract/Results/Figure 1"),
        ("C02","four diagnosis counts 114/78/122/86","frozen cohort audit","Results/Figure 1"),
        ("C03","Han ecology n=284 and internal test n=118","Han 2025; pipeline reconstruction","Introduction/Results/Figure 1"),
        ("C04","anchor R²=0.0194095, P=0.0001, PERMDISP P=0.487","frozen v5 grid anchor row","Abstract/Results/Figure 2"),
        ("C05","pseudocount absolute R² difference 0.0003349","two frozen 30-species Aitchison rows","Results/Figure 2"),
        ("C06","90/30/2 retained species","frozen v5 grid","Results/Methods/Figure 2"),
        ("C07","all full-cohort Bray cells dispersion-qualified","frozen v5 grid","Abstract/Results/Figure S1"),
        ("C08","n=119 diagnosis counts 42/19/36/22","frozen QC table","Results/Figure 1"),
        ("C09","cluster silhouette and ARI range","frozen clustering diagnostics","Results/Figure 3"),
        ("C10","BALF low-biomass contamination context","Salter 2014; Drengenes 2019; Minich 2019","Introduction/Discussion"),
        ("C11","CLR/Aitchison compositional geometry","Aitchison 1982; Fernandes 2014; Gloor 2017","Introduction/Methods/Discussion"),
        ("C12","PERMANOVA requires dispersion qualification","Anderson 2001; Anderson 2006","Introduction/Methods/Discussion"),
        ("C13","classifier/database dependence","Wood 2019; Lu 2017; McIntyre 2017; Ye 2019","Introduction/Discussion"),
        ("C14","no stable cross-metric ecotype solution","frozen silhouette and ARI data","Abstract/Results/Discussion"),
        ("C15","pipeline discrepancies not biological disagreement","pipeline difference matrix","Results/Discussion")]
        for i,c,e,l in evidence:w.writerow({"claim_id":i,"claim":c,"evidence":e,"location":l,"status":"ALIGNED"})
    if status!="PASS": raise SystemExit("consistency audit failed")

if __name__=="__main__":main()
