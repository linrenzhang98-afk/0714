import unittest
from pathlib import Path
class CommitPin(unittest.TestCase):
 def test_bootstrap_preserves_caller_head(self):
  s=(Path(__file__).parents[1]/'scripts/bootstrap_etty_prjca046985_source_inventory.sh').read_text()
  self.assertIn('BOOTSTRAP_COMMIT="$(git -C "$B" rev-parse HEAD)"',s)
  self.assertIn('CONTROL_MAIN_COMMIT="$BOOTSTRAP_COMMIT"',s)
  self.assertNotIn('checkout --detach origin/main',s)
  self.assertIn('checkout --detach "$CONTROL_MAIN_COMMIT"',s)
if __name__=='__main__': unittest.main()
