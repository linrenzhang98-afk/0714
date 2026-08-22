import csv,json,tempfile,unittest
from pathlib import Path
import importlib.util
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('inv',ROOT/'scripts/inventory_prjca046985_sources.py'); inv=importlib.util.module_from_spec(spec); spec.loader.exec_module(inv)
class InventoryRuntime(unittest.TestCase):
 def make(self,n=130):
  td=tempfile.TemporaryDirectory(); d=Path(td.name); m=d/'m.tsv';
  with m.open('w') as f:
   f.write('run_accession\tcompressed_bytes\tgroup_raw\n');
   for i in range(n): f.write(f'R{i:03d}\t3\tg\n')
  j=d/'j.json'; json.dump({'params':{'pilot_runs':[{'run_accession':f'R{i:03d}'} for i in range(8)]}},j.open('w')); return td,m,j
 def test_list_dict_and_exact_remaining(self):
  td,m,j=self.make(); self.assertEqual(len(inv.inputs(m,j)),122); td.cleanup()
 def test_wrong_pilot_fails(self):
  td,m,j=self.make(); x=json.load(j.open()); x['params']['pilot_runs'][0]={'run_accession':'BAD'}; json.dump(x,j.open('w')); self.assertRaises(ValueError,inv.inputs,m,j); td.cleanup()
 def test_duplicate_canonical_fails(self):
  td,m,j=self.make(); withm=m.read_text().replace('R129\t3','R000\t3'); m.write_text(withm); self.assertRaises(ValueError,inv.inputs,m,j); td.cleanup()
 def test_pilot_count_is_eight(self):
  td,m,j=self.make(); x=json.load(j.open()); x['params']['pilot_runs']=x['params']['pilot_runs'][:7]; json.dump(x,j.open('w')); self.assertRaises(ValueError,inv.inputs,m,j); td.cleanup()
 def test_bootstrap_has_no_legacy_orphan(self):
  s=(ROOT/'scripts/bootstrap_etty_prjca046985_source_inventory.sh').read_text(); self.assertNotIn('--orphan',s); self.assertNotIn('kraken2',s.lower()); self.assertNotIn('curl ',s)
if __name__=='__main__': unittest.main()
