import json,tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts.etty_job_agent import _bounded_job,envelope,failure_payload,queue_entries
from scripts.etty_bounded_job import JobError
class AgentContract(unittest.TestCase):
 def base(self): return {'schema_version':1,'job_id':'j','authorized':True,'authorization_record':'review','execution_commit':'0123456789abcdef0123456789abcdef01234567','job_definition_path':'job.json','job_definition_sha256':'a'*64,'transfer_cap_bytes':10,'allowed_source_hosts':['example.test'],'allowed_destination_roots':['/tmp'],'resource_caps':{'wall_seconds':1},'handoff_allowlist':['result.json']}
 def test_valid_envelope(self): envelope(self.base())
 def test_head_rejected(self):
  x=self.base(); x['execution_commit']='HEAD'; self.assertRaises(JobError,envelope,x)
 def test_unauthorized_rejected(self):
  x=self.base(); x['authorized']=False; self.assertRaises(JobError,envelope,x)
 def test_definition_traversal_rejected(self):
  x=self.base(); x['job_definition_path']='../job.json'; self.assertRaises(JobError,envelope,x)
 def test_missing_schema_rejected(self):
  x=self.base(); del x['handoff_allowlist']; self.assertRaises(JobError,envelope,x)
 def test_resource_scope_expansion_rejected(self):
  e=self.base(); e['resource_caps']={'allowed_executables':['/bin/true'],'allowed_working_roots':['/tmp'],'allowed_environment_keys':[],'wall_seconds':2}
  job={'authorized':True,'allowed_hosts':['example.test'],'allowed_destination_roots':['/tmp'],'transfer_cap_bytes':10,'allowed_executables':['/bin/false'],'allowed_working_roots':['/tmp'],'allowed_environment_keys':[],'wall_seconds':2,'items':[]}
  self.assertRaises(JobError,_bounded_job,job,e)
 def test_queue_discovery_ignores_readme_and_non_json(self):
  listing='automation/etty_jobs/README.md\nautomation/etty_jobs/good.json\nautomation/etty_jobs/note.txt\nautomation/etty_jobs/nested/bad.json\n'
  with mock.patch('subprocess.check_output',return_value=listing):
   self.assertEqual(queue_entries(Path('/tmp/repo')),['automation/etty_jobs/good.json'])
 def test_failure_payload_is_bounded_and_non_sensitive(self):
  with tempfile.TemporaryDirectory() as raw:
   state=Path(raw)/'acquisition.json'; state.write_text(json.dumps({'network_bytes':7,'items':{'done':{'status':'done'},'failed':{'status':'transient_failed'}}}))
   payload=failure_payload('job',{'items':[{},{}]},state,'acquisition',JobError('temporary '+('x'*1000)))
   self.assertEqual(payload['status'],'SAFE_STOP'); self.assertEqual(payload['completed_items'],1); self.assertEqual(payload['failed_item_ids'],['failed']); self.assertLessEqual(len(payload['error']),500)
if __name__=='__main__': unittest.main()
