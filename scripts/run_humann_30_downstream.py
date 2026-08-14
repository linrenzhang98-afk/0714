#!/usr/bin/env python3
"""Lightweight, reproducible downstream analysis of the fixed 30 HUMAnN outputs."""

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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

KINDS = ("genefamilies", "pathabundance", "pathcoverage")
EXCLUDED = {"UNMAPPED", "UNINTEGRATED"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Iterable[object]], header: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_context = gzip.open(path, mode="wt", encoding="utf-8", newline="") if path.suffix == ".gz" else path.open(mode="w", encoding="utf-8", newline="")
    with handle_context as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header); writer.writerows(rows)


def profile(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\r\n").split("\t")
            values[fields[0]] = float(fields[1])
    return values


def matrix_rows(features: list[str], samples: list[str], data: dict[str, dict[str, float]]):
    for feature in features:
        yield [feature, *(format(data[s].get(feature, 0.0), ".10g") for s in samples)]


def normalize(data: dict[str, dict[str, float]], kind: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for sample, values in data.items():
        if kind == "pathcoverage":
            out[sample] = dict(values)
            continue
        denominator = sum(v for f, v in values.items() if f not in EXCLUDED)
        out[sample] = {f: (v / denominator if denominator else 0.0) for f, v in values.items()}
    return out


def filtered_features(data: dict[str, dict[str, float]], samples: list[str], minimum: int) -> list[str]:
    universe = sorted(set().union(*(set(x) for x in data.values())))
    return [f for f in universe if f not in EXCLUDED and "|" not in f and sum(data[s].get(f, 0) > 0 for s in samples) >= minimum]


def bray(a: list[float], b: list[float]) -> float:
    denominator = sum(a) + sum(b)
    return sum(abs(x-y) for x, y in zip(a, b)) / denominator if denominator else 0.0


def symmetric_eigen(a: list[list[float]]) -> list[tuple[float, list[float]]]:
    """Jacobi eigensolver; sufficient and deterministic for the fixed 30x30 matrix."""
    n=len(a); work=[row[:] for row in a]; vectors=[[float(i==j) for j in range(n)] for i in range(n)]
    for _ in range(100*n*n):
        p,q=max(((i,j) for i in range(n) for j in range(i+1,n)),key=lambda ij:abs(work[ij[0]][ij[1]]))
        if abs(work[p][q]) < 1e-12: break
        angle=.5*math.atan2(2*work[p][q],work[q][q]-work[p][p]); c=math.cos(angle); s=math.sin(angle)
        for k in range(n):
            if k not in (p,q):
                wkp,wkq=work[k][p],work[k][q]; work[k][p]=work[p][k]=c*wkp-s*wkq; work[k][q]=work[q][k]=s*wkp+c*wkq
        app,aqq,apq=work[p][p],work[q][q],work[p][q]
        work[p][p]=c*c*app-2*s*c*apq+s*s*aqq; work[q][q]=s*s*app+2*s*c*apq+c*c*aqq; work[p][q]=work[q][p]=0.0
        for k in range(n):
            vkp,vkq=vectors[k][p],vectors[k][q]; vectors[k][p]=c*vkp-s*vkq; vectors[k][q]=s*vkp+c*vkq
    return sorted(((work[j][j],[vectors[i][j] for i in range(n)]) for j in range(n)),reverse=True,key=lambda x:x[0])


def pcoa(dist: list[list[float]]) -> tuple[list[tuple[float, float]], list[float]]:
    n = len(dist); d2 = [[v*v for v in row] for row in dist]
    rowmean = [sum(row)/n for row in d2]; grand = sum(rowmean)/n
    b = [[-.5*(d2[i][j]-rowmean[i]-rowmean[j]+grand) for j in range(n)] for i in range(n)]
    eigen=symmetric_eigen(b); (l1,v1),(l2,v2)=eigen[:2]
    positive = sum(max(value,0) for value,_ in eigen)
    coords = [(v1[i]*math.sqrt(max(l1, 0)), v2[i]*math.sqrt(max(l2, 0))) for i in range(n)]
    return coords, ([l1/positive, l2/positive] if positive else [0, 0])


def cluster_order(dist: list[list[float]], target_clusters: int = 5) -> tuple[list[int], list[int]]:
    clusters = {i: [i] for i in range(len(dist))}; next_id = len(dist)
    assignments=[0]*len(dist)
    while len(clusters) > 1:
        if len(clusters)==target_clusters:
            for label,members in enumerate(sorted(clusters.values(),key=lambda x:min(x)),1):
                for member in members: assignments[member]=label
        ids = sorted(clusters); best = None
        for ai, a in enumerate(ids):
            for b in ids[ai+1:]:
                value = sum(dist[i][j] for i in clusters[a] for j in clusters[b])/(len(clusters[a])*len(clusters[b]))
                candidate = (value, a, b)
                if best is None or candidate < best: best = candidate
        assert best is not None
        _, a, b = best; clusters[next_id] = clusters.pop(a)+clusters.pop(b); next_id += 1
    return next(iter(clusters.values())), assignments


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__); out = [0.0]*len(values); i = 0
    while i < len(order):
        j = i+1
        while j < len(order) and values[order[j]] == values[order[i]]: j += 1
        rank = (i+j+1)/2
        for k in order[i:j]: out[k] = rank
        i = j
    return out


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = ranks(a), ranks(b); ma, mb = statistics.mean(ra), statistics.mean(rb)
    numerator = sum((x-ma)*(y-mb) for x, y in zip(ra, rb))
    denominator = math.sqrt(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))
    return numerator/denominator if denominator else 0.0


def correlation_permutation_p(a: list[float], b: list[float], observed: float, permutations: int, seed: int) -> float:
    rng = random.Random(seed); shuffled=b[:]; exceed=0
    for _ in range(permutations):
        rng.shuffle(shuffled); exceed += abs(spearman(a,shuffled)) >= abs(observed)-1e-12
    return (exceed+1)/(permutations+1)


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()


def kw(values: list[float], labels: list[str]) -> float:
    rs = ranks(values); groups: dict[str, list[float]] = defaultdict(list)
    for r, label in zip(rs, labels): groups[label].append(r)
    n = len(values)
    return 12/(n*(n+1))*sum(sum(v)**2/len(v) for v in groups.values())-3*(n+1)


def permutation_p(values: list[float], labels: list[str], observed: float, permutations: int, seed: int) -> float:
    rng = random.Random(seed); shuffled = labels[:]; exceed = 0
    for _ in range(permutations):
        rng.shuffle(shuffled)
        exceed += kw(values, shuffled) >= observed-1e-12
    return (exceed+1)/(permutations+1)


def bh(rows: list[dict[str, object]], key: str = "p_value") -> None:
    order = sorted(range(len(rows)), key=lambda i: float(rows[i][key])); q = 1.0; m = len(rows)
    for rank_index in range(m-1, -1, -1):
        idx = order[rank_index]; q = min(q, float(rows[idx][key])*m/(rank_index+1)); rows[idx]["q_value"] = q


def svg_scatter(path: Path, coords: list[tuple[float,float]], samples: list[str], groups: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#4477AA","#EE6677","#228833","#CCBB44","#66CCEE","#AA3377","#BBBBBB","#000000","#44AA99"]
    mapping = {g: colors[i % len(colors)] for i, g in enumerate(sorted(set(groups)))}
    xs=[x for x,_ in coords]; ys=[y for _,y in coords]
    def scale(v, lo, hi, a, b): return (a+b)/2 if hi==lo else a+(v-lo)*(b-a)/(hi-lo)
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650">','<rect width="100%" height="100%" fill="white"/>','<text x="50" y="35" font-size="22" font-family="sans-serif">HUMAnN pathway abundance PCoA (fixed selected n=30)</text>']
    for (x,y), sample, group in zip(coords,samples,groups):
        px=scale(x,min(xs),max(xs),70,680); py=scale(y,min(ys),max(ys),570,70)
        lines.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6" fill="{mapping[group]}"><title>{sample} | {group}</title></circle>')
    for i,(g,c) in enumerate(mapping.items()): lines.append(f'<circle cx="735" cy="{80+i*25}" r="6" fill="{c}"/><text x="750" y="{85+i*25}" font-size="13" font-family="sans-serif">{g}</text>')
    lines += ['<line x1="70" y1="570" x2="680" y2="570" stroke="#333"/>','<line x1="70" y1="70" x2="70" y2="570" stroke="#333"/>','</svg>']
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def svg_bars(path: Path, values: list[int], samples: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); maximum=max(values) if values else 1
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560">','<rect width="100%" height="100%" fill="white"/>','<text x="45" y="32" font-size="21" font-family="sans-serif">Detected unstratified pathways per sample</text>']
    for i,(sample,value) in enumerate(zip(samples,values)):
        x=50+i*30; height=430*value/maximum
        lines.append(f'<rect x="{x}" y="{490-height:.2f}" width="21" height="{height:.2f}" fill="#4477AA"><title>{sample}: {value}</title></rect>')
        lines.append(f'<text transform="translate({x+15},510) rotate(60)" font-size="8" font-family="sans-serif">{sample}</text>')
    lines.append('</svg>'); path.write_text("\n".join(lines)+"\n",encoding="utf-8")


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--input-root",required=True,type=Path); parser.add_argument("--cohort",required=True,type=Path); parser.add_argument("--audit-summary",required=True,type=Path); parser.add_argument("--species-matrix",required=True,type=Path); parser.add_argument("--out",required=True,type=Path); parser.add_argument("--min-prevalence",type=int,default=6); parser.add_argument("--permutations",type=int,default=199); args=parser.parse_args()
    audit=json.loads(args.audit_summary.read_text()); args.out.mkdir(parents=True,exist_ok=True)
    if not audit.get("audit_passed"):
        raise SystemExit("real hospital-side audit has not passed")
    cohort=read_tsv(args.cohort); samples=[r["run"] for r in cohort]; groups=[r["pathogen_group"] for r in cohort]
    if len(samples)!=30 or len(set(samples))!=30 or any(r.get("status")!="done" for r in cohort): raise SystemExit("fixed cohort/status gate failed")
    manifest=[]; normalized_by_kind={}; raw_by_kind={}
    for kind in KINDS:
        data={s:profile(args.input_root/s/f"{s}_{kind}.tsv") for s in samples}; raw_by_kind[kind]=data; universe=sorted(set().union(*(set(v) for v in data.values())))
        write_tsv(args.out/"joined"/f"{kind}.tsv.gz",matrix_rows(universe,samples,data),["feature",*samples])
        for stratum, features in (("unstratified",[f for f in universe if "|" not in f]),("stratified",[f for f in universe if "|" in f])):
            write_tsv(args.out/"joined"/f"{kind}_{stratum}.tsv.gz",matrix_rows(features,samples,data),["feature",*samples])
        norm=normalize({s:{f:v for f,v in data[s].items() if "|" not in f} for s in samples},kind); normalized_by_kind[kind]=norm
        kept=filtered_features(norm,samples,args.min_prevalence)
        write_tsv(args.out/"normalized"/f"{kind}_unstratified_filtered.tsv.gz",matrix_rows(kept,samples,norm),["feature",*samples])
        for p in sorted((args.out/"joined").glob(f"{kind}*"))+sorted((args.out/"normalized").glob(f"{kind}*")): manifest.append(p)
    sample_qc=[]
    for i,s in enumerate(samples):
        row=[s,groups[i]]
        for kind in KINDS:
            raw=raw_by_kind[kind][s]; vals=normalized_by_kind[kind][s]
            unstrat={f:v for f,v in raw.items() if "|" not in f}; strat={f:v for f,v in raw.items() if "|" in f}
            row += [len(raw),sum(v>0 for v in raw.values()),sum(unstrat.values()),sum(strat.values()),raw.get("UNMAPPED",0),raw.get("UNINTEGRATED",0),sum(vals.values())]
        sample_qc.append(row)
    write_tsv(args.out/"qc"/"sample_qc.tsv",sample_qc,["run","pathogen_group",*[f"{k}_{x}" for k in KINDS for x in ("features","detected","unstratified_total","stratified_total","unmapped","unintegrated","analysis_total")]])
    feature_qc=[]
    for kind in KINDS:
        norm=normalized_by_kind[kind]; universe=sorted(set().union(*(set(v) for v in norm.values())))
        contributor_sets: dict[str, set[str]] = defaultdict(set)
        for sample_raw in raw_by_kind[kind].values():
            for stratified_feature in sample_raw:
                if "|" in stratified_feature:
                    base, taxon = stratified_feature.split("|", 1); contributor_sets[base].add(taxon)
        for f in universe:
            vals=[norm[s].get(f,0) for s in samples]
            contributors=len(contributor_sets.get(f,set())) if "|" not in f else 0
            feature_qc.append([kind,f,sum(v>0 for v in vals),statistics.mean(vals),statistics.median(vals),max(vals),statistics.pvariance(vals),sum(v==0 for v in vals)/30,contributors])
    write_tsv(args.out/"qc"/"feature_qc.tsv.gz",feature_qc,["kind","feature","prevalence","mean","median","max","variance","zero_fraction","taxonomic_contributors"])
    data=normalized_by_kind["pathabundance"]; feats=filtered_features(data,samples,args.min_prevalence); vectors=[[data[s].get(f,0) for f in feats] for s in samples]
    distances=[[bray(a,b) for b in vectors] for a in vectors]; write_tsv(args.out/"statistics"/"bray_curtis.tsv",([samples[i],*(format(x,'.10g') for x in distances[i])] for i in range(30)),["run",*samples])
    coords, explained=pcoa(distances); write_tsv(args.out/"statistics"/"pcoa.tsv",([samples[i],groups[i],coords[i][0],coords[i][1]] for i in range(30)),["run","pathogen_group","PCoA1","PCoA2"])
    order,assignments=cluster_order(distances); write_tsv(args.out/"statistics"/"cluster_order.tsv",([rank+1,samples[i],groups[i],assignments[i]] for rank,i in enumerate(order)),["order","run","pathogen_group","average_linkage_cluster_k5"])
    svg_scatter(args.out/"figures"/"pathabundance_pcoa.svg",coords,samples,groups)
    svg_bars(args.out/"figures"/"detected_pathways.svg",[sum(data[s].get(f,0)>0 for f in feats) for s in samples],samples)
    eligible={g for g in set(groups) if groups.count(g)>=3}; selected=sorted(feats,key=lambda f:statistics.pvariance([data[s].get(f,0) for s in samples]),reverse=True)[:200]; diff=[]
    labels=[g if g in eligible else "Other_lt3" for g in groups]
    for n,f in enumerate(selected):
        vals=[data[s].get(f,0) for s in samples]; h=kw(vals,labels); diff.append({"feature":f,"H":h,"p_value":permutation_p(vals,labels,h,args.permutations,1000+n)})
    bh(diff); write_tsv(args.out/"statistics"/"pathogen_group_pathway_exploration.tsv",([r["feature"],r["H"],r["p_value"],r["q_value"]] for r in diff),["feature","kruskal_wallis_H","permutation_p","BH_q"])
    species=read_tsv(args.species_matrix); smap={r["run"]:r for r in species}; columns=[c for c in species[0] if c not in ("run","pathogen_group")]; assoc=[]
    for gi,group in enumerate(sorted(eligible)):
        aliases={"Enterobacterales":("escherichia","klebsiella","enterobacter","serratia","citrobacter"),"Mycobacteria":("mycobacter",),"Haemophilus":("haemophilus",)}
        terms=aliases.get(group,(group.lower(),)); matches=[c for c in columns if any(term in c.lower() for term in terms)]
        burden=[sum(float(smap[s].get(c,0) or 0) for c in matches) for s in samples]
        group_rows=[]
        for fi,f in enumerate(selected):
            function=[data[s].get(f,0) for s in samples]; rho=spearman(burden,function); p=correlation_permutation_p(burden,function,rho,args.permutations,50000+gi*1000+fi)
            group_rows.append({"pathogen_group":group,"pathway":f,"rho":rho,"p_value":p,"matches":len(matches),"features":";".join(matches)})
        bh(group_rows); assoc.extend(group_rows)
    write_tsv(args.out/"statistics"/"pathogen_function_spearman.tsv",([r["pathogen_group"],r["pathway"],r["rho"],r["p_value"],r["q_value"],r["matches"],r["features"]] for r in assoc),["pathogen_group","pathway","spearman_rho","permutation_p","BH_q_within_group","matched_species_features","species_features"])
    sensitivity=[]
    for fraction in (.1,.2,.3):
        threshold=math.ceil(30*fraction)
        for kind in KINDS: sensitivity.append([kind,fraction,threshold,len(filtered_features(normalized_by_kind[kind],samples,threshold))])
    write_tsv(args.out/"qc"/"filter_sensitivity.tsv",sensitivity,["kind","minimum_prevalence_fraction","minimum_samples","retained_unstratified_features"])
    params={"generated_at":now(),"cohort_n":30,"scope":"selected_deep_review_only","command":sys.argv,"python":sys.version.split()[0],"min_prevalence_samples":args.min_prevalence,"filter_sensitivity_fractions":[.1,.2,.3],"permutations":args.permutations,"ordination":"Bray-Curtis classical PCoA","clustering":"average_linkage","pcoa_explained_first_two":explained,"audit_summary":str(args.audit_summary),"input_root":str(args.input_root),"interpretation":"Exploratory only; no inference to the approximately 400-run parent cohort."}
    (args.out/"parameters.json").write_text(json.dumps(params,indent=2)+"\n")
    (args.out/"summary.md").write_text("# Fixed-30 HUMAnN exploratory downstream summary\n\nReal hospital-side audit passed before analysis. Outputs cover joined matrices, stratification, normalization/filtering, QC, ordination/clustering, pathogen-group exploration, and pathogen-function correlations.\n\nAll findings are selective deep-review hypotheses restricted to these 30 samples and must not be extrapolated to the approximately 400-run parent cohort.\n")
    checks=[]
    for p in sorted(x for x in args.out.rglob('*') if x.is_file() and x.name!='checksums.tsv'):
        checks.append([sha256_file(p),str(p.relative_to(args.out)),p.stat().st_size])
    write_tsv(args.out/"checksums.tsv",checks,["sha256","path","bytes"])
    return 0

if __name__=="__main__": raise SystemExit(main())
