import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
CLASS=ROOT/'scripts/classify_etty_pilot_attempt.py'

class RecoveryContractTest(unittest.TestCase):
 def test_zero_execution_classification(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/'state').mkdir(); (root/'logs').mkdir(); (root/'results').mkdir()
   (root/'state/runner_state.json').write_text(json.dumps({'jobs':{'20260822T120000Z-prjca046985-native-kraken2-pilot':{'status':'failed','returncode':2}}}))
   out=subprocess.check_output(['python3',str(CLASS),str(root)],text=True)
   self.assertEqual(json.loads(out)['classification'],'PRE_EXECUTION_FAILURE_ZERO_KRAKEN2')
 def test_partial_and_unknown_do_not_classify_zero(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/'state').mkdir(); (root/'logs').mkdir(); (root/'results').mkdir()
   (root/'state/runner_state.json').write_text(json.dumps({'jobs':{'20260822T120000Z-native-kraken2-pilot':{'status':'failed'}}}))
   self.assertEqual(json.loads(subprocess.check_output(['python3',str(CLASS),str(root)],text=True))['classification'],'UNKNOWN')
   (root/'results/20260822T120000Z-prjca046985-native-kraken2-pilot').mkdir()
   (root/'results/20260822T120000Z-prjca046985-native-kraken2-pilot/x.kraken2.out').write_text('started')
   self.assertEqual(json.loads(subprocess.check_output(['python3',str(CLASS),str(root)],text=True))['classification'],'PARTIAL_EXECUTION')

if __name__=='__main__': unittest.main()
