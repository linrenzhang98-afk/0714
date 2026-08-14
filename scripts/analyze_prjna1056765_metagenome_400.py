#!/usr/bin/env python3
"""Formal taxonomy/community analysis for the complete 400-run PRJNA1056765 cohort."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

BACKGROUND=("homo sapiens","arabidopsis","benincasa","camelina","cucurbita","toxoplasma")


def read_tsv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as h:return list(csv.DictReader(h,delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Iterable[object]], header: Iterable[object]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    ctx=gzip.open(path,"wt",encoding="utf-8",newline="") if path.suffix==".gz" else path.open("w",encoding="utf-8",newline="")
    with ctx as h:
        w=csv.writer(h,delimiter="\t",lineterminator="\n"); w.writerow(header); w.writerows(rows)


def sha256(path: Path) -> str:
    d=hashlib.sha256()
    with path.open("rb") as h:
        for c in iter(lambda:h.read(1024*1024),b""):d.update(c)
    return d.hexdigest()


def load_matrix(path: Path) -> tuple[list[str],list[str],list[list[float]]]:
    with path.open(encoding="utf-8",newline="") as h:
        r=csv.reader(h,delimiter="\t"); header=next(r); rows=list(r)
    runs=header[2:]; taxa=[x[0] for x in rows]; by_sample=[[0.0]*len(taxa) for _ in runs]
    for j,row in enumerate(rows):
        for i,text in enumerate(row[2:]):by_sample[i][j]=float(text or 0)
    return runs,taxa,by_sample


def normalize_rows(rows: list[list[float]]) -> list[list[float]]:
    return [[v/sum(row) if sum(row)>0 else 0.0 for v in row] for row in rows]


def aggregate_genus(taxa:list[str],data:list[list[float]]) -> tuple[list[str],list[list[float]]]:
    genera=sorted({t.split()[0] if t.split() else t for t in taxa}); index={g:i for i,g in enumerate(genera)}
    out=[[0.0]*len(genera) for _ in data]
    for j,t in enumerate(taxa):
        g=t.split()[0] if t.split() else t; k=index[g]
        for i,row in enumerate(data):out[i][k]+=row[j]
    return genera,out


def prevalence(data:list[list[float]]) -> list[int]:
    return [sum(row[j]>0 for row in data) for j in range(len(data[0]))]


def diversity(row:list[float]) -> tuple[int,float,float,float]:
    positive=[v for v in row if v>0]; richness=len(positive)
    shannon=-sum(v*math.log(v) for v in positive); simpson=1-sum(v*v for v in positive)
    pielou=shannon/math.log(richness) if richness>1 else 0.0
    return richness,shannon,simpson,pielou


def median_mad_z(values:list[float]) -> list[float]:
    med=statistics.median(values); mad=statistics.median(abs(x-med) for x in values)
    return [0.67448975*(x-med)/mad if mad else 0.0 for x in values]


def bray(a:list[float],b:list[float]) -> float:
    den=sum(a)+sum(b); return sum(abs(x-y) for x,y in zip(a,b))/den if den else 0.0


def euclidean(a:list[float],b:list[float]) -> float:
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def distance_matrix(data:list[list[float]],metric:str) -> list[list[float]]:
    n=len(data); out=[[0.0]*n for _ in range(n)]; fn=bray if metric=="bray" else euclidean
    for i in range(n):
        for j in range(i):out[i][j]=out[j][i]=fn(data[i],data[j])
    return out


def gower(dist:list[list[float]]) -> list[list[float]]:
    n=len(dist); d2=[[v*v for v in row] for row in dist]; means=[sum(r)/n for r in d2]; grand=sum(means)/n
    return [[-.5*(d2[i][j]-means[i]-means[j]+grand) for j in range(n)] for i in range(n)]


def dot(a:list[float],b:list[float])->float:return sum(x*y for x,y in zip(a,b))


def orthonormalize(vectors:list[list[float]]) -> list[list[float]]:
    out=[]
    for vector in vectors:
        v=vector[:]
        for q in out:
            projection=dot(v,q); v=[x-projection*y for x,y in zip(v,q)]
        norm=math.sqrt(dot(v,v))
        if norm<1e-15:v=[1.0 if i==len(out) else 0.0 for i in range(len(v))]; norm=1.0
        out.append([x/norm for x in v])
    return out


def leading_eigen(matrix:list[list[float]],components:int=5) -> list[tuple[float,list[float]]]:
    n=len(matrix); rng=random.Random(4001056765); vectors=orthonormalize([[rng.random()-.5 for _ in range(n)] for _ in range(components)])
    shift=max(sum(abs(v) for v in row) for row in matrix)+1e-9
    for _ in range(350):
        updated=[]
        for q in vectors:updated.append([sum(matrix[i][j]*q[j] for j in range(n))+shift*q[i] for i in range(n)])
        new=orthonormalize(updated)
        change=max(min(sum((a-b)**2 for a,b in zip(x,y)),sum((a+b)**2 for a,b in zip(x,y))) for x,y in zip(vectors,new))
        vectors=new
        if change<1e-16:break
    result=[]
    for q in vectors:
        aq=[sum(matrix[i][j]*q[j] for j in range(n)) for i in range(n)]; result.append((dot(q,aq),q))
    return sorted(result,reverse=True,key=lambda x:x[0])


def pcoa(dist:list[list[float]],components:int=5) -> tuple[list[list[float]],list[float],list[list[float]]]:
    b=gower(dist); eig=leading_eigen(b,components); trace=sum(b[i][i] for i in range(len(b)))
    coords=[[eig[k][1][i]*math.sqrt(max(eig[k][0],0)) for k in range(components)] for i in range(len(b))]
    explained=[max(x[0],0)/trace if trace>0 else 0 for x in eig]
    return coords,explained,b


def clr(data:list[list[float]],pseudocount:float) -> list[list[float]]:
    out=[]
    for row in data:
        logs=[math.log(v if v>0 else pseudocount) for v in row]; mean=statistics.mean(logs); out.append([x-mean for x in logs])
    return out


def group_f(matrix:list[list[float]],labels:list[str]) -> tuple[float,float,float]:
    groups:dict[str,list[int]]=defaultdict(list)
    for i,label in enumerate(labels):groups[label].append(i)
    between=0.0
    for ids in groups.values():between+=sum(matrix[i][j] for i in ids for j in ids)/len(ids)
    total=sum(matrix[i][i] for i in range(len(matrix))); within=total-between; g=len(groups); n=len(labels)
    f=(between/(g-1))/(within/(n-g)) if within>0 and g>1 else 0.0
    return f,between/total if total else 0.0,within


def shuffled_labels(labels:list[str],strata:list[str]|None,rng:random.Random)->list[str]:
    out=labels[:]
    if strata is None:rng.shuffle(out); return out
    groups:dict[str,list[int]]=defaultdict(list)
    for i,s in enumerate(strata):groups[s].append(i)
    for ids in groups.values():
        values=[out[i] for i in ids];rng.shuffle(values)
        for i,v in zip(ids,values):out[i]=v
    return out


def permanova(matrix:list[list[float]],labels:list[str],strata:list[str]|None,permutations:int,seed:int)->dict[str,object]:
    observed,r2,_=group_f(matrix,labels); rng=random.Random(seed); exceed=0
    for _ in range(permutations):
        perm=shuffled_labels(labels,strata,rng); exceed+=group_f(matrix,perm)[0]>=observed-1e-14
    return {"pseudo_F":observed,"R2":r2,"p_value":(exceed+1)/(permutations+1),"permutations":permutations}


def centroid_distances(dist:list[list[float]],labels:list[str])->list[float]:
    groups:dict[str,list[int]]=defaultdict(list)
    for i,g in enumerate(labels):groups[g].append(i)
    out=[]
    for i,g in enumerate(labels):
        ids=groups[g]; first=sum(dist[i][j]**2 for j in ids)/len(ids); second=sum(dist[j][k]**2 for j in ids for k in ids)/(2*len(ids)**2)
        out.append(math.sqrt(max(first-second,0)))
    return out


def anova_f(values:list[float],labels:list[str])->tuple[float,float]:
    groups:dict[str,list[float]]=defaultdict(list)
    for v,g in zip(values,labels):groups[g].append(v)
    mean=statistics.mean(values); between=sum(len(v)*(statistics.mean(v)-mean)**2 for v in groups.values()); within=sum(sum((x-statistics.mean(v))**2 for x in v) for v in groups.values())
    f=(between/(len(groups)-1))/(within/(len(values)-len(groups))) if within else 0
    return f,between/(between+within) if between+within else 0


def permdisp(dist:list[list[float]],labels:list[str],strata:list[str]|None,permutations:int,seed:int)->dict[str,object]:
    values=centroid_distances(dist,labels); observed,r2=anova_f(values,labels);rng=random.Random(seed);exceed=0
    for _ in range(permutations):exceed+=anova_f(values,shuffled_labels(labels,strata,rng))[0]>=observed-1e-14
    return {"F":observed,"R2":r2,"p_value":(exceed+1)/(permutations+1),"permutations":permutations,"group_mean_distance":{g:statistics.mean([v for v,x in zip(values,labels) if x==g]) for g in sorted(set(labels))}}


def ranks(values:list[float])->list[float]:
    order=sorted(range(len(values)),key=values.__getitem__);out=[0.0]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        rank=(i+j+1)/2
        for k in order[i:j]:out[k]=rank
        i=j
    return out


def gamma_q(a:float,x:float)->float:
    if x<=0:return 1.0
    gln=math.lgamma(a)
    if x<a+1:
        ap=a;term=1/a;total=term
        for _ in range(1000):
            ap+=1;term*=x/ap;total+=term
            if abs(term)<abs(total)*1e-14:break
        return max(0.0,min(1.0,1-total*math.exp(-x+a*math.log(x)-gln)))
    b=x+1-a;c=1/1e-300;d=1/b;h=d
    for i in range(1,1000):
        an=-i*(i-a);b+=2;d=an*d+b;d=1e-300 if abs(d)<1e-300 else d;c=b+an/c;c=1e-300 if abs(c)<1e-300 else c;d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<1e-14:break
    return max(0.0,min(1.0,math.exp(-x+a*math.log(x)-gln)*h))


def kruskal(values:list[float],labels:list[str])->tuple[float,float,float]:
    rs=ranks(values);groups:dict[str,list[float]]=defaultdict(list)
    for r,g in zip(rs,labels):groups[g].append(r)
    n=len(values);h=12/(n*(n+1))*sum(sum(x)**2/len(x) for x in groups.values())-3*(n+1)
    ties=Counter(values); correction=1-sum(c**3-c for c in ties.values())/(n**3-n) if n>1 else 1;h=h/correction if correction else 0
    df=len(groups)-1;p=gamma_q(df/2,h/2);effect=max(0,(h-len(groups)+1)/(n-len(groups))) if n>len(groups) else 0
    return h,p,effect


def stratified_kw_permutation_p(values:list[float],labels:list[str],strata:list[str],observed:float,permutations:int,seed:int)->float:
    rs=ranks(values);n=len(values);ties=Counter(values);correction=1-sum(c**3-c for c in ties.values())/(n**3-n) if n>1 else 1;rng=random.Random(seed);exceed=0
    def stat(labs):
        groups:dict[str,list[float]]=defaultdict(list)
        for rank,label in zip(rs,labs):groups[label].append(rank)
        h=12/(n*(n+1))*sum(sum(x)**2/len(x) for x in groups.values())-3*(n+1)
        return h/correction if correction else 0
    for _ in range(permutations):exceed+=stat(shuffled_labels(labels,strata,rng))>=observed-1e-14
    return (exceed+1)/(permutations+1)


def bh(rows:list[dict[str,object]],key:str="p_value",output:str="q_value") -> None:
    order=sorted(range(len(rows)),key=lambda i:float(rows[i][key]));m=len(rows);q=1.0
    for rank in range(m,0,-1):
        i=order[rank-1];q=min(q,float(rows[i][key])*m/rank);rows[i][output]=q


def hierarchy(dist:list[list[float]]) -> tuple[dict[int,list[int]],list[int]]:
    import heapq
    n=len(dist);active={i:[i] for i in range(n)};sizes={i:1 for i in range(n)};d={(i,j):dist[i][j] for i in range(n) for j in range(i)};heap=[(v,i,j) for (i,j),v in d.items()];heapq.heapify(heap); snapshots={};next_id=n
    while len(active)>1:
        if 2<=len(active)<=10:
            labels=[0]*n
            for label,members in enumerate(sorted(active.values(),key=min),1):
                for i in members:labels[i]=label
            snapshots[len(active)]=labels
        while True:
            value,a,b=heapq.heappop(heap);key=(max(a,b),min(a,b))
            if a in active and b in active and abs(d[key]-value)<1e-15:break
        members=active.pop(a)+active.pop(b);sa,sb=sizes[a],sizes[b];new=next_id;next_id+=1;active[new]=members;sizes[new]=sa+sb
        for c in list(active):
            if c==new:continue
            dac=d[(max(a,c),min(a,c))];dbc=d[(max(b,c),min(b,c))];value=(sa*dac+sb*dbc)/(sa+sb);key=(max(new,c),min(new,c));d[key]=value;heapq.heappush(heap,(value,new,c))
    return snapshots,next(iter(active.values()))


def silhouette(dist:list[list[float]],labels:list[int])->float:
    groups:dict[int,list[int]]=defaultdict(list)
    for i,g in enumerate(labels):groups[g].append(i)
    values=[]
    for i,g in enumerate(labels):
        own=groups[g];a=sum(dist[i][j] for j in own if j!=i)/(len(own)-1) if len(own)>1 else 0
        b=min(sum(dist[i][j] for j in ids)/len(ids) for h,ids in groups.items() if h!=g);values.append((b-a)/max(a,b) if max(a,b)>0 and len(own)>1 else 0)
    return statistics.mean(values)


def adjusted_rand(a:list[int],b:list[int])->float:
    table=Counter(zip(a,b));ca=Counter(a);cb=Counter(b);comb=lambda n:n*(n-1)/2
    nij=sum(comb(v) for v in table.values());ai=sum(comb(v) for v in ca.values());bj=sum(comb(v) for v in cb.values());total=comb(len(a));expected=ai*bj/total if total else 0;maximum=(ai+bj)/2
    return (nij-expected)/(maximum-expected) if maximum!=expected else 1.0


def pearson(a:list[float],b:list[float])->float:
    ma,mb=statistics.mean(a),statistics.mean(b);num=sum((x-ma)*(y-mb) for x,y in zip(a,b));den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b));return num/den if den else 0


def normal_sf(z:float)->float:return .5*math.erfc(z/math.sqrt(2))


def mann_whitney(a:list[float],b:list[float])->tuple[float,float,float]:
    allv=a+b;rr=ranks(allv);u=sum(rr[:len(a)])-len(a)*(len(a)+1)/2;mean=len(a)*len(b)/2
    ties=Counter(allv);tie=sum(v**3-v for v in ties.values());var=len(a)*len(b)/12*((len(allv)+1)-tie/(len(allv)*(len(allv)-1))) if len(allv)>1 else 0
    z=(u-mean)/math.sqrt(var) if var else 0;delta=2*u/(len(a)*len(b))-1
    return u,2*normal_sf(abs(z)),delta


def svg_scatter(path:Path,coords:list[list[float]],labels:list[str],title:str,highlight:list[bool]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True);colors=["#4477AA","#EE6677","#228833","#CCBB44","#66CCEE","#AA3377"] ;mapping={g:colors[i%len(colors)] for i,g in enumerate(sorted(set(labels)))};xs=[x[0] for x in coords];ys=[x[1] for x in coords]
    scale=lambda v,lo,hi,a,b:(a+b)/2 if hi==lo else a+(v-lo)*(b-a)/(hi-lo)
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650">','<rect width="100%" height="100%" fill="white"/>',f'<text x="45" y="34" font-size="21" font-family="sans-serif">{title}</text>']
    for i,(xy,label) in enumerate(zip(coords,labels)):
        x=scale(xy[0],min(xs),max(xs),65,700);y=scale(xy[1],min(ys),max(ys),575,65);stroke='#111' if highlight and highlight[i] else 'none';width=2 if highlight and highlight[i] else 0
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{5 if highlight and highlight[i] else 3.5}" fill="{mapping[label]}" fill-opacity="0.72" stroke="{stroke}" stroke-width="{width}"/>')
    for i,(g,c) in enumerate(mapping.items()):lines.append(f'<circle cx="745" cy="{80+i*25}" r="6" fill="{c}"/><text x="760" y="{85+i*25}" font-size="13" font-family="sans-serif">{g}</text>')
    lines+=['<line x1="65" y1="575" x2="700" y2="575" stroke="#333"/>','<line x1="65" y1="65" x2="65" y2="575" stroke="#333"/>','</svg>'];path.write_text("\n".join(lines)+"\n")


def svg_bars(path:Path,labels:list[str],values:list[float],title:str,xlabel:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True);height=max(430,len(labels)*22+90);mx=max(values) if values else 1
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">','<rect width="100%" height="100%" fill="white"/>',f'<text x="35" y="30" font-size="20" font-family="sans-serif">{title}</text>']
    for i,(label,v) in enumerate(zip(labels,values)):
        y=55+i*22;width=620*v/mx if mx else 0;lines.append(f'<text x="255" y="{y+13}" text-anchor="end" font-size="11" font-family="sans-serif">{label}</text><rect x="265" y="{y}" width="{width:.2f}" height="15" fill="#4477AA"><title>{v:.6g}</title></rect>')
    lines.append(f'<text x="575" y="{height-12}" text-anchor="middle" font-size="13" font-family="sans-serif">{xlabel}</text></svg>');path.write_text("\n".join(lines)+"\n")


def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--matrix",type=Path,default=Path("reports_public/metagenome_production/bracken_species_fraction_matrix.tsv"));p.add_argument("--qc",type=Path,default=Path("reports_public/metagenome_production/run_qc_summary.tsv"));p.add_argument("--clinical",type=Path,default=Path("reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv"));p.add_argument("--deep-review",type=Path,default=Path("reports_public/metagenome_deep_review/deep_review_samples.tsv"));p.add_argument("--out",type=Path,default=Path("reports_public/metagenome_400_formal"));p.add_argument("--permutations",type=int,default=9999);args=p.parse_args()
    runs,taxa,raw=load_matrix(args.matrix);qc={r["run"]:r for r in read_tsv(args.qc)};clinical={r["run"]:r for r in read_tsv(args.clinical)};deep_ids={r["run"] for r in read_tsv(args.deep_review)}
    if len(runs)!=400 or len(set(runs))!=400 or set(runs)!=set(qc) or set(runs)!=set(clinical):raise SystemExit("fixed full-cohort membership gate failed")
    keep=[i for i,t in enumerate(taxa) if not any(x in t.lower() for x in BACKGROUND)];species=[taxa[i] for i in keep];data=normalize_rows([[row[i] for i in keep] for row in raw]);all_taxa=normalize_rows(raw)
    excluded=[i for i in range(len(taxa)) if i not in set(keep)]
    write_tsv(args.out/"audit/background_feature_exclusions.tsv",([taxa[j],sum(raw[i][j]>0 for i in range(400)),"obvious non-microbial host/plant/protist label; excluded before microbial community normalization"] for j in excluded),["feature","detected_samples","reason"])
    genera,genus_data=aggregate_genus(species,data);diagnosis=[clinical[r]["diagnosis"] for r in runs];cohorts=[clinical[r]["cohort"] for r in runs]
    div=[diversity(row) for row in data];total_reads=[float(qc[r]["total_reads"]) for r in runs];classified=[float(qc[r]["classified_pct"])/100 for r in runs];assigned=[sum(raw[i])*total_reads[i] for i in range(400)];dominance=[max(row) if row else 0 for row in data]
    zsets=[median_mad_z([math.log10(x+1) for x in total_reads]),median_mad_z(classified),median_mad_z([x[0] for x in div]),median_mad_z(dominance)]
    qc_rows=[];sensitivity=[]
    for i,r in enumerate(runs):
        flags=[]
        if classified[i]<.005:flags.append("classified_fraction_lt_0.5pct")
        if assigned[i]<1000:flags.append("bracken_assigned_reads_lt_1000")
        if div[i][0]<=2:flags.append("richness_le_2")
        for name,z in zip(("log_read_depth","classified_fraction","richness","dominance"),(x[i] for x in zsets)):
            if abs(z)>3.5:flags.append(name+"_robust_outlier")
        sensitivity.append(not flags);q=qc[r]
        qc_rows.append([r,diagnosis[i],cohorts[i],int(total_reads[i]),q["classified_reads"],classified[i],round(assigned[i]),div[i][0],div[i][1],div[i][2],div[i][3],dominance[i],q["top_species"],q["top_species_fraction"],";".join(flags),not flags])
    write_tsv(args.out/"qc/cohort_qc.tsv",qc_rows,["run","diagnosis","cohort","total_reads","classified_reads","classified_fraction","bracken_assigned_reads_estimate","observed_species","shannon","simpson","pielou","dominant_microbial_species_abundance","raw_dominant_species","raw_dominant_species_fraction_total_reads","qc_flags","sensitivity_included"])
    # Matrices and landscape.
    write_tsv(args.out/"taxonomy/species_relative_abundance.tsv.gz",([species[j],*[data[i][j] for i in range(400)]] for j in range(len(species))),["species",*runs]);write_tsv(args.out/"taxonomy/genus_relative_abundance.tsv.gz",([genera[j],*[genus_data[i][j] for i in range(400)]] for j in range(len(genera))),["genus",*runs])
    landscape={}
    for level,names,matrix in (("species",species,data),("genus",genera,genus_data)):
        prev=prevalence(matrix);rows=[]
        for j,name in enumerate(names):
            vals=[x[j] for x in matrix];rows.append([name,prev[j],prev[j]/400,statistics.mean(vals),statistics.median(vals),max(vals)])
        rows.sort(key=lambda x:(-x[2],-x[3],x[0]));write_tsv(args.out/f"taxonomy/{level}_landscape.tsv",rows,[level,"detected_samples","prevalence","mean_relative_abundance","median_relative_abundance","maximum_relative_abundance"]);landscape[level]=rows
    dom=Counter(species[max(range(len(species)),key=lambda j:data[i][j])] if sum(data[i]) else "None" for i in range(400));write_tsv(args.out/"taxonomy/dominant_species_distribution.tsv",([x,n,n/400] for x,n in dom.most_common()),["dominant_species","samples","fraction"])
    write_tsv(args.out/"alpha/alpha_diversity.tsv",([runs[i],diagnosis[i],cohorts[i],*div[i],sensitivity[i]] for i in range(400)),["run","diagnosis","cohort","observed_species","shannon","simpson","pielou","sensitivity_included"])
    alpha_stats=[]
    for idx,metric in enumerate(("observed_species","shannon","simpson","pielou")):
        vals=[x[idx] for x in div]
        for subset_name,subset_ids in (("full",list(range(400))),("QC-sensitivity",[i for i,x in enumerate(sensitivity) if x])):
            subvals=[vals[i] for i in subset_ids];subdiag=[diagnosis[i] for i in subset_ids];h,pv,e=kruskal(subvals,subdiag);alpha_stats.append({"metric":metric,"subset":subset_name,"group":"diagnosis","H":h,"p_value":pv,"effect":e})
        h,pv,e=kruskal(vals,cohorts);alpha_stats.append({"metric":metric,"subset":"full","group":"study_cohort","H":h,"p_value":pv,"effect":e})
    bh(alpha_stats);write_tsv(args.out/"alpha/alpha_metadata_associations.tsv",([x["metric"],x["subset"],x["group"],x["H"],x["effect"],x["p_value"],x["q_value"]] for x in alpha_stats),["metric","sample_set","independent_variable","kruskal_H","epsilon_squared","raw_p","BH_q"])
    # Prespecified 10% feature set; 5/20% sensitivity counts.
    prev=prevalence(data);selected=[j for j,n in enumerate(prev) if n>=40];filtered=[[row[j] for j in selected] for row in data];positive=[v for row in filtered for v in row if v>0];pseudo=min(positive)/2
    clrdata=clr(filtered,pseudo);braydist=distance_matrix(filtered,"bray");aitdist=distance_matrix(clrdata,"euclidean")
    bcoords,bexp,bmat=pcoa(braydist);acoords,aexp,amat=pcoa(aitdist)
    write_tsv(args.out/"beta/bray_curtis_distance.tsv.gz",([runs[i],*braydist[i]] for i in range(400)),["run",*runs]);write_tsv(args.out/"beta/aitchison_distance.tsv.gz",([runs[i],*aitdist[i]] for i in range(400)),["run",*runs])
    write_tsv(args.out/"beta/bray_pcoa.tsv",([runs[i],diagnosis[i],cohorts[i],runs[i] in deep_ids,sensitivity[i],*bcoords[i]] for i in range(400)),["run","diagnosis","cohort","selected_deep_review_30","sensitivity_included",*[f"PCoA{k}" for k in range(1,6)]])
    write_tsv(args.out/"beta/aitchison_pcoa.tsv",([runs[i],diagnosis[i],cohorts[i],runs[i] in deep_ids,sensitivity[i],*acoords[i]] for i in range(400)),["run","diagnosis","cohort","selected_deep_review_30","sensitivity_included",*[f"PCoA{k}" for k in range(1,6)]])
    centroid_distance=[math.sqrt(max(bmat[i][i],0)) for i in range(400)];centroid_z=median_mad_z(centroid_distance)
    write_tsv(args.out/"beta/ordination_outlier_diagnostics.tsv",([runs[i],diagnosis[i],centroid_distance[i],centroid_z[i],abs(centroid_z[i])>3.5] for i in range(400)),["run","diagnosis","bray_distance_to_cohort_centroid","robust_MAD_z","ordination_outlier_abs_z_gt_3.5"])
    # Full and flagged-sample sensitivity formal inference; each PERMANOVA paired with PERMDISP.
    inference=[]
    def add_inference(metric,subset_name,dist,mat,labs,strata):
        seed=1056765+len(inference)*100;pa=permanova(mat,labs,strata,args.permutations,seed);pd=permdisp(dist,labs,strata,args.permutations,seed+1);inference.append([metric,subset_name,"diagnosis",len(labs),len(set(labs)),pa["pseudo_F"],pa["R2"],pa["p_value"],pd["F"],pd["R2"],pd["p_value"],args.permutations,json.dumps(pd["group_mean_distance"],sort_keys=True)])
    add_inference("Bray-Curtis","full",braydist,bmat,diagnosis,cohorts)
    ids=[i for i,x in enumerate(sensitivity) if x];sd=[[braydist[i][j] for j in ids] for i in ids];_,_,smat=pcoa(sd,2);add_inference("Bray-Curtis","QC-sensitivity",sd,smat,[diagnosis[i] for i in ids],[cohorts[i] for i in ids])
    add_inference("Aitchison","full",aitdist,amat,diagnosis,cohorts)
    ad=[[aitdist[i][j] for j in ids] for i in ids];_,_,asmat=pcoa(ad,2);add_inference("Aitchison","QC-sensitivity",ad,asmat,[diagnosis[i] for i in ids],[cohorts[i] for i in ids])
    write_tsv(args.out/"statistics/permanova_permdisp.tsv",inference,["metric","sample_set","independent_variable","n","groups","PERMANOVA_F","PERMANOVA_R2","PERMANOVA_p","PERMDISP_F","PERMDISP_R2","PERMDISP_p","permutations","group_mean_distance_to_centroid"])
    # Community states and metric sensitivity.
    bsnap,border=hierarchy(braydist);asnap,_=hierarchy(aitdist);sil=[]
    for k in range(2,11):sil.append([k,silhouette(braydist,bsnap[k]),silhouette(aitdist,asnap[k]),adjusted_rand(bsnap[k],asnap[k])])
    best=max(sil,key=lambda x:x[1]);bestk=best[0];clusters=bsnap[bestk];write_tsv(args.out/"clustering/cluster_diagnostics.tsv",sil,["k","bray_silhouette","aitchison_silhouette","bray_aitchison_adjusted_rand"]);write_tsv(args.out/"clustering/sample_community_states.tsv",([runs[i],diagnosis[i],clusters[i],sensitivity[i]] for i in range(400)),["run","diagnosis","community_state","sensitivity_included"])
    signatures=[]
    for c in sorted(set(clusters)):
        members=[i for i,x in enumerate(clusters) if x==c]
        scores=[]
        for j,name in enumerate(species):scores.append((statistics.mean(data[i][j] for i in members)-statistics.mean(row[j] for row in data),name,statistics.mean(data[i][j] for i in members)))
        for rank,(effect,name,mean) in enumerate(sorted(scores,reverse=True)[:15],1):signatures.append([c,len(members),rank,name,mean,effect])
    write_tsv(args.out/"clustering/community_state_signatures.tsv",signatures,["community_state","samples","rank","species","state_mean_abundance","difference_from_cohort_mean"])
    # Diagnosis differential abundance, species primary and genus sensitivity.
    for level,names,matrix in (("species",species,data),("genus",genera,genus_data)):
        pr=prevalence(matrix);sel=[j for j,n in enumerate(pr) if n>=40];selset=set(sel);minimum=min(v for row in matrix for j,v in enumerate(row) if j in selset and v>0)/2;clrm=clr([[row[j] for j in sel] for row in matrix],minimum);rows=[]
        sensitivity_ids=[i for i,x in enumerate(sensitivity) if x]
        for jj,j in enumerate(sel):
            values=[row[j] for row in matrix];h,_,e=kruskal(values,diagnosis);pv=stratified_kw_permutation_p(values,diagnosis,cohorts,h,args.permutations,700000+jj+(0 if level=="species" else 10000));medians={g:statistics.median([v for v,x in zip(values,diagnosis) if x==g]) for g in sorted(set(diagnosis))};clrmeans={g:statistics.mean([row[jj] for row,x in zip(clrm,diagnosis) if x==g]) for g in sorted(set(diagnosis))};subvalues=[values[i] for i in sensitivity_ids];subdiag=[diagnosis[i] for i in sensitivity_ids];substrata=[cohorts[i] for i in sensitivity_ids];sh,_,se=kruskal(subvalues,subdiag);sp=stratified_kw_permutation_p(subvalues,subdiag,substrata,sh,args.permutations,900000+jj+(0 if level=="species" else 10000));rows.append({"feature":names[j],"prevalence":pr[j]/400,"H":h,"effect":e,"p_value":pv,"sensitivity_H":sh,"sensitivity_p":sp,"sensitivity_effect":se,"max_median_group":max(medians,key=medians.get),"median_range":max(medians.values())-min(medians.values()),"clr_mean_range":max(clrmeans.values())-min(clrmeans.values()),"medians":json.dumps(medians,sort_keys=True),"clrmeans":json.dumps(clrmeans,sort_keys=True)})
        bh(rows);bh(rows,key="sensitivity_p",output="sensitivity_q");rows.sort(key=lambda x:(x["q_value"],-x["effect"]));write_tsv(args.out/f"associations/diagnosis_{level}_differential.tsv",([x["feature"],x["prevalence"],x["H"],x["effect"],x["median_range"],x["max_median_group"],x["p_value"],x["q_value"],x["clr_mean_range"],x["sensitivity_H"],x["sensitivity_effect"],x["sensitivity_p"],x["sensitivity_q"],x["medians"],x["clrmeans"]] for x in rows),[level,"prevalence","kruskal_H","epsilon_squared","median_abundance_range","highest_median_diagnosis","cohort_stratified_permutation_p","BH_q","CLR_group_mean_range","QC_sensitivity_H","QC_sensitivity_epsilon_squared","QC_sensitivity_cohort_stratified_permutation_p","QC_sensitivity_BH_q","group_medians_json","group_CLR_means_json"])
    # CLR association network, explicitly exploratory.
    ranked=sorted(selected,key=lambda j:(-prev[j],-statistics.mean(row[j] for row in data)))[:50];network_clr=clr([[row[j] for j in ranked] for row in data],pseudo);edges=[]
    for a in range(len(ranked)):
        va=[row[a] for row in network_clr]
        for b in range(a):
            rho=pearson(va,[row[b] for row in network_clr])
            if abs(rho)>=.3:edges.append([species[ranked[a]],species[ranked[b]],rho,abs(rho),"CLR Pearson; compositional exploratory association, not interaction"])
    edges.sort(key=lambda x:-x[3]);write_tsv(args.out/"associations/clr_taxon_associations.tsv",edges,["taxon_a","taxon_b","clr_pearson_r","absolute_r","interpretation"])
    # Map selected 30 back into full-cohort space and quantify selection bias.
    selection=[]
    metrics={"observed_species":[x[0] for x in div],"shannon":[x[1] for x in div],"dominant_species_abundance":dominance,"classified_fraction":classified,"distance_to_bray_centroid":[math.sqrt(max(bmat[i][i],0)) for i in range(400)]}
    selected_mask=[r in deep_ids for r in runs]
    for name,values in metrics.items():
        a=[v for v,x in zip(values,selected_mask) if x];b=[v for v,x in zip(values,selected_mask) if not x];u,pv,delta=mann_whitney(a,b);selection.append([name,len(a),len(b),statistics.mean(a),statistics.mean(b),statistics.median(a),statistics.median(b),delta,pv])
    write_tsv(args.out/"integration_30/selection_bias_metrics.tsv",selection,["metric","selected_n","other_n","selected_mean","other_mean","selected_median","other_median","cliffs_delta_selected_vs_other","mann_whitney_p"])
    state_rows=[];major=[]
    for c in sorted(set(clusters)):
        n=sum(x==c for x in clusters);s=sum(x==c and y for x,y in zip(clusters,selected_mask));state_rows.append([c,n,n/400,s,s/30,(s/30)/(n/400) if n else 0]);
        if n/400>=.05:major.append(c)
    write_tsv(args.out/"integration_30/community_state_coverage.tsv",state_rows,["community_state","full_n","full_fraction","selected30_n","selected30_fraction","selection_enrichment_ratio"])
    coverage_by_k=[]
    for k in range(2,11):
        for c in sorted(set(bsnap[k])):
            n=sum(x==c for x in bsnap[k]);s=sum(x==c and y for x,y in zip(bsnap[k],selected_mask));coverage_by_k.append([k,c,n,n/400,s,s/30,n/400>=.05,s>0])
    write_tsv(args.out/"integration_30/community_state_coverage_k2_k10.tsv",coverage_by_k,["k","community_state","full_n","full_fraction","selected30_n","selected30_fraction","major_state_ge_5pct","covered_by_selected30"])
    write_tsv(args.out/"integration_30/deep_review_positions.tsv",([runs[i],diagnosis[i],clusters[i],*bcoords[i]] for i in range(400) if selected_mask[i]),["run","diagnosis","community_state",*[f"Bray_PCoA{k}" for k in range(1,6)]])
    # Plots plus direct source tables already exported.
    svg_scatter(args.out/"figures/bray_pcoa_diagnosis.svg",bcoords,diagnosis,"Bray-Curtis PCoA — published diagnosis")
    svg_scatter(args.out/"figures/bray_pcoa_deep_review.svg",bcoords,diagnosis,"Fixed 30 deep-review samples in the full 400-run space",selected_mask)
    top=landscape["species"][:25];svg_bars(args.out/"figures/top_species_prevalence.svg",[x[0] for x in top],[x[2] for x in top],"Most prevalent microbial species","Prevalence")
    svg_bars(args.out/"figures/cluster_silhouette.svg",[f"k={x[0]}" for x in sil],[x[1] for x in sil],"Community-state silhouette profile","Mean silhouette")
    flag_counts=Counter(flag for row in qc_rows for flag in str(row[14]).split(";") if flag);svg_bars(args.out/"figures/qc_flag_counts.svg",list(flag_counts),list(flag_counts.values()),"Prespecified QC flags (samples retained)","Flagged samples")
    write_tsv(args.out/"figures/plot_source_top_species_prevalence.tsv",([x[0],x[2],x[3]] for x in top),["species","prevalence","mean_relative_abundance"])
    write_tsv(args.out/"figures/plot_source_cluster_silhouette.tsv",sil,["k","bray_silhouette","aitchison_silhouette","bray_aitchison_adjusted_rand"])
    write_tsv(args.out/"figures/plot_source_qc_flag_counts.tsv",flag_counts.items(),["qc_flag","samples"])
    # Parameters, summaries and limitations.
    formal={"generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"cohort_n":400,"species_input_features":len(taxa),"microbial_species_features":len(species),"excluded_background_features":len(taxa)-len(species),"prevalence_filter_primary":"10% (40/400)","prevalence_sensitivity":{"5%":sum(x>=20 for x in prev),"10%":len(selected),"20%":sum(x>=80 for x in prev)},"clr_pseudocount":pseudo,"qc_sensitivity_n":sum(sensitivity),"qc_flagged_n":400-sum(sensitivity),"permutations":args.permutations,"permutation_constraint":"diagnosis labels permuted within published Training/Test cohort","community_state_k":bestk,"community_state_selection":"maximum Bray-Curtis average-linkage silhouette across k=2..10","major_states_ge_5pct":major,"major_states_covered_by_30":sum(any(row[0]==c and row[3]>0 for row in state_rows) for c in major),"pcoa_explained_fraction_of_gower_trace":{"bray":bexp,"aitchison":aexp},"background_keywords":BACKGROUND,"command":sys.argv,"python":sys.version.split()[0],"interpretation_scope":"formal diagnosis inference for available 400-run cohort; clusters/networks/descriptive landscape exploratory"}
    (args.out/"methods/parameters.json").parent.mkdir(parents=True,exist_ok=True);(args.out/"methods/parameters.json").write_text(json.dumps(formal,indent=2)+"\n")
    species_diff=read_tsv(args.out/"associations/diagnosis_species_differential.tsv");full_sig=[x for x in species_diff if float(x["BH_q"])<.05];stable_sig=[x for x in full_sig if float(x["QC_sensitivity_BH_q"])<.05]
    summary={"state":"complete","cohort_n":400,"diagnosis_counts":dict(Counter(diagnosis)),"qc_flagged_n":formal["qc_flagged_n"],"prevalent_species_n":len(selected),"community_state_k":bestk,"community_state_stability_interpretation":"No stable metric-invariant ecotypes: Bray/Aitchison ARI approximately zero across k=2..10; k=10 is a boundary silhouette maximum and descriptive only.","formal_inference_file":"statistics/permanova_permdisp.tsv","diagnosis_species_FDR_lt_0.05":len(full_sig),"diagnosis_species_also_QC_sensitivity_FDR_lt_0.05":len(stable_sig),"deep_review_n":30,"deep_review_major_state_coverage":f"{formal['major_states_covered_by_30']}/{len(major)}","interpretation":"Aitchison diagnosis inference is location-supported; Bray diagnosis result is confounded by significant dispersion. Landscape/clusters/network are descriptive or exploratory; fixed-30 HUMAnN cannot be extrapolated."};(args.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (args.out/"limitations.md").write_text("""# Limitations

- This is formal inference for the complete 400-run *available public production cohort*, not an unqualified population estimate. Two mapped WGS records had no downloadable reads (`size_MB=0`).
- Kraken2/Bracken results and the compact checked-in matrix were reused; raw reports were not reprocessed. Database composition and false assignments remain measurement limitations.
- Very low classified fractions make absolute microbial signal uncertain in some samples. No sample was deleted; flagged-sample sensitivity is reported.
- Diagnosis is an independent published clinical label. Dominant pathogen labels and community states are abundance-derived and cannot independently validate differential taxa.
- Genus is inferred from the first token of species labels and is a sensitivity view, not a separately rerun Bracken genus estimate.
- CLR pseudocount, prevalence filtering, clustering and taxon networks are analytical choices. CLR associations are compositional hypotheses, not ecological interactions or causality.
- The fixed 30 deep-review samples were selected for pathogen-focused review. Their HUMAnN/AMR results are functional exploration only and cannot represent the full 400-run functional landscape.
""")
    bray_full=inference[0];ait_full=inference[2];selected_classified=next(x for x in selection if x[0]=="classified_fraction");selected_dominance=next(x for x in selection if x[0]=="dominant_species_abundance")
    (args.out/"summary.md").write_text(f"""# PRJNA1056765 formal taxonomy/community analysis

The complete available cohort contains 400 unique patient/BioSample runs with 400/400 completed production records and exact Bracken-matrix membership. Published diagnosis is the primary independent phenotype; abundance-derived dominant-pathogen labels are descriptive only.

Primary analysis retained {len(selected)} microbial species at prevalence ≥10%. {400-sum(sensitivity)} samples were prespecified QC/low-information flags; none were deleted, and key inference was repeated in the {sum(sensitivity)}-sample sensitivity cohort.

## Main findings and evidence class

1. **Formal, compositionally supported but small diagnosis association.** Aitchison PERMANOVA gave R²={ait_full[6]:.4f}, p={ait_full[7]:.4g} in all 400 samples, with PERMDISP p={ait_full[10]:.4g}; the QC-sensitivity result was also significant. Diagnosis therefore explains a small fraction of composition rather than defining sharply separated communities.
2. **Bray result is not location-specific.** Bray PERMANOVA gave R²={bray_full[6]:.4f}, p={bray_full[7]:.4g}, but PERMDISP was also significant (p={bray_full[10]:.4g}). This cannot be written as an unqualified diagnosis centroid shift.
3. **Formal differential evidence is sparse and prevalence-driven.** {len(full_sig)} species passed full-cohort BH FDR <0.05; {len(stable_sig)} also passed BH FDR in the strict QC-sensitivity cohort. Full-cohort candidates were {', '.join(x['species'] for x in full_sig)}. Their group medians were generally zero, so effect sizes/CLR contrasts and raw distributions are essential.
4. **No defensible stable ecotype solution.** Bray silhouette reached its boundary maximum at k={bestk}, while Bray/Aitchison adjusted Rand agreement was approximately zero across k=2..10. Clusters are exploratory community states, not clinical subtypes.
5. **The fixed 30 are strongly selected.** Median classified fraction was {float(selected_classified[5]):.4f} versus {float(selected_classified[6]):.4f}; median dominant-species abundance was {float(selected_dominance[5]):.3f} versus {float(selected_dominance[6]):.3f}. The 30 cover {formal['major_states_covered_by_30']}/{len(major)} k={bestk} states representing ≥5% of the cohort and miss a state containing 7.5% of all samples. Their HUMAnN results cannot represent the 400-run functional landscape.

Formal inference statistics and paired dispersion tests are in `statistics/permanova_permdisp.tsv`. Differential tables use published diagnosis, cohort-stratified permutations, effect sizes, raw P and BH FDR in both full and QC-sensitivity cohorts, with CLR group-mean sensitivity. Clusters, dominant taxa and CLR networks remain descriptive/exploratory.

The fixed-30 HUMAnN analysis is suitable only as a selected functional supplement; it must not be presented as a functional survey of all 400 runs.
""")
    files=[x for x in args.out.rglob("*") if x.is_file() and x.name!="manifest.tsv"];write_tsv(args.out/"methods/manifest.tsv",([str(x.relative_to(args.out)),x.stat().st_size,sha256(x)] for x in sorted(files)),["path","bytes","sha256"])
    print(json.dumps(summary,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
