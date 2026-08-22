import json, tempfile, unittest
from pathlib import Path
class HandoffChannelTest(unittest.TestCase):
 def test_policy_and_allowlist(self):
  p=json.loads(Path('automation/standing_authorization.json').read_text())['ETYY_HANDOFF_WRITER_POLICY']
  self.assertEqual(p['branch'],'etty-handoff'); self.assertFalse(p['main_write']); self.assertFalse(p['force_push']); self.assertFalse(p['raw_data'])
 def test_publisher_has_guards(self):
  text=Path('scripts/publish_etty_handoff.py').read_text()
  for token in ('ALLOWED','CAP','etty-handoff','PRIVATE KEY','ALREADY_PUBLISHED','"add"','"push"'):
   self.assertIn(token,text)
 def test_ingest_verifies_hashes(self):
  self.assertIn('sha256',Path('scripts/ingest_etty_handoff.py').read_text())
if __name__=='__main__': unittest.main()
