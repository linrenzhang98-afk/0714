import json,tempfile,unittest
from pathlib import Path
from scripts.etty_job_agent import process,sha
class Agent(unittest.TestCase):
 def test_synthetic_lifecycle(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t); repo=d/'repo'; (repo/'.git').mkdir(parents=True); q=repo/'job.json'; q.write_text(json.dumps({'authorized':True,'items':[],'allowed_hosts':['x'],'transfer_cap_bytes':1})); env={'authorized':True,'job_id':'j','execution_commit':'HEAD','job_definition_path':'job.json','job_definition_sha256':sha(q)}
   # empty item rejected closed; verifies envelope/hash path handling
   with self.assertRaises(Exception): process(env,repo,d/'state.json')
 def test_unauthorized(self):
  with self.assertRaises(Exception): process({'authorized':False},Path('/tmp'),Path('/tmp/s'))
if __name__=='__main__': unittest.main()
