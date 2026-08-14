#!/usr/bin/env python3
"""Continuous temporal/technical diagnostics for completed 400-run ordinations."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from analyze_prjna1056765_metagenome_400 import bh, ranks, read_tsv, write_tsv


def spearman(a,b):
    ra,rb=ranks(a),ranks(b);ma=sum(ra)/len(ra);mb=sum(rb)/len(rb);num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb));den=math.sqrt(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb));return num/den if den else 0


def permute_within(values,strata,rng):
    out=values[:];groups=defaultdict(list)
    for i,s in enumerate(strata):groups[s].append(i)
    for ids in groups.values():
        v=[out[i] for i in ids];rng.shuffle(v)
        for i,x in zip(ids,v):out[i]=x
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("reports_public/metagenome_400_formal"));p.add_argument("--clinical",type=Path,default=Path("reports_public/prjna1056765_clinical_groups/run_clinical_mapping.tsv"));p.add_argument("--qc",type=Path,default=Path("reports_public/metagenome_production/run_qc_summary.tsv"));p.add_argument("--permutations",type=int,default=9999);args=p.parse_args();clinical={x["run"]:x for x in read_tsv(args.clinical)};qc={x["run"]:x for x in read_tsv(args.qc)};results=[]
    for metric,file in (("Bray-Curtis","bray_pcoa.tsv"),("Aitchison","aitchison_pcoa.tsv")):
        ordination=read_tsv(args.root/"beta"/file);runs=[x["run"] for x in ordination];strata=[clinical[x]["cohort"] for x in runs];variables={"collection_date_ordinal":[datetime.strptime(clinical[x]["collection_date"],"%Y%m%d").toordinal() for x in runs],"log10_total_reads":[math.log10(float(qc[x]["total_reads"])) for x in runs]}
        for vi,(variable,values) in enumerate(variables.items()):
            for axis in range(1,6):
                coords=[float(x[f"PCoA{axis}"]) for x in ordination];observed=spearman(values,coords);rng=random.Random(1056765+vi*100+axis+(0 if metric=="Bray-Curtis" else 1000));exceed=0
                for _ in range(args.permutations):exceed+=abs(spearman(permute_within(values,strata,rng),coords))>=abs(observed)-1e-15
                results.append({"metric":metric,"variable":variable,"axis":axis,"rho":observed,"p_value":(exceed+1)/(args.permutations+1),"permutations":args.permutations,"constraint":"within published Training/Test cohort","evidence_class":"temporal/technical sensitivity diagnostic"})
    bh(results);write_tsv(args.root/"statistics/continuous_metadata_pcoa_associations.tsv",([x["metric"],x["variable"],x["axis"],x["rho"],x["p_value"],x["q_value"],x["permutations"],x["constraint"],x["evidence_class"]] for x in results),["metric","continuous_variable","axis","spearman_rho","permutation_p","BH_q","permutations","permutation_constraint","evidence_class"]);(args.root/"methods/continuous_metadata_parameters.json").write_text(json.dumps({"permutations":args.permutations,"axes":5,"metrics":["Bray-Curtis","Aitchison"],"variables":["collection_date_ordinal","log10_total_reads"],"interpretation":"technical/temporal diagnostic, not disease inference"},indent=2)+"\n");return 0


if __name__=="__main__":raise SystemExit(main())
