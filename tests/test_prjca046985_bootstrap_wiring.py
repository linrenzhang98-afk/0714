import unittest
from pathlib import Path
class BootstrapWiring(unittest.TestCase):
 def test_resolves_and_passes_pilot_job(self):
  s=(Path(__file__).parents[1]/'scripts/bootstrap_etty_prjca046985_source_inventory.sh').read_text()
  self.assertIn('INVENTORY_JOB=',s); self.assertIn('PILOT_JOB_REL=',s); self.assertIn('PILOT_JOB="$R/$PILOT_JOB_REL"',s)
  self.assertIn('"$R/scripts/inventory_prjca046985_sources.py" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$H" "$PILOT_JOB"',s)
  self.assertIn('"$H/provenance.json" "$R/reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_exact_manifest.tsv" "$PILOT_JOB"',s)
  self.assertNotIn('"$R/jobs/20260822T160000Z-prjca046985-source-inventory.json"; "$PY" "$R/scripts/validate',s)
if __name__=='__main__': unittest.main()
