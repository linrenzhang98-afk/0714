import json,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]; CAN='/mnt/disk1/db/kraken2/0714/results/20260821T150000Z-prjca046985-read-length-audit/fastq'
class Root(unittest.TestCase):
 def test_manifest_roots(self):
  d=json.load(open(ROOT/'reports_public/prjca046985_external_cohort_pilot_package/manifests/PRJCA046985_122_acquisition_manifest.json')); e=d['entries']; self.assertEqual(len(e),122); self.assertEqual(len({x['run_accession'] for x in e}),122); self.assertEqual(len({x['destination_path'] for x in e}),122)
  for x in e: self.assertEqual(Path(x['destination_path']).parent.as_posix(),CAN); self.assertEqual(Path(x['destination_path']).name,x['run_accession']+'.fq.gz')
 def test_no_new_timestamp_root(self):
  for p in [ROOT/'reports_public/prjca046985_external_cohort_pilot_package/acquisition_plan.json',ROOT/'scripts/inventory_prjca046985_sources.py']:
   self.assertNotIn('20260822T150000Z-prjca046985-read-length-audit',p.read_text())
if __name__=='__main__': unittest.main()
