#!/usr/bin/env python3
import json,sys
p=json.load(open(sys.argv[1])); j=p['job']; m=j['method']; f=[]
if p['counts']['remaining_planned']!=len(j['run_allowlist']): f.append('count mismatch')
if m.get('threads')!=4 or m.get('confidence')!=0.0 or m.get('minimum_hit_groups')!=2: f.append('parameter pins')
if m.get('trimming') or m.get('host_filtering') or m.get('bracken') or m.get('biological_inference'): f.append('prohibited method')
if m.get('database_identity')!='6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3': f.append('DB identity')
if p.get('local_presence_verified') or p.get('download_requirement')!='NOT_ESTABLISHED; no execution authorized': f.append('unsafe authorization state')
if f: print('\n'.join(f),file=sys.stderr); sys.exit(1)
print('VALID_PLAN')
