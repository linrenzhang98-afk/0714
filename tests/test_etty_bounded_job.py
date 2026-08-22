import json,tempfile,unittest
from pathlib import Path
from scripts.etty_bounded_job import JobError,validate_manifest
class Generic(unittest.TestCase):
 def base(self): return {'authorized':True,'allowed_hosts':['example.test'],'transfer_cap_bytes':10,'items':[{'id':'a','url':'https://example.test/a','destination':'/tmp/a','expected_bytes':5}]}
 def test_host(self):
  m=self.base(); m['items'][0]['url']='https://evil.test/a'; self.assertRaises(JobError,validate_manifest,m)
 def test_duplicate_destination(self):
  m=self.base(); m['items'].append({'id':'b','url':'https://example.test/b','destination':'/tmp/a','expected_bytes':1}); self.assertRaises(JobError,validate_manifest,m)
 def test_cap(self):
  m=self.base(); m['items'][0]['expected_bytes']=11; self.assertRaises(JobError,validate_manifest,m)
 def test_unauthorized(self):
  m=self.base(); m['authorized']=False; self.assertRaises(JobError,validate_manifest,m)
 def test_valid(self): validate_manifest(self.base())
if __name__=='__main__': unittest.main()
