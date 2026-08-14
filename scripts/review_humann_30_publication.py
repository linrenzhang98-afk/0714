#!/usr/bin/env python3
"""Publication-grade sensitivity review of the selected fixed-30 HUMAnN results."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

from analyze_prjna1056765_metagenome_400 import (
    bh, distance_matrix, gower, kruskal, pcoa, permanova, permdisp,
    ranks, read_tsv, svg_scatter, write_tsv,
)

SPECIAL={"UNMAPPED","UNINTEGRATED"}


def matrix_header(path:Path)->list[str]:
    with gzip.open(path,"rt",encoding="utf-8",newline="") as h:return next(csv.reader(h,delimiter="\t"))[1:]


def load_normalized(path:Path,minimum_prevalence:int)->tuple[list[str],list[str],list[list[float]]]:
    samples=matrix_header(path);den=[0.0]*len(samples);kept=[]
    with gzip.open(path,"rt",encoding="utf-8",newline="") as h:
        reader=csv.reader(h,delimiter="\t");next(reader)
        for row in reader:
            values=[float(x or 0) for x in row[1:]]
            if row[0] not in SPECIAL:
                for i,v in enumerate(values):den[i]+=v
                if sum(v>0 for v in values)>=minimum_prevalence:kept.append((row[0],values))
    features=[x[0] for x in kept];data=[[kept[j][1][i]/den[i] if den[i]>0 else 0.0 for j in range(len(kept))] for i in range(len(samples))]
    return samples,features,data


def spearman(a:list[float],b:list[float])->float:
    ra,rb=ranks(a),ranks(b);ma,mb=statistics.mean(ra),statistics.mean(rb);num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb));den=math.sqrt(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb));return num/den if den else 0


def betacf(a:float,b:float,x:float)->float:
    qab=a+b;qap=a+1;qam=a-1;c=1.0;d=1-qab*x/qap;d=1e-300 if abs(d)<1e-300 else d;d=1/d;h=d
    for m in range(1,500):
        m2=2*m;aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1+aa*d;d=1e-300 if abs(d)<1e-300 else d;c=1+aa/c;c=1e-300 if abs(c)<1e-300 else c;d=1/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1+aa*d;d=1e-300 if abs(d)<1e-300 else d;c=1+aa/c;c=1e-300 if abs(c)<1e-300 else c;d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<3e-14:break
    return h


def betai(a:float,b:float,x:float)->float:
    if x<=0:return 0.0
    if x>=1:return 1.0
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log(1-x))
    return bt*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*betacf(b,a,1-x)/b


def correlation_p(r:float,n:int)->float:
    if n<3:return 1.0
    x=(n-2)/(n-2+(r*r*(n-2)/(max(1-r*r,1e-15))))
    return betai((n-2)/2,.5,x)


def feature_kw(features:list[str],data:list[list[float]],labels:list[str])->list[dict[str,object]]:
    rows=[]
    for j,f in enumerate(features):
        values=[x[j] for x in data];h,p,e=kruskal(values,labels);means={g:statistics.mean(v for v,x in zip(values,labels) if x==g) for g in sorted(set(labels))};rows.append({"feature":f,"H":h,"p_value":p,"effect":e,"top_group":max(means,key=means.get),"mean_range":max(means.values())-min(means.values()),"means":json.dumps(means,sort_keys=True)})
    bh(rows);rows.sort(key=lambda x:(x["q_value"],-x["effect"]));return rows


def inference(name:str,samples:list[str],data:list[list[float]],labels:list[str],permutations:int,seed:int)->tuple[list[list[float]],list[object]]:
    dist=distance_matrix(data,"bray");coords,explained,b=pcoa(dist);pa=permanova(b,labels,None,permutations,seed);pd=permdisp(dist,labels,None,permutations,seed+1)
    row=[name,len(samples),len(data[0]) if data else 0,len(set(labels)),pa["pseudo_F"],pa["R2"],pa["p_value"],pd["F"],pd["R2"],pd["p_value"],permutations,*explained[:2]]
    return coords,row


def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--joined",type=Path,default=Path("reports_public/metagenome_humann_30_downstream/joined"));p.add_argument("--status",type=Path,default=Path("reports_public/metagenome_functional_profile/run_status.tsv"));p.add_argument("--species-matrix",type=Path,default=Path("reports_public/metagenome_standard_shotgun/species_relative_abundance_matrix.tsv"));p.add_argument("--sample-qc",type=Path,default=Path("reports_public/metagenome_humann_30_downstream/qc/sample_qc.tsv"));p.add_argument("--out",type=Path,default=Path("reports_public/metagenome_400_formal/integration_30/humann_publication_review"));p.add_argument("--permutations",type=int,default=9999);args=p.parse_args()
    status=read_tsv(args.status);groups={r["run"]:r["pathogen_group"] for r in status};sample_qc={r["run"]:r for r in read_tsv(args.sample_qc)};args.out.mkdir(parents=True,exist_ok=True)
    inference_rows=[];gene_main=None;gene_features=None;gene_samples=None
    for fraction,minimum in ((.1,3),(.2,6),(.3,9)):
        samples,features,data=load_normalized(args.joined/"genefamilies_unstratified.tsv.gz",minimum);labels=[groups[s] for s in samples];coords,row=inference(f"gene_family_prevalence_{int(fraction*100)}pct",samples,data,labels,args.permutations,1000+minimum);inference_rows.append(row)
        write_tsv(args.out/f"gene_family/pcoa_prevalence_{int(fraction*100)}pct.tsv",([samples[i],labels[i],*coords[i]] for i in range(30)),["run","pathogen_group",*[f"PCoA{k}" for k in range(1,6)]])
        if minimum==6:gene_main=(data,labels,coords);gene_features=features;gene_samples=samples
    assert gene_main and gene_features and gene_samples
    gene_kw=feature_kw(gene_features,gene_main[0],gene_main[1]);write_tsv(args.out/"gene_family/pathogen_group_exploration.tsv",([x["feature"],x["H"],x["effect"],x["mean_range"],x["top_group"],x["p_value"],x["q_value"],x["means"]] for x in gene_kw),["UniRef90","kruskal_H","epsilon_squared","group_mean_range","highest_mean_group","raw_p","BH_q","group_means_json"])
    svg_scatter(args.out/"figures/gene_family_pcoa.svg",gene_main[2],gene_main[1],"Selected 30: UniRef90 Bray-Curtis PCoA (prevalence ≥20%)")
    # Existing taxonomy fractions supply abundance-derived pathogen burden; association remains exploratory.
    sp=read_tsv(args.species_matrix);smap={r["run"]:r for r in sp};columns=[c for c in sp[0] if c not in ("run","pathogen_group")];aliases={"Enterobacterales":("escherichia","klebsiella","enterobacter","serratia","citrobacter"),"Mycobacteria":("mycobacter",),"Haemophilus":("haemophilus",)};assoc=[]
    for group in sorted(set(gene_main[1])):
        terms=aliases.get(group,(group.lower(),));matches=[c for c in columns if any(t in c.lower() for t in terms)];burden=[sum(float(smap[s].get(c,0) or 0) for c in matches) for s in gene_samples];part=[]
        for j,f in enumerate(gene_features):
            rho=spearman(burden,[row[j] for row in gene_main[0]]);part.append({"group":group,"feature":f,"rho":rho,"p_value":correlation_p(rho,30),"matches":";".join(matches)})
        bh(part);assoc.extend(part)
    write_tsv(args.out/"gene_family/pathogen_abundance_associations.tsv",([x["group"],x["feature"],x["rho"],x["p_value"],x["q_value"],x["matches"]] for x in assoc),["pathogen_group","UniRef90","spearman_rho","raw_p","BH_q_within_pathogen","matched_species_features"])
    # MetaCyc dropout sets: technical n=30, biological n=24, and n=23 excluding extreme sparse SRR27343296.
    samples,pathfeatures,pathdata=load_normalized(args.joined/"pathabundance_unstratified.tsv.gz",6);bio_counts={s:int(sample_qc[s]["pathabundance_detected"]) for s in samples};zero=[s for s in samples if bio_counts[s]==0];sparse="SRR27343296"
    sets={"technical_n30":samples,"biological_n24":[s for s in samples if s not in zero],"biological_nonextreme_n23":[s for s in samples if s not in zero and s!=sparse]};path_results={};pcoa_sets={}
    for idx,(name,members) in enumerate(sets.items()):
        ids=[samples.index(s) for s in members];data=[pathdata[i] for i in ids];labels=[groups[s] for s in members];coords,row=inference(name,members,data,labels,args.permutations,3000+idx);inference_rows.append(row);results=feature_kw(pathfeatures,data,labels);path_results[name]=results;pcoa_sets[name]=(members,labels,coords)
        write_tsv(args.out/f"pathway/{name}_group_exploration.tsv",([x["feature"],x["H"],x["effect"],x["mean_range"],x["top_group"],x["p_value"],x["q_value"],x["means"]] for x in results),["MetaCyc_pathway","kruskal_H","epsilon_squared","group_mean_range","highest_mean_group","raw_p","BH_q","group_means_json"])
        write_tsv(args.out/f"pathway/{name}_pcoa.tsv",([members[i],labels[i],*coords[i]] for i in range(len(members))),["run","pathogen_group",*[f"PCoA{k}" for k in range(1,6)]])
    # Candidate stability is evaluated without changing the fixed feature set.
    maps={name:{x["feature"]:x for x in rows} for name,rows in path_results.items()};stability=[]
    for f in pathfeatures:
        r30,r24,r23=(maps[x][f] for x in sets);stable=(r30["top_group"]==r24["top_group"]==r23["top_group"] and float(r23["q_value"])<.05);stability.append([f,r30["q_value"],r24["q_value"],r23["q_value"],r30["effect"],r24["effect"],r23["effect"],r30["top_group"],r24["top_group"],r23["top_group"],stable])
    write_tsv(args.out/"pathway/annotation_dropout_stability.tsv",stability,["MetaCyc_pathway","n30_BH_q","n24_BH_q","n23_BH_q","n30_effect","n24_effect","n23_effect","n30_top_group","n24_top_group","n23_top_group","stable_direction_and_n23_FDR"])
    svg_scatter(args.out/"figures/pathway_pcoa_n30.svg",pcoa_sets["technical_n30"][2],pcoa_sets["technical_n30"][1],"Selected 30: MetaCyc technical-reference PCoA")
    svg_scatter(args.out/"figures/pathway_pcoa_n23.svg",pcoa_sets["biological_nonextreme_n23"][2],pcoa_sets["biological_nonextreme_n23"][1],"Selected 23: MetaCyc annotation-detectable non-extreme PCoA")
    write_tsv(args.out/"statistics/permanova_permdisp.tsv",inference_rows,["analysis","n","features","groups","PERMANOVA_F","PERMANOVA_R2","PERMANOVA_p","PERMDISP_F","PERMDISP_R2","PERMDISP_p","permutations","PCoA1_fraction_gower_trace","PCoA2_fraction_gower_trace"])
    write_tsv(args.out/"pathway/annotation_dropout_samples.tsv",([s,groups[s],bio_counts[s],"zero_biological_pathway" if s in zero else ("extreme_sparse" if s==sparse else "retained_n23")] for s in samples),["run","pathogen_group","biological_pathways_detected","annotation_status"])
    stable_count=sum(bool(x[-1]) for x in stability);gene_sig=sum(float(x["q_value"])<.05 for x in gene_kw);assoc_sig=sum(float(x["q_value"])<.05 for x in assoc)
    summary={"scope":"selected_deep_review_functional_exploration_only","gene_family_samples":30,"gene_family_primary_prevalence":"20% (6/30)","gene_family_features":len(gene_features),"gene_group_FDR_lt_0.05":gene_sig,"pathogen_gene_associations_FDR_lt_0.05":assoc_sig,"pathway_zero_biological_samples":zero,"pathway_extreme_sparse_sample":sparse,"pathway_fixed_features":len(pathfeatures),"pathway_stable_candidates_n30_n24_n23":stable_count,"permutations":args.permutations,"interpretation":"No result may be extrapolated to the 400-run cohort. Pathway signal is retained only if direction and FDR survive n=30 to n=24 to n=23."};(args.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (args.out/"summary.md").write_text(f"""# Fixed-30 HUMAnN publication-grade sensitivity review

This is a selected deep-review functional supplement, never 400-run functional inference.

- UniRef90 uses all 30 samples, prevalence ≥20% ({len(gene_features)} features), with 10% and 30% sensitivity ordinations. Pathogen-group PERMANOVA/PERMDISP uses 9,999 permutations but remains exploratory because groups were derived from taxonomy.
- Six samples have zero biological MetaCyc pathways: {', '.join(zero)}. SRR27344041 has two technical rows (UNMAPPED/UNINTEGRATED), not a header-only file. SRR27343296 is the prespecified extreme-sparse case.
- MetaCyc is compared at n=30, n=24 and n=23 using one fixed prevalence-filtered feature set. {stable_count} pathways retain the same top group and BH q<0.05 at n=23. Signals that disappear are annotation-detectability-driven and are not biological conclusions.
- Gene-family group FDR hits: {gene_sig}; pathogen-abundance × gene-family association FDR hits: {assoc_sig}. These are hypothesis-generating within the selected 30 only.
""")
    files=[x for x in args.out.rglob("*") if x.is_file() and x.name!="manifest.tsv"];write_tsv(args.out/"manifest.tsv",([str(x.relative_to(args.out)),x.stat().st_size] for x in sorted(files)),["path","bytes"]);print(json.dumps(summary,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
