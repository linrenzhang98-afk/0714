#!/usr/bin/env python3
"""Build the frozen PRJNA1056765 manuscript package from checked-in results.

This is deliberately a packaging script: it performs no new inferential test.
It first enforces a numeric consistency gate, then formats frozen statistics,
descriptive summaries, figures, tables, manuscript text, and a claims matrix.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import math
import pathlib
import re
import statistics
import struct
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone


DIAGNOSES = ["Bacterial infection", "Fungal infection", "Lung cancer", "Pulmonary tuberculosis"]
COLORS = {"Bacterial infection": "#0072B2", "Fungal infection": "#009E73", "Lung cancer": "#D55E00", "Pulmonary tuberculosis": "#CC79A7"}
CANDIDATES = ["Parvimonas micra", "Porphyromonas endodontalis", "Porphyromonas gingivalis", "Campylobacter rectus", "Fusobacterium nucleatum"]


def read_tsv(path: pathlib.Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: pathlib.Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def f(x: str | float | int) -> float:
    return float(x)


def q(values: list[float], p: float) -> float:
    values = sorted(values)
    if not values: return float("nan")
    x = (len(values) - 1) * p; lo = int(x); hi = min(lo + 1, len(values) - 1)
    return values[lo] * (hi - x) + values[hi] * (x - lo)


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()


def gate(root: pathlib.Path) -> dict:
    cohort = read_tsv(root / "audit/cohort_audit.tsv")
    qc = read_tsv(root / "qc/cohort_qc.tsv")
    pm = read_tsv(root / "statistics/permanova_permdisp.tsv")
    da = read_tsv(root / "associations/diagnosis_species_differential.tsv")
    sb = {r["metric"]: r for r in read_tsv(root / "integration_30/selection_bias_metrics.tsv")}
    availability = json.loads((root / "audit/data_availability.json").read_text())
    checks: list[dict] = []
    def check(name: str, ok: bool, observed, expected):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "observed": str(observed), "expected": str(expected)})
    check("cohort rows", len(cohort) == 400, len(cohort), 400)
    check("unique runs", len({r['run'] for r in cohort}) == 400, len({r['run'] for r in cohort}), 400)
    check("unique BioSamples", len({r['biosample'] for r in cohort}) == 400, len({r['biosample'] for r in cohort}), 400)
    check("unique patients", len({r['patient_id'] for r in cohort}) == 400, len({r['patient_id'] for r in cohort}), 400)
    check("production complete", all(r["production_status"] == "done" and r["in_species_matrix"] == "True" for r in cohort), sum(r["production_status"] == "done" for r in cohort), 400)
    check("strict QC N", sum(r["sensitivity_included"] == "True" for r in qc) == 119, sum(r["sensitivity_included"] == "True" for r in qc), 119)
    check("QC flagged N", sum(bool(r["qc_flags"]) for r in qc) == 281, sum(bool(r["qc_flags"]) for r in qc), 281)
    get = lambda metric, sample: next(r for r in pm if r["metric"] == metric and r["sample_set"] == sample)
    a, b = get("Aitchison", "full"), get("Bray-Curtis", "full")
    check("Aitchison R2", abs(f(a["PERMANOVA_R2"]) - .0194) < 5e-5, a["PERMANOVA_R2"], "0.0194 +/- rounding")
    check("Aitchison P", f(a["PERMANOVA_p"]) == .0001, a["PERMANOVA_p"], .0001)
    check("Aitchison PERMDISP P", abs(f(a["PERMDISP_p"]) - .487) < 5e-4, a["PERMDISP_p"], "0.487 +/- rounding")
    check("Bray R2", abs(f(b["PERMANOVA_R2"]) - .0153) < 5e-5, b["PERMANOVA_R2"], "0.0153 +/- rounding")
    check("Bray P", f(b["PERMANOVA_p"]) == .0115, b["PERMANOVA_p"], .0115)
    check("Bray PERMDISP P", f(b["PERMDISP_p"]) == .0013, b["PERMDISP_p"], .0013)
    sig = [r for r in da if f(r["BH_q"]) < .05]
    stable = [r for r in sig if r["QC_sensitivity_BH_q"] and f(r["QC_sensitivity_BH_q"]) < .05]
    check("full FDR species", len(sig) == 5 and [r["species"] for r in sig] == CANDIDATES, [r["species"] for r in sig], CANDIDATES)
    stable_expected = ["Porphyromonas gingivalis", "Campylobacter rectus", "Fusobacterium nucleatum"]
    check("sensitivity-stable species", [r["species"] for r in stable] == stable_expected, [r["species"] for r in stable], stable_expected)
    for metric, s, o, tol in [("classified_fraction", .0459, .0175, 5e-5), ("dominant_species_abundance", .956, .390, 5e-4)]:
        check(metric + " selected median", abs(f(sb[metric]["selected_median"]) - s) < tol, sb[metric]["selected_median"], s)
        check(metric + " other median", abs(f(sb[metric]["other_median"]) - o) < tol, sb[metric]["other_median"], o)
    check("two unavailable published WGS", len(availability["published_clinical_wgs_not_analyzed"]) == 2 and all(x["size_mb"] == "0" for x in availability["published_clinical_wgs_not_analyzed"]), availability["published_clinical_wgs_not_analyzed"], "2 records with size_MB=0")
    prose = "\n".join((root / p).read_text() for p in ["summary.md", "methods/article_strategy.md", "tables/article_findings.tsv", "limitations.md", "integration_30/humann_publication_review/summary.md"])
    for token in ["0.0194", "0.0001", "0.487", "0.0153", "0.0115", "0.0013", "119", "0.0459", "0.0175", "0.956", "0.390"]:
        check("prose contains " + token, token in prose, token in prose, True)
    if any(x["status"] == "FAIL" for x in checks):
        raise RuntimeError("Publication consistency gate failed: " + "; ".join(x["check"] for x in checks if x["status"] == "FAIL"))
    return {"checks": checks, "cohort": cohort, "qc": qc, "pm": pm, "da": da, "sb": sb, "availability": availability}


class SVG:
    def __init__(self, title: str, w=1600, h=1120): self.w=w; self.h=h; self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', '<rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:Arial,sans-serif;fill:#222}.t{font-size:27px;font-weight:700}.p{font-size:22px;font-weight:700}.s{font-size:15px}.n{font-size:13px;fill:#555}</style>', f'<text x="45" y="42" class="t">{html.escape(title)}</text>']
    def panel(self,x,y,w,h,label,title): self.s += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff" stroke="#ccd3da"/>',f'<text x="{x+15}" y="{y+28}" class="p">{label}</text>',f'<text x="{x+50}" y="{y+27}" class="s">{html.escape(title)}</text>']
    def text(self,x,y,t,cls="s",anchor="start",fill=None): self.s.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"'+(f' fill="{fill}"' if fill else '')+f'>{html.escape(str(t))}</text>')
    def rect(self,x,y,w,h,fill,stroke="none",op=1): self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" opacity="{op}"/>')
    def line(self,x1,y1,x2,y2,stroke="#444",width=1,dash=""): self.s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def circle(self,x,y,r,fill,op=.65,stroke="none"): self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" opacity="{op}" stroke="{stroke}"/>')
    def finish(self,path): self.s.append('</svg>'); path.write_text('\n'.join(self.s)+'\n',encoding='utf-8')


# Tiny dependency-free PNG companion. SVG is the editable publication master.
FONT_BLOB = r'''
FONT={
"A":"0111010001111111000110001","B":"1111010001111101000111110","C":"0111110000100001000001111","D":"1111010001100011000111110","E":"1111110000111101000011111","F":"1111110000111101000010000","G":"0111110000101111000101111","H":"1000110001111111000110001","I":"1111100100001000010011111","J":"0011100010000101001001100","K":"1000110010111001001010001","L":"1000010000100001000011111","M":"1000111011101011000110001","N":"1000111001101011001110001","O":"0111010001100011000101110","P":"1111010001111101000010000","Q":"0111010001100011010101111","R":"1111010001111101010010010","S":"0111110000011100000111110","T":"1111100100001000010000100","U":"1000110001100011000101110","V":"1000110001100010101000100","W":"1000110001101011101110001","X":"1000101010001000101010001","Y":"1000101010001000010000100","Z":"1111100010001000100011111","0":"0111010001101011000101110","1":"0010001100001000010001110","2":"0111010001000100010011111","3":"1111000001001100000111110","4":"0001000110010101111100010","5":"1111110000111100000111110","6":"0111010000111101000101110","7":"1111100010001000100001000","8":"0111010001011101000101110","9":"0111010001011110000101110","-":"0000000000111110000000000",".":"0000000000000000011000110","/":"0000100010001000100010000"," ":"0000000000000000000000000",":":"0000000110000000011000000","=":"0000011111000001111100000","<":"0001000100010000010000010",">":"0100000100001000100001000","%":"1100100010001000100010011","_":"0000000000000000000011111","(":"0010001000010000100000100",")":"0010000010000100001000100",",
"+":"0000000100011100010000000"}
'''
# Recover the valid 5x5 glyph pairs from the embedded dependency-free font.
FONT = dict(re.findall(r'"(.)":"([01]{25})"', FONT_BLOB))
FONT.setdefault(" ", "0" * 25)


class PNG:
    def __init__(self,w=1600,h=1120): self.w=w;self.h=h;self.p=bytearray([255])*(w*h*3)
    def px(self,x,y,c):
        if 0<=x<self.w and 0<=y<self.h:
            i=(y*self.w+x)*3; self.p[i:i+3]=bytes(c)
    def rect(self,x,y,w,h,c):
        for yy in range(max(0,int(y)),min(self.h,int(y+h))):
            i=(yy*self.w+max(0,int(x)))*3; n=max(0,min(self.w,int(x+w))-max(0,int(x))); self.p[i:i+n*3]=bytes(c)*n
    def line(self,x1,y1,x2,y2,c=(60,60,60),width=2):
        steps=max(abs(int(x2-x1)),abs(int(y2-y1)),1)
        for j in range(steps+1):
            x=round(x1+(x2-x1)*j/steps);y=round(y1+(y2-y1)*j/steps)
            self.rect(x-width//2,y-width//2,width,width,c)
    def circle(self,cx,cy,r,c):
        for y in range(int(cy-r),int(cy+r)+1):
            d=int(math.sqrt(max(0,r*r-(y-cy)**2))); self.rect(cx-d,y,2*d+1,1,c)
    def text(self,x,y,s,scale=3,c=(30,30,30)):
        x0=x
        for ch in str(s).upper():
            bits=FONT.get(ch,FONT[" "])
            for j,b in enumerate(bits):
                if b=="1": self.rect(x+(j%5)*scale,y+(j//5)*scale,scale,scale,c)
            x+=6*scale
            if x>self.w-30: y+=8*scale;x=x0
    def save(self,path):
        raw=b''.join(b'\x00'+self.p[y*self.w*3:(y+1)*self.w*3] for y in range(self.h))
        def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
        path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',self.w,self.h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))


def bars(svg,x,y,w,h,items,color="#3B82F6",maxv=None):
    maxv=maxv or max(v for _,v in items) or 1
    bh=(h-35)/max(1,len(items))
    for i,(name,v) in enumerate(items):
        yy=y+35+i*bh; svg.rect(x+145,yy,bh and (w-175)*v/maxv, max(4,bh*.58),color); svg.text(x+140,yy+11,name,"n","end"); svg.text(x+150+(w-175)*v/maxv,yy+11,f"{v:.3g}","n")


def scatter(svg, rows, x,y,w,h, xkey="PCoA1",ykey="PCoA2",highlight=None):
    xs=[f(r[xkey]) for r in rows];ys=[f(r[ykey]) for r in rows]; xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
    sx=lambda v:x+25+(w-50)*(v-xmin)/(xmax-xmin or 1); sy=lambda v:y+h-25-(h-50)*(v-ymin)/(ymax-ymin or 1)
    svg.line(x+25,y+h-25,x+w-20,y+h-25,"#aaa");svg.line(x+25,y+35,x+25,y+h-25,"#aaa")
    for r in rows:
        selected=highlight and r.get(highlight)=="True"; svg.circle(sx(f(r[xkey])),sy(f(r[ykey])),4.3 if selected else 2.5,COLORS.get(r.get("diagnosis"),"#777"),.9 if selected else .38,"#111" if selected else "none")


def generic_png(path,title,panels,decorator):
    p=PNG();p.text(45,25,title,4); coords=[(35,75,755,490),(810,75,755,490),(35,590,490,490),(555,590,490,490),(1075,590,490,490)]
    for i,(label,ptitle) in enumerate(panels):
        x,y,w,h=coords[i];p.rect(x,y,w,h,(248,250,252));p.line(x,y,x+w,y,(190,200,210));p.text(x+15,y+15,label,4);p.text(x+65,y+17,ptitle,2)
    decorator(p,coords);p.save(path)


def png_bars(p: PNG, box, values, color=(0,114,178), maximum=None):
    x,y,w,h=box; maximum=maximum or max(values or [1]); n=max(1,len(values)); bh=max(5,(h-125)//n)
    for i,v in enumerate(values):
        yy=y+70+i*bh; p.rect(x+45,yy,max(2,int((w-90)*v/(maximum or 1))),max(3,bh-4),color)


def png_scatter(p: PNG, box, rows, selected_key=None):
    x,y,w,h=box; xs=[f(r["PCoA1"]) for r in rows];ys=[f(r["PCoA2"]) for r in rows];xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
    p.line(x+35,y+h-45,x+w-25,y+h-45,(150,150,150));p.line(x+35,y+55,x+35,y+h-45,(150,150,150))
    rgb={"Bacterial infection":(0,114,178),"Fungal infection":(0,158,115),"Lung cancer":(213,94,0),"Pulmonary tuberculosis":(204,121,167)}
    for r in rows:
        xx=x+35+int((w-65)*(f(r["PCoA1"])-xmin)/(xmax-xmin or 1));yy=y+h-45-int((h-100)*(f(r["PCoA2"])-ymin)/(ymax-ymin or 1));rad=4 if selected_key and r.get(selected_key)=="True" else 2;p.circle(xx,yy,rad,rgb[r["diagnosis"]])


def make_figures(root:pathlib.Path,out:pathlib.Path,data:dict)->list[dict]:
    figdir=out/"figures";figdir.mkdir(parents=True,exist_ok=True); legends=[]
    qc=data["qc"]; landscape=read_tsv(root/"taxonomy/species_landscape.tsv"); dom=read_tsv(root/"taxonomy/dominant_species_distribution.tsv"); alpha=read_tsv(root/"alpha/alpha_diversity.tsv"); pcoa=read_tsv(root/"beta/aitchison_pcoa.tsv")
    # Figure 1 source and vector
    src=[]
    for r in qc: src += [{"section":"sample_qc","run":r["run"],"category":r["diagnosis"],"metric":"classified_fraction","value":r["classified_fraction"]},{"section":"sample_qc","run":r["run"],"category":r["diagnosis"],"metric":"observed_species","value":r["observed_species"]},{"section":"sample_qc","run":r["run"],"category":r["diagnosis"],"metric":"shannon","value":r["shannon"]}]
    for r in landscape[:20]: src.append({"section":"species_prevalence","run":"","category":r["species"],"metric":"prevalence","value":r["prevalence"]})
    for r in dom: src.append({"section":"dominant_species","run":"","category":r["dominant_species"],"metric":"sample_fraction","value":r["fraction"]})
    write_tsv(figdir/"Figure1_source.tsv",src,["section","run","category","metric","value"])
    s=SVG("Figure 1. Cohort and taxonomic landscape"); P=[(35,70,500,460),(555,70,500,460),(1075,70,490,460),(35,550,750,530),(805,550,760,530)]
    titles=["Cohort workflow","Classified fraction","Dominant species","Top prevalent species","Richness and Shannon"]
    for i,z in enumerate(P):s.panel(*z,chr(65+i),titles[i])
    s.text(280,210,"402 published WGS records","s","middle");s.line(280,225,280,285,"#555",3);s.text(280,315,"400 analyzable","p","middle");s.text(280,350,"400 runs = 400 BioSamples = 400 patients","n","middle");s.text(280,385,"2 records had size_MB=0","n","middle")
    vals=[f(r["classified_fraction"]) for r in qc]; bins=[0]*10
    for v in vals:bins[min(9,int(min(v,.099999)/.01))]+=1
    bars(s,570,105,455,375,[(f"{i}-{i+1}%",v) for i,v in enumerate(bins)],"#56B4E9")
    bars(s,1090,105,445,375,[(r["dominant_species"][:24],f(r["fraction"])) for r in dom[:12]],"#E69F00")
    bars(s,55,585,700,440,[(r["species"][:27],f(r["prevalence"])) for r in landscape[:15]],"#009E73",1)
    for j,d in enumerate(DIAGNOSES):
        rr=[r for r in alpha if r["diagnosis"]==d]; ox=[f(r["observed_species"]) for r in rr];sh=[f(r["shannon"]) for r in rr];yy=640+j*90;s.rect(835,yy,20,20,COLORS[d]);s.text(865,yy+15,d,"s");s.text(865,yy+43,f"richness median {statistics.median(ox):.1f}; Shannon {statistics.median(sh):.2f}","n")
    s.finish(figdir/"Figure1.svg")
    def raster1(p,c):
        p.text(c[0][0]+120,c[0][1]+150,"402 TO 400",5);p.text(c[0][0]+120,c[0][1]+230,"400 RUNS BIOSAMPLES PATIENTS",2)
        png_bars(p,c[1],bins,(86,180,233));png_bars(p,c[2],[f(r["fraction"]) for r in dom[:12]],(230,159,0),1)
        png_bars(p,c[3],[f(r["prevalence"]) for r in landscape[:15]],(0,158,115),1)
        png_bars(p,c[4],[statistics.median([f(r["shannon"]) for r in alpha if r["diagnosis"]==d]) for d in DIAGNOSES],(204,121,167),2.5)
    generic_png(figdir/"Figure1.png","FIGURE 1 COHORT AND TAXONOMIC LANDSCAPE",[("A","COHORT WORKFLOW"),("B","CLASSIFIED FRACTION"),("C","DOMINANT SPECIES"),("D","TOP PREVALENCE"),("E","RICHNESS SHANNON")],raster1)
    legends.append({"figure":"Figure 1","legend":"Cohort construction and taxonomic landscape. (A) Of 402 mapped published WGS records, 400 had sequence data and exact production/matrix membership; two size_MB=0 records were unavailable. Each analyzable run mapped uniquely to one BioSample and patient. (B) Classified-read fraction distribution. (C) Distribution of dominant microbial species, retaining samples without a microbial dominant species as ‘None’. (D) Prevalence of the 15 most prevalent species. (E) Diagnosis-stratified descriptive summaries of observed richness and Shannon diversity. QC flags were not exclusion criteria; all 400 samples remained in the primary analysis."})
    # Figure 2
    src=[]
    for r in pcoa: src.append({"section":"aitchison_pcoa","metric":r["run"],"cohort":r["diagnosis"],"value1":r["PCoA1"],"value2":r["PCoA2"],"value3":r["sensitivity_included"]})
    for r in data["pm"]: src.append({"section":"permanova_permdisp","metric":r["metric"],"cohort":r["sample_set"],"value1":r["PERMANOVA_R2"],"value2":r["PERMANOVA_p"],"value3":r["PERMDISP_p"]})
    write_tsv(figdir/"Figure2_source.tsv",src,["section","metric","cohort","value1","value2","value3"])
    s=SVG("Figure 2. Diagnosis-associated community composition");P=[(35,70,750,500),(805,70,760,500),(35,590,490,490),(555,590,490,490),(1075,590,490,490)];titles=["Aitchison PCoA","Group centroids","PERMANOVA effect sizes","PERMDISP","Strict-QC subset in full ordination"]
    for i,z in enumerate(P):s.panel(*z,chr(65+i),titles[i])
    scatter(s,pcoa,55,115,710,430)
    for j,d in enumerate(DIAGNOSES):
        rr=[r for r in pcoa if r["diagnosis"]==d];cx=statistics.mean(f(r["PCoA1"]) for r in rr);cy=statistics.mean(f(r["PCoA2"]) for r in rr);s.rect(840,135+j*90,24,24,COLORS[d]);s.text(875,153+j*90,d,"s");s.text(875,178+j*90,f"centroid ({cx:.2f}, {cy:.2f}); n={len(rr)}","n")
    pr={(r["metric"],r["sample_set"]):r for r in data["pm"]}
    bars(s,55,635,440,385,[(m+" "+c,f(pr[(m,c)]["PERMANOVA_R2"])) for m in ["Aitchison","Bray-Curtis"] for c in ["full","QC-sensitivity"]],"#0072B2",.08)
    for j,m in enumerate(["Aitchison","Bray-Curtis"]):
        r=pr[(m,"full")];s.text(585,690+j*130,m,"s");s.text(585,720+j*130,f"PERMDISP p={f(r['PERMDISP_p']):.4g}","p");s.text(585,750+j*130,"not dispersion-driven" if f(r["PERMDISP_p"])>=.05 else "dispersion differs; qualify", "n")
    scatter(s,pcoa,1095,635,440,380,highlight="sensitivity_included")
    s.finish(figdir/"Figure2.svg")
    def raster2(p,c):
        png_scatter(p,c[0],pcoa);png_scatter(p,c[1],pcoa)
        png_bars(p,c[2],[f(pr[(m,z)]["PERMANOVA_R2"]) for m in ["Aitchison","Bray-Curtis"] for z in ["full","QC-sensitivity"]],(0,114,178),.08)
        png_bars(p,c[3],[f(pr[(m,"full")]["PERMDISP_p"]) for m in ["Aitchison","Bray-Curtis"]],(213,94,0),.5);png_scatter(p,c[4],pcoa,"sensitivity_included")
    generic_png(figdir/"Figure2.png","FIGURE 2 DIAGNOSIS ASSOCIATED COMPOSITION",[("A","AITCHISON PCOA"),("B","GROUP CENTROIDS"),("C","PERMANOVA R2"),("D","PERMDISP"),("E","STRICT QC N119")],raster2)
    legends.append({"figure":"Figure 2","legend":"Published diagnosis is associated with modest compositional differences. (A) Full-cohort Aitchison PCoA colored by published diagnosis. (B) Group centroids are shown descriptively without implying sharp separation. (C) PERMANOVA R² for full and prespecified strict-QC sensitivity cohorts. Full-cohort Aitchison R²=0.0194, p=0.0001; Bray–Curtis R²=0.0153, p=0.0115 (9,999 cohort-stratified permutations). (D) Aitchison PERMDISP was not significant (p=0.487), whereas Bray–Curtis PERMDISP was significant (p=0.0013), requiring qualification of the Bray result. (E) The 119 strict-QC samples are highlighted within the full-cohort Aitchison ordination; this is not a separately refitted ordination."})
    # Figure 3
    differential={r["species"]:r for r in data["da"]}; matrix=read_tsv(root/"taxonomy/species_relative_abundance.tsv.gz"); byrun={r["run"]:r for r in qc}; raw=[]
    for row in matrix:
        if row["species"] in CANDIDATES:
            for run,val in row.items():
                if run!="species":raw.append({"species":row["species"],"run":run,"diagnosis":byrun[run]["diagnosis"],"relative_abundance":val,"is_zero":str(f(val)==0)})
    src=[]
    for r in raw:src.append({"section":"raw_abundance",**r,"prevalence":"","effect_size":"","full_p":"","full_fdr":"","sensitivity_p":"","sensitivity_fdr":"","clr_means":""})
    for name in CANDIDATES:
        r=differential[name];src.append({"section":"frozen_differential","species":name,"run":"","diagnosis":r["highest_median_diagnosis"],"relative_abundance":"","is_zero":"","prevalence":r["prevalence"],"effect_size":r["epsilon_squared"],"full_p":r["cohort_stratified_permutation_p"],"full_fdr":r["BH_q"],"sensitivity_p":r["QC_sensitivity_cohort_stratified_permutation_p"],"sensitivity_fdr":r["QC_sensitivity_BH_q"],"clr_means":r["group_CLR_means_json"]})
    write_tsv(figdir/"Figure3_source.tsv",src)
    s=SVG("Figure 3. Diagnosis-associated candidate species");P=[(35,70,500,460),(555,70,500,460),(1075,70,490,460),(35,550,750,530),(805,550,760,530)];titles=["Overall prevalence","Observed zeros","CLR group means","Full and strict-QC FDR","Evidence classification"]
    for i,z in enumerate(P):s.panel(*z,chr(65+i),titles[i])
    abbr=[("P. micra",differential[CANDIDATES[0]]),("P. endodontalis",differential[CANDIDATES[1]]),("P. gingivalis",differential[CANDIDATES[2]]),("C. rectus",differential[CANDIDATES[3]]),("F. nucleatum",differential[CANDIDATES[4]])]
    bars(s,55,110,450,365,[(a,f(r["prevalence"])) for a,r in abbr],"#009E73",.35)
    zero=Counter(r["species"] for r in raw if r["is_zero"]=="True")
    bars(s,575,110,450,365,[(a,zero[n]/400) for a,(n,_) in zip([x[0] for x in abbr],[(x[0],x[1]) for x in abbr])],"#999999",1)
    for i,(a,r) in enumerate(abbr):
        means=json.loads(r["group_CLR_means_json"])
        for j,d in enumerate(DIAGNOSES):
            v=means[d]; col="#B2182B" if v>0 else "#2166AC";s.rect(1100+j*95,145+i*62,86,45,col,op=min(.9,.25+abs(v)/3));
        s.text(1095,175+i*62,a,"n","end")
    for j,d in enumerate(DIAGNOSES):s.text(1143+j*95,455,d.split()[0][:5],"n","middle")
    for i,(a,r) in enumerate(abbr):
        yy=610+i*82;s.text(55,yy+20,a,"s");s.rect(215,yy,480*min(1,-math.log10(f(r["BH_q"]))/5),22,"#0072B2");s.text(705,yy+17,f"full q={f(r['BH_q']):.4g}; strict q={f(r['QC_sensitivity_BH_q']):.4g}","n","end")
    stable={"Porphyromonas gingivalis","Campylobacter rectus","Fusobacterium nucleatum"}
    for i,(a,r) in enumerate(abbr):
        name=CANDIDATES[i];yy=625+i*83;s.text(840,yy,name,"s");s.text(840,yy+27,"full + strict-QC FDR" if name in stable else "full-cohort FDR only","p" if name in stable else "n");s.text(840,yy+50,"candidate taxon; not a biomarker","n")
    s.finish(figdir/"Figure3.svg")
    def raster3(p,c):
        png_bars(p,c[0],[f(r["prevalence"]) for _,r in abbr],(0,158,115),.35);png_bars(p,c[1],[zero[n]/400 for n in CANDIDATES],(120,120,120),1)
        means=[json.loads(r["group_CLR_means_json"])[d] for _,r in abbr for d in DIAGNOSES];png_bars(p,c[2],[abs(v) for v in means],(204,121,167),max(abs(v) for v in means))
        png_bars(p,c[3],[-math.log10(f(r["BH_q"])) for _,r in abbr],(0,114,178),5);png_bars(p,c[4],[1 if CANDIDATES[i] in stable else .45 for i in range(5)],(213,94,0),1)
    generic_png(figdir/"Figure3.png","FIGURE 3 DIAGNOSIS ASSOCIATED SPECIES",[("A","PREVALENCE"),("B","ZERO FRACTION"),("C","CLR MEANS"),("D","FULL STRICT FDR"),("E","EVIDENCE CLASS")],raster3)
    legends.append({"figure":"Figure 3","legend":"Five prespecified-analysis candidate species associated with published diagnosis. (A) Overall prevalence. (B) Observed zero fraction, displayed explicitly because group medians were generally zero. (C) Diagnosis-specific CLR means (red, positive; blue, negative). (D) Full-cohort and strict-QC BH FDR values from the frozen differential analysis. (E) Evidence classification. Parvimonas micra and Porphyromonas endodontalis passed full-cohort FDR only; Porphyromonas gingivalis, Campylobacter rectus, and Fusobacterium nucleatum also passed strict-QC FDR. These are candidate taxa, not diagnostic biomarkers."})
    # Figure 4
    diag=read_tsv(root/"clustering/cluster_diagnostics.tsv");states=read_tsv(root/"clustering/sample_community_states.tsv");src=[]
    for r in diag:src.append({"section":"cluster_diagnostics","k":r["k"],"category":"","value1":r["bray_silhouette"],"value2":r["aitchison_silhouette"],"value3":r["bray_aitchison_adjusted_rand"]})
    for st,n in Counter(r["community_state"] for r in states).items():src.append({"section":"k10_state_size","k":"10","category":st,"value1":n,"value2":n/400,"value3":""})
    for r in dom:src.append({"section":"dominant_species","k":"","category":r["dominant_species"],"value1":r["samples"],"value2":r["fraction"],"value3":""})
    write_tsv(figdir/"Figure4_source.tsv",src,["section","k","category","value1","value2","value3"])
    s=SVG("Figure 4. Community heterogeneity and absence of stable ecotypes");P=[(35,70,750,500),(805,70,760,500),(35,590,490,490),(555,590,490,490),(1075,590,490,490)];titles=["Silhouette k=2–10","Cross-metric ARI","Bray k=10 state sizes","Dominant-species heterogeneity","Interpretation"]
    for i,z in enumerate(P):s.panel(*z,chr(65+i),titles[i])
    for key,col in [("bray_silhouette","#0072B2"),("aitchison_silhouette","#D55E00")]:
        pts=[]
        for r in diag:pts.append((85+(f(r["k"])-2)/8*650,500-f(r[key])*650))
        for a,bp in zip(pts,pts[1:]):s.line(*a,*bp,col,4)
        for a in pts:s.circle(*a,5,col,.9)
    s.text(100,545,"Bray (blue); Aitchison (orange). Boundary maxima are not stable subtype evidence.","n")
    pts=[(850+(f(r["k"])-2)/8*650,330-f(r["bray_aitchison_adjusted_rand"])*900) for r in diag]
    s.line(850,330,1500,330,"#999",1,"5,5")
    for a,bp in zip(pts,pts[1:]):s.line(*a,*bp,"#6A3D9A",4)
    for a in pts:s.circle(*a,5,"#6A3D9A",.9)
    count=Counter(r["community_state"] for r in states);bars(s,55,635,440,385,[("state "+k,n/400) for k,n in sorted(count.items(),key=lambda x:int(x[0]))],"#56B4E9",.35)
    bars(s,575,635,440,385,[(r["dominant_species"][:19],f(r["fraction"])) for r in dom[:10]],"#E69F00",.25)
    s.text(1110,700,"Community states are exploratory.","p");s.text(1110,750,"Silhouette depends on metric and k.","s");s.text(1110,790,"Bray–Aitchison ARI is near zero.","s");s.text(1110,830,"No stable diagnosis-linked ecotype.","p");s.text(1110,885,"Do not call clusters clinical subtypes.","n")
    s.finish(figdir/"Figure4.svg")
    def raster4(p,c):
        for box,key,col in [(c[0],"bray_silhouette",(0,114,178)),(c[0],"aitchison_silhouette",(213,94,0)),(c[1],"bray_aitchison_adjusted_rand",(106,61,154))]:
            x,y,w,h=box;vals=[f(r[key]) for r in diag];lo=min(vals+[0]);hi=max(vals+[.01]);pts=[(x+45+i*(w-90)//8,y+h-55-int((h-130)*(v-lo)/(hi-lo or 1))) for i,v in enumerate(vals)]
            for aa,bb in zip(pts,pts[1:]):p.line(*aa,*bb,col,4)
        png_bars(p,c[2],[n/400 for _,n in sorted(count.items(),key=lambda x:int(x[0]))],(86,180,233),.35);png_bars(p,c[3],[f(r["fraction"]) for r in dom[:10]],(230,159,0),.25);p.text(c[4][0]+65,c[4][1]+180,"ARI APPROX ZERO",3);p.text(c[4][0]+65,c[4][1]+240,"NO STABLE ECOTYPES",3)
    generic_png(figdir/"Figure4.png","FIGURE 4 COMMUNITY HETEROGENEITY",[("A","SILHOUETTE K2-10"),("B","CROSS METRIC ARI"),("C","STATE SIZES"),("D","DOMINANT TAXA"),("E","NO STABLE ECOTYPES")],raster4)
    legends.append({"figure":"Figure 4","legend":"Exploratory community structure is metric dependent. (A) Silhouette values for k=2–10 under Bray–Curtis and Aitchison representations. (B) Adjusted Rand index comparing assignments across metrics was approximately zero. (C) Sizes of the exploratory Bray k=10 community states. (D) Dominant-species heterogeneity. (E) Prespecified interpretation. The boundary behavior and weak cross-metric agreement do not support stable diagnosis-linked ecotypes or clinical subtypes."})
    # Figure 5
    coverage=read_tsv(root/"integration_30/community_state_coverage_k2_k10.tsv");hum=json.loads((root/"integration_30/humann_publication_review/summary.json").read_text());src=[]
    for r in data["sb"].values():src.append({"section":"selection_bias","metric":r["metric"],"group":"selected30","value1":r["selected_median"],"value2":r["selected_mean"],"value3":r["mann_whitney_p"]});src.append({"section":"selection_bias","metric":r["metric"],"group":"other370","value1":r["other_median"],"value2":r["other_mean"],"value3":r["mann_whitney_p"]})
    for r in pcoa:src.append({"section":"pcoa_position","metric":r["run"],"group":r["diagnosis"],"value1":r["PCoA1"],"value2":r["PCoA2"],"value3":r["selected_deep_review_30"]})
    for r in coverage:
        if r["k"]=="10":src.append({"section":"state_coverage_k10","metric":r["community_state"],"group":"selected30","value1":r["selected30_fraction"],"value2":r["full_fraction"],"value3":r["covered_by_selected30"]})
    for metric,val in [("HUMAnN_total",30),("biological_pathway_present",24),("extreme_sparse_excluded",23),("zero_biological_pathway",6),("stable_pathway_candidates",hum["pathway_stable_candidates_n30_n24_n23"])]:src.append({"section":"humann_dropout","metric":metric,"group":"","value1":val,"value2":"","value3":""})
    write_tsv(figdir/"Figure5_source.tsv",src,["section","metric","group","value1","value2","value3"])
    s=SVG("Figure 5. Fixed-30 selection bias and functional limitations");P=[(35,70,500,460),(555,70,500,460),(1075,70,490,460),(35,550,750,530),(805,550,760,530)];titles=["Classified fraction","Dominant-species abundance","Position in cohort PCoA","Community-state coverage","HUMAnN annotation dropout"]
    for i,z in enumerate(P):s.panel(*z,chr(65+i),titles[i])
    for panel,metric,x0 in [(P[0],"classified_fraction",70),(P[1],"dominant_species_abundance",590)]:
        r=data["sb"][metric];mx=max(f(r["selected_median"]),f(r["other_median"]))
        bars(s,x0,150,430,250,[("fixed 30",f(r["selected_median"])),("other 370",f(r["other_median"]))],"#D55E00",mx*1.15)
        s.text(x0+210,450,f"Mann–Whitney p={f(r['mann_whitney_p']):.2g}","n","middle")
    scatter(s,pcoa,1095,115,440,360,highlight="selected_deep_review_30")
    c10=[r for r in coverage if r["k"]=="10"];bars(s,55,610,700,410,[("state "+r["community_state"]+(' covered' if r["covered_by_selected30"]=='True' else ' missed'),f(r["full_fraction"])) for r in c10],"#56B4E9",.35)
    s.text(850,670,"30 technical reference","p");s.text(1170,670,"n=30","p");s.line(990,680,990,735,"#555",3);s.text(850,765,"remove 6 zero-biological-pathway","s");s.text(1170,765,"n=24","p");s.line(990,775,990,830,"#555",3);s.text(850,860,"remove SRR27343296 (extreme sparse)","s");s.text(1170,860,"n=23","p");s.text(850,930,"101 candidates stable across n=30→24→23","s");s.text(850,970,"Selected functional supplement only; no 400-run extrapolation.","n")
    s.finish(figdir/"Figure5.svg")
    def raster5(p,c):
        rr=data["sb"]["classified_fraction"];png_bars(p,c[0],[f(rr["selected_median"]),f(rr["other_median"])],(213,94,0),.05)
        rr=data["sb"]["dominant_species_abundance"];png_bars(p,c[1],[f(rr["selected_median"]),f(rr["other_median"])],(213,94,0),1);png_scatter(p,c[2],pcoa,"selected_deep_review_30")
        png_bars(p,c[3],[f(r["full_fraction"]) for r in c10],(86,180,233),.35);png_bars(p,c[4],[30,24,23],(213,94,0),30)
    generic_png(figdir/"Figure5.png","FIGURE 5 FIXED30 FUNCTION LIMITS",[("A","CLASSIFIED FRACTION"),("B","DOMINANT ABUNDANCE"),("C","PCOA POSITION"),("D","STATE COVERAGE"),("E","HUMANN 30 TO 24 TO 23")],raster5)
    legends.append({"figure":"Figure 5","legend":"The fixed deep-review subset is selected and cannot represent cohort-wide function. (A) Median classified fraction was 0.0459 in the fixed 30 versus 0.0175 in the other 370. (B) Median dominant-species abundance was 0.956 versus 0.390. (C) Fixed-30 samples highlighted in the full-cohort Aitchison PCoA. (D) Coverage of exploratory k=10 states; the subset covered 3 of 4 major states (≥5% prevalence) and missed a state containing 7.5% of all samples. (E) HUMAnN pathway sensitivity: n=30 technical reference, n=24 after excluding six zero-biological-pathway samples, and n=23 after additionally excluding extreme-sparse SRR27343296. The 101 direction- and FDR-stable candidates remain hypothesis-generating only."})
    for x in legends:(figdir/(x["figure"].replace(" ","")+"_legend.md")).write_text(f"# {x['figure']} legend\n\n{x['legend']}\n")
    return legends


def make_tables(root:pathlib.Path,out:pathlib.Path,data:dict):
    td=out/"tables";td.mkdir(parents=True,exist_ok=True);qc=data["qc"]
    rows=[]
    for label,rr in [("Overall",qc)]+[(d,[r for r in qc if r["diagnosis"]==d]) for d in DIAGNOSES]:
        row={"group":label,"N":len(rr)}
        for key,label2 in [("total_reads","total_reads"),("classified_fraction","classified_fraction"),("bracken_assigned_reads_estimate","bracken_assigned_reads"),("observed_species","observed_species"),("shannon","shannon"),("dominant_microbial_species_abundance","dominant_species_abundance")]:
            v=[f(r[key]) for r in rr];row[label2+"_median"]=f"{statistics.median(v):.6g}";row[label2+"_IQR"]=f"{q(v,.25):.6g}–{q(v,.75):.6g}"
        row["QC_flagged_n"]=sum(bool(r["qc_flags"]) for r in rr);row["strict_QC_n"]=sum(r["sensitivity_included"]=="True" for r in rr);rows.append(row)
    write_tsv(td/"Table1_cohort_characteristics.tsv",rows)
    table2=[]
    for r in data["pm"]:
        table2.append({"distance":r["metric"],"cohort":r["sample_set"],"N":r["n"],"PERMANOVA_R2":r["PERMANOVA_R2"],"PERMANOVA_F":r["PERMANOVA_F"],"permutation_P":r["PERMANOVA_p"],"PERMDISP_P":r["PERMDISP_p"],"permutations":r["permutations"],"interpretation":"Primary formal; small association not dispersion-driven" if r["metric"]=="Aitchison" and f(r["PERMDISP_p"])>=.05 else ("Secondary/qualified; dispersion differs" if r["metric"]=="Bray-Curtis" and f(r["PERMDISP_p"])<.05 else "Sensitivity support")})
    write_tsv(td/"Table2_permanova_permdisp.tsv",table2)
    dd={r["species"]:r for r in data["da"]};stable={"Porphyromonas gingivalis","Campylobacter rectus","Fusobacterium nucleatum"};table3=[]
    for name in CANDIDATES:
        r=dd[name];means=json.loads(r["group_CLR_means_json"]);hi=max(means,key=means.get);lo=min(means,key=means.get)
        table3.append({"species":name,"prevalence":r["prevalence"],"epsilon_squared":r["epsilon_squared"],"full_cohort_P":r["cohort_stratified_permutation_p"],"full_cohort_BH_FDR":r["BH_q"],"strict_QC_P":r["QC_sensitivity_cohort_stratified_permutation_p"],"strict_QC_BH_FDR":r["QC_sensitivity_BH_q"],"CLR_direction":f"highest {hi}; lowest {lo}","evidence_class":"full + strict-QC FDR" if name in stable else "full-cohort FDR only"})
    write_tsv(td/"Table3_diagnosis_associated_species.tsv",table3)


def make_manuscript(root:pathlib.Path,out:pathlib.Path,data:dict,legends:list[dict],generated:str):
    md=out/"manuscript";md.mkdir(parents=True,exist_ok=True)
    title="Large-scale BALF shotgun metagenomics reveals modest diagnosis-associated shifts amid substantial inter-individual heterogeneity in respiratory microbial community structure"
    files={
    "01_title_options.md":f"# Title options\n\n## Recommended\n\n{title}\n\n## Alternatives\n\n1. Diagnosis explains modest variation against a heterogeneous BALF metagenomic landscape.\n2. Compositional analysis of 400 BALF shotgun metagenomes identifies modest diagnosis associations and substantial heterogeneity.\n3. Respiratory microbial community variation across 400 BALF shotgun metagenomes: diagnosis associations and limits of selected functional profiling.\n",
    "02_abstract_structured.md":"""# Structured abstract

## Background

Respiratory metagenomic communities are heterogeneous, and statistically significant disease associations need not imply sharply separated or diagnostic community types. We characterized the taxonomic landscape of a published bronchoalveolar lavage fluid (BALF) shotgun metagenomic cohort and tested associations with independently recorded diagnosis.

## Methods

We analyzed frozen Kraken2/Bracken results for 400 unique runs, BioSamples, and patients. Species-level relative abundance was primary and genus level was a sensitivity analysis. Published diagnosis was tested using Aitchison and Bray–Curtis PERMANOVA with 9,999 cohort-stratified permutations, paired with PERMDISP. All samples remained in the primary analysis; 119 samples formed a prespecified strict-QC sensitivity cohort. Differential species analysis reported prevalence, effect size, permutation P, BH FDR, and CLR sensitivity. Clustering and fixed-30 HUMAnN analyses were exploratory.

## Results

Production results were complete for 400/400 analyzable records; two additional mapped published WGS records had size_MB=0. Published diagnosis explained a small fraction of Aitchison variation (R²=0.0194, p=0.0001), without evidence of differential dispersion (PERMDISP p=0.487), and the association persisted in the strict-QC cohort. Bray–Curtis evidence was weaker and dispersion-confounded (R²=0.0153, p=0.0115; PERMDISP p=0.0013). Five species passed full-cohort BH FDR; Porphyromonas gingivalis, Campylobacter rectus, and Fusobacterium nucleatum also passed strict-QC FDR. Cross-metric clustering agreement was approximately zero and did not support stable ecotypes. The fixed 30 had higher median classified fraction (0.0459 versus 0.0175) and dominant-species abundance (0.956 versus 0.390) than the other 370 and had pathway annotation dropout.

## Conclusions

Large-scale BALF metagenomics supports modest diagnosis-associated compositional differences amid substantial inter-individual heterogeneity. Candidate species require external validation; neither exploratory clusters nor the selected functional subset supports diagnostic, causal, or cohort-wide functional claims.
""",
    "03_introduction_outline.md":"""# Introduction outline

1. BALF shotgun metagenomics can resolve respiratory community composition beyond targeted assays, but low microbial signal and marked person-to-person variation complicate interpretation.
2. Published disease comparisons often emphasize significance while under-reporting explained variance, dispersion, compositionality, and sample-quality sensitivity.
3. Data-derived dominant taxa and clusters are useful descriptive summaries but are not independent clinical phenotypes or validated subtypes.
4. Objective: characterize the complete analyzable taxonomy/community landscape, test the independent published-diagnosis association with compositional safeguards, identify limited candidate taxa, and quantify why a selected 30-sample functional review cannot represent the cohort.
5. Prespecified framing: community-level Aitchison inference is primary; species candidates are secondary; Bray–Curtis is qualified; clustering/network and HUMAnN are exploratory.
""",
    "04_methods_draft.md":"""# Methods draft

## Cohort and independent metadata

The source project contained 402 mapped published clinical WGS records. Two records (SRR27343810 and SRR27343463) had size_MB=0 and no reads available, leaving 400 analyzable records. The analysis cohort comprised 400 unique runs, 400 unique BioSamples, and 400 unique patient identifiers. Frozen production Kraken2/Bracken results were complete for all 400. Published diagnosis was obtained from the checked-in clinical mapping and comprised bacterial infection (n=114), fungal infection (n=78), lung cancer (n=122), and pulmonary tuberculosis (n=86). No abundance-derived label was used as an independent phenotype.

## Taxonomic inputs and QC

Species-level Bracken relative abundance was primary; genus-level analysis was sensitivity. Six prespecified background/non-target labels were excluded before microbial community analysis, and the remaining profiles were closed to unit sum. QC flags were: classified fraction <0.5%; Bracken-assigned reads <1,000; observed species ≤2; or robust outlier status (absolute median-absolute-deviation z score >3.5) for log10 total reads, classified fraction, richness, or dominant-species abundance. A total of 281 samples had at least one flag. Flags were annotations, not deletion criteria: the primary cohort remained n=400, while the 119 samples without flags formed the prespecified strict-QC sensitivity cohort. This dual-track design avoided complete-case deletion of a non-random low-information phenotype while testing robustness.

## Diversity and community composition

Observed species, Shannon diversity, Simpson diversity, and Pielou evenness were calculated per sample. Bray–Curtis distances were calculated from relative abundance. For Aitchison analysis, a recorded pseudocount was applied before CLR transformation (see methods/parameters.json). Principal coordinate analysis summarized each distance matrix. Published-diagnosis PERMANOVA used 9,999 permutations constrained within the published cohort field; every PERMANOVA was paired with PERMDISP. Effect size (R²) and dispersion were interpreted before p values. The complete analysis was repeated in the strict-QC cohort.

## Differential species analysis

The frozen species analysis used prevalence ≥10%, effect-size reporting, cohort-stratified permutation p values, BH FDR, and diagnosis-specific CLR means. The strict-QC analysis used the same frozen feature set and parameters. No threshold or group was changed after inspecting results.

## Exploratory structure and selected functional review

Hierarchical community clustering was explored for k=2–10 using Bray–Curtis and Aitchison representations. Silhouette and cross-metric adjusted Rand index were used to evaluate stability; clusters were termed exploratory community states. CLR taxon associations were descriptive and not interpreted as ecological interactions. The fixed 30 deep-review samples were mapped into the 400-sample space and compared descriptively with the other 370. HUMAnN gene-family and pathway results were reviewed only as a selected functional supplement, including pathway annotation-dropout sensitivity at n=30, n=24, and n=23. No functional result was extrapolated to the 400-run cohort.

## Reproducibility

All manuscript values derive from checked-in frozen result tables. Figure source TSVs, table TSVs, legends, consistency checks, input hashes, and parameters accompany the package. The package builder performs no new inferential test.
""",
    "05_results_draft.md":"""# Results draft

## 3.1 Cohort construction and respiratory metagenomic landscape

The analyzable cohort contained 400 unique runs, BioSamples, and patients, with complete frozen Kraken2/Bracken production records. Two additional mapped published WGS records had size_MB=0 and therefore no sequence reads; neither was removed on the basis of an analysis result. Published diagnoses included lung cancer (n=122), bacterial infection (n=114), pulmonary tuberculosis (n=86), and fungal infection (n=78). Low microbial information was common: 281 samples carried at least one prespecified QC flag. These samples were retained in the primary analysis, and the 119 unflagged samples constituted the strict-QC sensitivity cohort.

## 3.2 Published diagnosis explains a small but reproducible fraction of compositional variation

Published diagnosis was associated with Aitchison community composition in the full cohort (PERMANOVA R²=0.0194, F=2.613, p=0.0001). PERMDISP was not significant (p=0.487), arguing against differential within-group dispersion as the explanation for this result. The prespecified strict-QC analysis also supported the association. The effect remained small: diagnosis explained approximately 1.9% of compositional variation, and ordination showed substantial overlap and inter-individual heterogeneity. Bray–Curtis PERMANOVA was also significant (R²=0.0153, F=2.056, p=0.0115), but PERMDISP was significant (p=0.0013); it therefore provides secondary, qualified evidence rather than an unambiguous centroid-shift result.

## 3.3 A limited set of oral-associated taxa shows diagnosis-associated differences

Five species passed full-cohort BH FDR: Parvimonas micra, Porphyromonas endodontalis, Porphyromonas gingivalis, Campylobacter rectus, and Fusobacterium nucleatum. Of these, P. gingivalis, C. rectus, and F. nucleatum also passed BH FDR in the strict-QC cohort. Prevalence was limited and group medians were generally zero; interpretation therefore rests on the combined prevalence, effect-size, raw-distribution, permutation, FDR, and CLR evidence rather than on separated boxplots. These taxa are diagnosis-associated candidates, not biomarkers.

## 3.4 Respiratory microbial communities do not form stable diagnosis-linked ecotypes

Exploratory clustering depended strongly on the distance representation and number of clusters. Bray silhouette reached its maximum at the tested k=10 boundary, while Bray–Aitchison adjusted Rand agreement remained approximately zero across k=2–10. Thus, data-driven community states provide descriptive organization of heterogeneity but do not support stable clinical subtypes or diagnosis-linked ecotypes.

## 3.5 The fixed deep-review subset is strongly enriched and not representative of the full cohort

The fixed 30 samples had a median classified fraction of 0.0459 compared with 0.0175 in the other 370 and a median dominant-species abundance of 0.956 compared with 0.390. They covered three of four k=10 community states representing at least 5% of the cohort and missed one state containing 7.5% of all samples. Their location and taxonomic enrichment demonstrate selection bias rather than a representative miniature cohort.

## 3.6 Functional profiling generates hypotheses but does not support cohort-wide functional inference

The fixed-30 HUMAnN review identified six samples without any biological pathway beyond UNMAPPED/UNINTEGRATED, while SRR27343296 was extremely pathway sparse. Sensitivity therefore compared n=30, n=24 after removing zero-biological-pathway samples, and n=23 after additionally removing SRR27343296. Although 101 pathway candidates retained direction and FDR across all three sets, the selected sampling, annotation dropout, taxonomy-derived grouping, and significant dispersion in functional PERMANOVA restrict these results to supplementary hypothesis generation. They do not support functional inference for the 400-run cohort.
""",
    "06_discussion_outline.md":"""# Discussion outline

1. Lead with scale and restraint: the 400-run BALF analysis detects a reproducible diagnosis association, but diagnosis explains only ~1.9% of compositional variation.
2. Emphasize why Aitchison is primary: compositional geometry, 9,999 permutations, nonsignificant PERMDISP, and strict-QC support.
3. Contrast Bray carefully: a significant PERMANOVA accompanied by significant PERMDISP cannot establish a pure location shift.
4. Discuss five oral-associated candidate taxa as limited secondary evidence; focus on prevalence, zeros, small effects, and three strict-QC-stable findings. Avoid mechanism, diagnostic performance, and causality.
5. Interpret weak cross-metric cluster agreement as evidence of substantial continuous heterogeneity, not failed discovery of hidden disease subtypes.
6. Explain the dual-track QC design: all 400 preserve the intended cohort; n=119 tests low-information sensitivity without outcome-driven deletion.
7. Position fixed-30 HUMAnN as a methods-aware functional supplement. Selection enrichment and annotation dropout preclude cohort-wide claims.
8. Close with the defensible contribution: robust quantification of modest diagnosis association and the limits of subtype and functional overinterpretation in heterogeneous respiratory metagenomes.
""",
    "07_limitations_final.md":"""# Final limitations

1. The study is a reanalysis of published observational BALF shotgun data. Published diagnosis is independent of the microbial matrix, but unmeasured clinical variables, treatment, sampling, host burden, and center effects may confound associations; causality and diagnostic performance cannot be inferred.
2. Microbial information was low or atypical in many samples: 281/400 met at least one prespecified QC flag. They were not excluded. The n=400 primary and n=119 strict-QC sensitivity analyses answer complementary questions, but neither removes possible low-biomass measurement artifacts.
3. Two of 402 mapped published WGS records had size_MB=0, yielding 400 analyzable records. Results apply to this complete available production cohort, not to unavailable records or a broader respiratory population.
4. Species candidates were sparse, with many zeros and generally zero group medians. FDR control and CLR sensitivity reduce but do not eliminate compositional, annotation, and multiple-testing uncertainty; external validation is required.
5. Significant Bray–Curtis PERMDISP limits interpretation of Bray PERMANOVA. Aitchison is therefore the primary formal result, and its R² remains small.
6. Community clusters were unstable across distance representations and remain exploratory community states rather than clinical subtypes.
7. The fixed 30 were selected, enriched for classified and dominant-species signal, incompletely covered community states, and exhibited HUMAnN pathway dropout. Their functional/AMR findings cannot be extrapolated to the 400-sample cohort.
""",
    "08_figure_legends.md":"# Main figure legends\n\n"+"\n\n".join(f"## {x['figure']}\n\n{x['legend']}" for x in legends)+"\n",
    "09_table_titles_footnotes.md":"""# Table titles and footnotes

## Table 1. Cohort characteristics and sequencing/community QC by published diagnosis

Values are N or median (IQR). Only variables present in the frozen cohort/QC tables are shown; no clinical covariate was inferred or manufactured. “QC flagged” denotes at least one prespecified flag and does not mean excluded. The primary cohort is n=400; “strict QC” denotes the unflagged n=119 sensitivity cohort.

## Table 2. Published-diagnosis PERMANOVA and paired PERMDISP results

All tests used 9,999 permutations constrained by the published cohort field. R² is the PERMANOVA effect size. A significant PERMDISP indicates differing within-group dispersion and requires qualified PERMANOVA interpretation. Aitchison/full is the primary formal analysis; Bray–Curtis is secondary/qualified.

## Table 3. Species associated with published diagnosis in the frozen analysis

Prevalence refers to the full 400-run cohort. Effect size is Kruskal–Wallis epsilon-squared. P values are cohort-stratified permutation values and FDR uses Benjamini–Hochberg correction. CLR direction identifies diagnoses with the highest and lowest group CLR means. “Full + strict-QC FDR” is sensitivity-supported; “full-cohort FDR only” is not.
""",
    "11_journal_positioning.md":"""# Journal positioning by scientific scope

## A. Optimistic

A broad microbiome or respiratory translational journal that values a comparatively large public BALF shotgun cohort, explicit compositional validation, effect-size restraint, and a negative result on stable ecotypes. The pitch is methodological rigor plus cohort scale—not biomarkers or mechanistic novelty.

## B. Realistic

A respiratory microbiology, clinical metagenomics, infectious-disease microbiome, or data-reanalysis journal receptive to robust observational community analysis. This is the best fit for the modest diagnosis R², limited candidate taxa, and carefully bounded selected functional supplement.

## C. Safe

A sound-science, microbial ecology methods/application, or open data-analysis journal that prioritizes reproducibility and technically defensible reuse of public sequencing data over strong mechanistic claims.

No impact factors or current rankings were queried. Final journal selection should be based on scope, article type, data-reanalysis policy, and tolerance for observational public-data studies.
"""}
    for name,text in files.items():(md/name).write_text(text.rstrip()+"\n",encoding="utf-8")
    # Claims matrix
    pm={(r["metric"],r["sample_set"]):r for r in data["pm"]}; claims=[]
    claims.append({"claim":"Published diagnosis is associated with modest Aitchison compositional differences","analysis":"Aitchison PERMANOVA + PERMDISP","N":400,"effect_size":pm[("Aitchison","full")]["PERMANOVA_R2"],"P":pm[("Aitchison","full")]["PERMANOVA_p"],"FDR":"NA","sensitivity_supported":"yes; n=119","dispersion_issue":"no; PERMDISP p=0.487","evidence_class":"Primary formal","allowed_wording":"associated with; modest compositional differences","forbidden_wording":"caused; drives; diagnostic signature"})
    claims.append({"claim":"Bray-Curtis composition differs by diagnosis but dispersion also differs","analysis":"Bray-Curtis PERMANOVA + PERMDISP","N":400,"effect_size":pm[("Bray-Curtis","full")]["PERMANOVA_R2"],"P":pm[("Bray-Curtis","full")]["PERMANOVA_p"],"FDR":"NA","sensitivity_supported":"qualified","dispersion_issue":"yes; PERMDISP p=0.0013","evidence_class":"Secondary/qualified","allowed_wording":"qualified association; dispersion differs","forbidden_wording":"unambiguous centroid separation; distinct subtype"})
    dd={r["species"]:r for r in data["da"]};stable={"Porphyromonas gingivalis","Campylobacter rectus","Fusobacterium nucleatum"}
    for name in CANDIDATES:
        r=dd[name];claims.append({"claim":name+" is a diagnosis-associated candidate taxon","analysis":"frozen prevalence-filtered species differential + CLR sensitivity","N":400,"effect_size":r["epsilon_squared"],"P":r["cohort_stratified_permutation_p"],"FDR":r["BH_q"],"sensitivity_supported":"yes" if name in stable else "no; full-cohort only","dispersion_issue":"not a PERMANOVA claim","evidence_class":"Secondary formal" if name in stable else "Secondary formal; not strict-QC stable","allowed_wording":"associated with; candidate taxon","forbidden_wording":"biomarker; diagnostic signature; caused; drives"})
    claims += [
    {"claim":"No stable diagnosis-linked ecotype was identified","analysis":"hierarchical clustering k=2–10; silhouette; cross-metric ARI","N":400,"effect_size":"ARI approximately zero","P":"NA","FDR":"NA","sensitivity_supported":"cross-metric check failed stability","dispersion_issue":"NA","evidence_class":"Exploratory/negative","allowed_wording":"metric-dependent community states; substantial heterogeneity","forbidden_wording":"distinct microbiome subtype; stable clinical subtype"},
    {"claim":"The fixed 30 are enriched for classified microbial signal","analysis":"prespecified selection-bias comparison","N":"30 vs 370","effect_size":"median 0.0459 vs 0.0175","P":data["sb"]["classified_fraction"]["mann_whitney_p"],"FDR":"NA","sensitivity_supported":"supported by dominance and state coverage","dispersion_issue":"NA","evidence_class":"Descriptive selection-bias","allowed_wording":"selected; enriched; not representative","forbidden_wording":"representative functional cohort"},
    {"claim":"The fixed 30 are enriched for dominant-species abundance","analysis":"prespecified selection-bias comparison","N":"30 vs 370","effect_size":"median 0.956 vs 0.390","P":data["sb"]["dominant_species_abundance"]["mann_whitney_p"],"FDR":"NA","sensitivity_supported":"supported by classified fraction and state coverage","dispersion_issue":"NA","evidence_class":"Descriptive selection-bias","allowed_wording":"selected; enriched; not representative","forbidden_wording":"pathogen-specific functional state"},
    {"claim":"HUMAnN candidates are hypothesis-generating only","analysis":"fixed-30 n=30→24→23 annotation-dropout review","N":"30/24/23","effect_size":"101 stable pathway candidates","P":"see supplement","FDR":"see supplement","sensitivity_supported":"direction and FDR across three sets","dispersion_issue":"functional PERMANOVA dispersion significant","evidence_class":"Supplementary exploratory","allowed_wording":"exploratory; selected functional supplement","forbidden_wording":"functional reprogramming; cohort-wide functional landscape; pathogen-specific functional state"}]
    write_tsv(md/"10_claims_matrix.tsv",claims)
    (md/"12_writing_guardrails.md").write_text("# Writing guardrails\n\nAllowed: associated with; modest compositional differences; exploratory; candidate taxa; substantial heterogeneity.\n\nForbidden: caused; drives; biomarker; diagnostic signature; distinct microbiome subtype; functional reprogramming; pathogen-specific functional state.\n",encoding="utf-8")


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=pathlib.Path,default=pathlib.Path("reports_public/metagenome_400_formal"));args=ap.parse_args();root=args.root;out=root/"publication_package";generated=datetime.now(timezone.utc).isoformat(timespec="seconds")
    data=gate(root)
    out.mkdir(parents=True,exist_ok=True)
    write_tsv(out/"consistency_audit.tsv",data["checks"])
    legends=make_figures(root,out,data);make_tables(root,out,data);make_manuscript(root,root,data,legends,generated)
    frozen_inputs = [
        "summary.md", "summary.json", "methods/article_strategy.md", "methods/parameters.json",
        "tables/article_findings.tsv", "statistics/permanova_permdisp.tsv",
        "associations/diagnosis_species_differential.tsv", "qc/cohort_qc.tsv",
        "audit/cohort_audit.tsv", "audit/data_availability.json",
        "taxonomy/species_relative_abundance.tsv.gz", "taxonomy/species_landscape.tsv",
        "beta/aitchison_pcoa.tsv", "clustering/cluster_diagnostics.tsv",
        "clustering/sample_community_states.tsv", "integration_30/selection_bias_metrics.tsv",
        "integration_30/community_state_coverage_k2_k10.tsv",
        "integration_30/humann_publication_review/summary.json",
        "integration_30/humann_publication_review/summary.md", "limitations.md",
    ]
    write_tsv(out/"frozen_input_manifest.tsv", [{"path":x,"bytes":(root/x).stat().st_size,"sha256":sha(root/x)} for x in frozen_inputs])
    (out/"supplementary_index.md").write_text("""# Supplementary material index

- Complete species differential table: `../associations/diagnosis_species_differential.tsv`
- Complete genus sensitivity differential table: `../associations/diagnosis_genus_differential.tsv`
- Sample-level QC flags and strict-QC membership: `../qc/cohort_qc.tsv`
- Cluster diagnostics and assignments: `../clustering/cluster_diagnostics.tsv`, `../clustering/sample_community_states.tsv`
- Fixed-30 selection bias and state coverage: `../integration_30/selection_bias_metrics.tsv`, `../integration_30/community_state_coverage_k2_k10.tsv`
- HUMAnN n=30→24→23 publication review and manifest: `../integration_30/humann_publication_review/`
- Full reproducibility parameters: `../methods/parameters.json`, `../methods/manifest.tsv`

These are frozen supporting outputs. The publication package adds formatting and figures but no new inferential analysis.
""", encoding="utf-8")
    manifest=[]
    for path in sorted(list(out.rglob("*")) + list((root/"manuscript").rglob("*"))):
        if path.is_file() and path.name!="manifest.tsv":manifest.append({"path":str(path.relative_to(root)),"bytes":path.stat().st_size,"sha256":sha(path)})
    write_tsv(out/"manifest.tsv",manifest)
    summary={"generated_at_utc":generated,"manuscript_ready":True,"consistency_gate":"PASS","cohort":400,"qc_flagged_retained":281,"strict_qc_sensitivity":119,"main_figures":5,"main_tables":3,"recommended_title":"Large-scale BALF shotgun metagenomics reveals modest diagnosis-associated shifts amid substantial inter-individual heterogeneity in respiratory microbial community structure","additional_analysis_scientifically_necessary":False,"blocking_issues":[]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    (out/"summary.md").write_text("# Publication package status\n\n- Manuscript-ready: **YES**\n- Consistency gate: **PASS**\n- Blocking issues: none\n- Frozen cohort: 400; QC-flagged retained: 281; strict-QC sensitivity: 119\n- Main figures: 5 (SVG, PNG, source TSV, legend)\n- Main tables: 3\n- Additional analysis scientifically necessary: **No**\n\nNo new inferential method, grouping, threshold, taxonomy rerun, or functional expansion was introduced.\n")
    print(out);return 0


if __name__=="__main__":raise SystemExit(main())
