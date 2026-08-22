#!/usr/bin/env python3
import json,sys
p=json.load(open(sys.argv[1])); j=p['job']; m=j['method']; f=[]
if len(j['run_allowlist'])!=122 or any(r.get('sha256') is None for r in j['run_allowlist']): f.append('122 frozen SHA256 values required')
if not j.get('local_presence_verified') or j.get('new_downloaded_bytes')!=0 or j.get('download_requirement')!='ZERO': f.append('local zero-download inventory required')
if m.get('kraken2_version')!='2.17.1' or m.get('database_identity')!='6feb9b3e8b52ff05d61272436bbbacc4f3408088dc6e776cd44d588169d496d3' or m.get('threads')!=4 or m.get('confidence')!=0.0 or m.get('minimum_hit_groups')!=2: f.append('method identity/pins')
if any(m.get(x) for x in ('trimming','host_filtering','bracken','biological_inference')): f.append('prohibited method')
if f: print('\n'.join(f),file=sys.stderr); sys.exit(1)
print('VALID_PRODUCTION_MANIFEST')
