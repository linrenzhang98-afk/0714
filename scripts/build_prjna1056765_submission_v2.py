#!/usr/bin/env python3
"""Build publication figures and supplements from frozen PRJNA1056765 outputs.

This script performs formatting and consistency checks only. It contains no
inferential procedure and does not alter the frozen v5 grid.
"""
from __future__ import annotations

import csv, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_prjna1056765_publication_package import SVG, PNG, read_tsv, write_tsv

OUT = ROOT / "reports_public/prjna1056765_submission_v2"
FIG = OUT / "figures"
SRC = FIG / "source_data"
SUP = OUT / "supplement"

BLUE = "#0072B2"; ORANGE = "#D55E00"; GREEN = "#009E73"; PURPLE = "#CC79A7"
GREY = "#6B7280"; LIGHT = "#E5E7EB"; DARK = "#1F2937"; RED = "#B91C1C"

def rows(path): return read_tsv(ROOT / path)
def num(x): return float(x)
def save_svg(s, name):
    path = FIG / f"{name}.svg"; s.finish(path); return path

def png_canvas(name, title, draw, w=2400, h=1600):
    p=PNG(w,h); p.text(70,45,title,5); draw(p); p.save(FIG/f"{name}.png")

def fig1(cohort):
    counts={}
    for r in cohort: counts[r["diagnosis"]]=counts.get(r["diagnosis"],0)+1
    source=[{"population":"Published source cohort","group":"All","n":402},
            {"population":"Unavailable records","group":"All","n":2},
            {"population":"Han ecology/training","group":"All","n":284},
            {"population":"Han internal test","group":"All","n":118},
            {"population":"Current primary","group":"All","n":400}]
    source += [{"population":"Current primary","group":k,"n":v} for k,v in counts.items()]
    qc=rows("reports_public/metagenome_400_formal/qc/cohort_qc.tsv")
    sens={}
    for r in qc:
        if r["sensitivity_included"]=="True": sens[r["diagnosis"]]=sens.get(r["diagnosis"],0)+1
    source += [{"population":"Pipeline-dependent sensitivity","group":"All","n":119}]
    source += [{"population":"Pipeline-dependent sensitivity","group":k,"n":v} for k,v in sens.items()]
    write_tsv(SRC/"Figure1_source.tsv",source,["population","group","n"])
    s=SVG("Cohort provenance and analytical design",1800,1050)
    s.text(55,90,"A","p"); s.text(95,90,"Source cohort and analytical populations","s")
    # compact flow
    s.rect(90,130,360,82,"#F3F4F6",DARK); s.text(270,162,"PRJNA1056765","p","middle"); s.text(270,190,"published cohort, n=402","s","middle")
    s.line(270,212,270,270,DARK,2); s.text(300,248,"2 records unavailable","n")
    s.rect(90,270,360,82,"#E8F1F8",BLUE); s.text(270,302,"400 downloadable DNA runs","p","middle"); s.text(270,330,"current source population","s","middle")
    s.line(270,352,270,420,DARK,2); s.line(270,420,720,420,DARK,2); s.line(270,420,270,480,DARK,2); s.line(720,420,720,480,DARK,2)
    s.rect(70,480,400,92,"#E8F1F8",BLUE); s.text(270,514,"Primary analytical population","p","middle"); s.text(270,544,"n=400; four-level omnibus","s","middle")
    s.rect(520,480,400,92,"#F3F4F6",GREY); s.text(720,514,"Pipeline-dependent sensitivity","p","middle"); s.text(720,544,"population, n=119","s","middle")
    s.text(1080,90,"B","p"); s.text(1120,90,"Published and current estimands","s")
    s.text(1110,150,"Han et al.","p"); s.line(1110,168,1660,168,LIGHT,2)
    s.text(1130,210,"Ecology / training","s"); s.text(1610,210,"n=284","p","end")
    s.text(1130,260,"Internal test","s"); s.text(1610,260,"n=118","p","end")
    s.text(1110,340,"Current study","p"); s.line(1110,358,1660,358,LIGHT,2)
    s.text(1130,400,"Primary four-level omnibus","s"); s.text(1610,400,"n=400","p","end")
    s.text(1130,450,"Sensitivity estimand","s"); s.text(1610,450,"n=119","p","end")
    s.text(55,660,"C","p"); s.text(95,660,"Diagnosis composition","s")
    colors={"Bacterial infection":BLUE,"Fungal infection":GREEN,"Lung cancer":ORANGE,"Pulmonary tuberculosis":PURPLE}
    order=list(colors)
    for i,(label,d) in enumerate([("Primary analytical population",counts),("Pipeline-dependent sensitivity population",sens)]):
        y=730+i*130; s.text(70,y,label,"s"); x=520; total=sum(d.values()); width=1100
        for g in order:
            w=width*d[g]/total; s.rect(x,y-24,w,38,colors[g]);
            if w>90: s.text(x+w/2,y+2,str(d[g]),"s","middle")
            x+=w
    x=80
    for g in order: s.rect(x,980,20,20,colors[g]); s.text(x+28,996,g,"n"); x+=390
    save_svg(s,"Figure1")
    def draw(p):
        p.rect(120,180,520,120,(232,241,248)); p.text(190,215,"PRJNA1056765 N=402",4); p.line(380,300,380,390); p.rect(120,390,520,120,(232,241,248)); p.text(190,425,"400 DOWNLOADABLE DNA RUNS",3)
        p.rect(120,620,520,110,(232,241,248)); p.text(180,655,"PRIMARY N=400",4); p.rect(760,620,620,110,(243,244,246)); p.text(810,655,"SENSITIVITY POPULATION N=119",3)
        cols=[(0,114,178),(0,158,115),(213,94,0),(204,121,167)]
        for j,d in enumerate((counts,sens)):
            x=180; y=1050+j*160; total=sum(d.values())
            for g,c in zip(order,cols):
                w=int(1900*d[g]/total); p.rect(x,y,w,70,c); x+=w
    png_canvas("Figure1","FIGURE 1  COHORT PROVENANCE AND ANALYTICAL DESIGN",draw)

def effect_figure(name, metric, title):
    grid=[r for r in rows("reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv") if r["metric"]==metric]
    if metric=="Aitchison": grid=[r for r in grid]
    write_tsv(SRC/f"{name}_source.tsv",grid,list(grid[0]))
    xmax=.085 if metric=="Bray-Curtis" else .075
    s=SVG(title,1800,1100)
    for pi,(pop,n,label) in enumerate([("full",400,"Primary analytical population"),("strict_QC",119,"Pipeline-dependent sensitivity population")]):
        x0=80+pi*870; s.text(x0,95,chr(65+pi),"p"); s.text(x0+42,95,f"{label} (n={n})","s")
        s.line(x0+270,165,x0+780,165,DARK,1)
        for t in range(0,9):
            val=xmax*t/8; xx=x0+270+510*t/8; s.line(xx,160,xx,910,LIGHT,1); s.text(xx,940,f"{val:.3f}","n","middle")
        s.text(x0+525,985,"PERMANOVA R²","s","middle")
        rr=[r for r in grid if r["population"]==pop]
        if metric=="Aitchison": rr=sorted(rr,key=lambda r:(num(r["prevalence_threshold"]),r["pseudocount_rule"]))
        else: rr=sorted(rr,key=lambda r:num(r["prevalence_threshold"]))
        for i,r in enumerate(rr):
            y=225+i*(105 if metric=="Aitchison" else 185); prev=int(num(r["prevalence_threshold"])*100); feat=r["retained_features"]
            if metric=="Aitchison": rule="P1" if r["pseudocount_rule"].startswith("P1") else "P2"; label=f"{prev}% / {feat} species  {rule}"
            else: label=f"{prev}% / {feat} species"
            s.text(x0+250,y+6,label,"n","end"); xx=x0+270+510*num(r["permanova_R2"])/xmax
            fill=BLUE if (metric!="Aitchison" or r["pseudocount_rule"].startswith("P1")) else ORANGE
            if metric=="Aitchison" and r["pseudocount_rule"].startswith("P2"):
                s.rect(xx-7,y-7,14,14,fill,DARK)
            else: s.circle(xx,y,8,fill,1,DARK)
            if r["is_anchor_replay"]=="True": s.text(xx+14,y-12,"anchor","n")
            if num(r["permdisp_p"])<.05: s.text(x0+790,y+6,"†","p","middle",RED)
            s.text(x0+250,y+31,f"R²={num(r['permanova_R2']):.4f}; PERMDISP P={num(r['permdisp_p']):.4g}","n","end")
        s.text(x0+270,1035,"† differential dispersion (P<0.05)","n")
    save_svg(s,name)
    def draw(p):
        for pi,(pop,n) in enumerate([("full",400),("strict_QC",119)]):
            x0=120+pi*1150; p.text(x0,160,("PRIMARY N=400" if pi==0 else "SENSITIVITY POPULATION N=119"),4)
            rr=sorted([r for r in grid if r["population"]==pop],key=lambda r:(num(r["prevalence_threshold"]),r["pseudocount_rule"]))
            for i,r in enumerate(rr):
                y=310+i*(150 if metric=="Aitchison" else 260); p.line(x0+380,y,x0+1000,y,(220,220,220)); xx=x0+380+int(620*num(r["permanova_R2"])/xmax); p.circle(xx,y,12,(0,114,178) if r.get("pseudocount_rule","").startswith("P1") else (213,94,0)); p.text(x0,y-12,f"{int(num(r['prevalence_threshold'])*100)}% {r['retained_features']} SPECIES",3)
    png_canvas(name,title.upper(),draw)

def fig3():
    d=rows("reports_public/metagenome_400_formal/clustering/cluster_diagnostics.tsv")
    write_tsv(SRC/"Figure3_source.tsv",d,list(d[0]))
    s=SVG("Community heterogeneity and cluster instability",1800,900)
    for pi,(title,key,ymin,ymax) in enumerate([("Silhouette across candidate k","silhouette",.35,.54),("Agreement between representations","ari",-.012,.012)]):
        x0=80+pi*870; s.text(x0,95,chr(65+pi),"p"); s.text(x0+45,95,title,"s"); xL=x0+100; xR=x0+790; yT=160; yB=720
        s.line(xL,yB,xR,yB,DARK); s.line(xL,yT,xL,yB,DARK)
        for k in range(2,11): s.text(xL+(k-2)*(xR-xL)/8,yB+32,k,"n","middle")
        for j in range(5):
            v=ymin+(ymax-ymin)*j/4; yy=yB-(yB-yT)*j/4; s.line(xL,yy,xR,yy,LIGHT); s.text(xL-15,yy+5,f"{v:.2f}" if pi==0 else f"{v:.3f}","n","end")
        if pi==0:
            for key,color,label in [("bray_silhouette",BLUE,"Bray–Curtis"),("aitchison_silhouette",ORANGE,"Aitchison")]:
                pts=[]
                for r in d:
                    xx=xL+(int(r["k"])-2)*(xR-xL)/8; yy=yB-(num(r[key])-ymin)/(ymax-ymin)*(yB-yT); pts.append((xx,yy)); s.circle(xx,yy,6,color,1)
                for a,b in zip(pts,pts[1:]): s.line(*a,*b,color,2)
            s.rect(x0+500,115,18,18,BLUE); s.text(x0+526,130,"Bray–Curtis","n"); s.rect(x0+630,115,18,18,ORANGE); s.text(x0+656,130,"Aitchison","n")
            s.text(xR-5,yT+25,"maximum at tested boundary","n","end")
        else:
            s.line(xL,yB-(0-ymin)/(ymax-ymin)*(yB-yT),xR,yB-(0-ymin)/(ymax-ymin)*(yB-yT),GREY,2,"5,5")
            pts=[]
            for r in d:
                xx=xL+(int(r["k"])-2)*(xR-xL)/8; yy=yB-(num(r["bray_aitchison_adjusted_rand"])-ymin)/(ymax-ymin)*(yB-yT); pts.append((xx,yy)); s.circle(xx,yy,6,GREEN,1)
            for a,b in zip(pts,pts[1:]): s.line(*a,*b,GREEN,2)
        s.text((xL+xR)/2,780,"Number of clusters (k)","s","middle")
    save_svg(s,"Figure3")
    def draw(p):
        for pi in range(2):
            x=140+pi*1160; p.line(x,1320,x+950,1320); p.line(x,240,x,1320)
            if pi==0:
                for key,c in [("bray_silhouette",(0,114,178)),("aitchison_silhouette",(213,94,0))]:
                    pts=[]
                    for r in d: pts.append((x+(int(r['k'])-2)*118,1320-int((num(r[key])-.35)/.19*1000)))
                    for a,b in zip(pts,pts[1:]): p.line(*a,*b,c,4)
                    for xx,yy in pts:p.circle(xx,yy,10,c)
            else:
                pts=[]
                for r in d: pts.append((x+(int(r['k'])-2)*118,780-int(num(r['bray_aitchison_adjusted_rand'])/.012*500)))
                for a,b in zip(pts,pts[1:]):p.line(*a,*b,(0,158,115),4)
                for xx,yy in pts:p.circle(xx,yy,10,(0,158,115))
    png_canvas("Figure3","FIGURE 3  COMMUNITY HETEROGENEITY AND CLUSTER INSTABILITY",draw)

def main():
    for p in (OUT,FIG,SRC,SUP,SUP/"tables"): p.mkdir(parents=True,exist_ok=True)
    cohort=rows("reports_public/metagenome_400_formal/audit/cohort_audit.tsv")
    fig1(cohort); effect_figure("Figure2","Aitchison","Prespecified compositional robustness"); fig3(); effect_figure("FigureS1","Bray-Curtis","Bray–Curtis and dispersion comparator")
    copies={
      "TableS1_complete_frozen_v5_grid.tsv":"reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv",
      "TableS2_QC_population.tsv":"reports_public/metagenome_400_formal/qc/cohort_qc.tsv",
      "TableS3_pipeline_difference_matrix.tsv":"pipeline_difference_matrix.tsv",
      "TableS4_frozen_primary_PERMANOVA_PERMDISP.tsv":"reports_public/metagenome_400_formal/statistics/permanova_permdisp.tsv",
      "TableS5_frozen_species_associations.tsv":"reports_public/metagenome_400_formal/associations/diagnosis_species_differential.tsv",
      "TableS6_clustering_diagnostics.tsv":"reports_public/metagenome_400_formal/clustering/cluster_diagnostics.tsv"}
    for dst,src in copies.items(): (SUP/"tables"/dst).write_bytes((ROOT/src).read_bytes())
    manifest=[]
    for p in sorted(FIG.rglob("*")):
        if p.is_file(): manifest.append({"file":str(p.relative_to(OUT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size,"role":"vector/raster figure" if p.parent==FIG else "figure source data"})
    write_tsv(OUT/"figure_source_manifest.tsv",manifest,["file","sha256","bytes","role"])
    # csv defaults to CRLF; repository text artifacts use LF for clean diffs.
    for p in OUT.rglob("*.tsv"):
        p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
    checks={"status":"PASS","frozen_grid_rows":len(rows("reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv")),"cohort_n":len(cohort),"sensitivity_n":sum(r["sensitivity_included"]=="True" for r in rows("reports_public/metagenome_400_formal/qc/cohort_qc.tsv")),"figures":["Figure1","Figure2","Figure3","FigureS1"],"figure4_decision":"Supplement only; frozen taxon results do not justify an additional main figure","new_statistics":False}
    (OUT/"consistency_report_v2.json").write_text(json.dumps(checks,indent=2)+"\n")

if __name__=="__main__": main()
