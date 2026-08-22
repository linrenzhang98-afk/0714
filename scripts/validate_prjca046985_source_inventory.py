#!/usr/bin/env python3
import json,re,sys
p=json.load(open(sys.argv[1])); s=json.load(open(sys.argv[2])); f=[]
if s.get('status')!='SOURCE_INVENTORY_COMPLETE' or s.get('eligible_count')!=122 or s.get('present_count')!=122 or s.get('missing_count')!=0 or s.get('byte_mismatch_count')!=0 or s.get('duplicate_accession_count')!=0 or s.get('duplicate_path_count')!=0 or s.get('sha256_count')!=122 or s.get('new_downloaded_bytes')!=0:f.append('summary invariant')
if len(p.get('runs',[]))!=122:f.append('run count')
for r in p.get('runs',[]):
 if r.get('status')!='OK' or r.get('actual_bytes')!=r.get('expected_bytes') or not re.fullmatch('[0-9a-f]{64}',r.get('sha256','')) or not r.get('source_path','').startswith('/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq/'): f.append(r.get('run_accession','invalid'))
if f: print('\n'.join(f),file=sys.stderr); sys.exit(1)
print('VALID_SOURCE_INVENTORY')
