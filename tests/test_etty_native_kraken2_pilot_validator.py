import json, subprocess, sys
from pathlib import Path
SCRIPT=Path(__file__).parents[1]/"scripts/validate_etty_native_kraken2_pilot.py"
def test_validator_rejects_missing_inputs(tmp_path):
 for n in ("job","state","summary"):
  (tmp_path/n).write_text("{}")
 p=subprocess.run([sys.executable,str(SCRIPT),"--job",str(tmp_path/"job"),"--state",str(tmp_path/"state"),"--summary",str(tmp_path/"summary"),"--live-db","x"],capture_output=True,text=True)
 assert p.returncode != 0
 assert "runner.status" in p.stderr
