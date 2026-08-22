#!/usr/bin/env python3
import hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
JOB='20260822T160000Z-prjca046985-source-inventory'; ALLOWED={'STATUS.txt','source_inventory.json','source_inventory_summary.json','provenance.json'}; CAP=5*1024*1024
def die(x): raise SystemExit('SAFE_STOP: '+x)
src,repo=Path(sys.argv[1]),Path(sys.argv[2]); branch=subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip();
if branch!='etty-handoff' or subprocess.check_output(['git','-C',str(repo),'remote','get-url','origin'],text=True).strip()!='git@github.com:linrenzhang98-afk/0714.git': die('branch/remote')
if (src/'STATUS.txt').read_text().strip()!='STATUS=SOURCE_INVENTORY_COMPLETE': die('inventory incomplete')
for x in ALLOWED:
 if not (src/x).is_file(): die('missing '+x)
total=sum((src/x).stat().st_size for x in ALLOWED)
if total>CAP: die('size cap')
manifest={'job_id':JOB,'target_branch':'etty-handoff','files':{x:hashlib.sha256((src/x).read_bytes()).hexdigest() for x in sorted(ALLOWED)},'total_bytes':total,'sensitivity_classification':'non-sensitive'}; dest=repo/'handoffs'/JOB
if (dest/'manifest.json').exists(): die('ALREADY_PUBLISHED' if json.loads((dest/'manifest.json').read_text()).get('files')==manifest['files'] else 'provenance conflict')
dest.mkdir(parents=True,exist_ok=True); (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for x in ALLOWED: shutil.copy2(src/x,dest/x)
subprocess.run(['git','-C',str(repo),'add','--','handoffs/'+JOB],check=True); subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','Publish PRJCA046985 source inventory'],check=True); subprocess.run(['git','-C',str(repo),'push','origin','etty-handoff'],check=True)
