import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "research_supervisor_console", ROOT / "scripts/research_supervisor_console.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class SupervisorConsoleParsingTests(unittest.TestCase):
    def test_parse_key_values(self):
        parsed = MOD.parse_key_values("state=running\nroute=short_read_shared_index\nreason=a=b\n")
        self.assertEqual(parsed["state"], "running")
        self.assertEqual(parsed["route"], "short_read_shared_index")
        self.assertEqual(parsed["reason"], "a=b")

    def test_pending_decision_requires_marker_or_ask(self):
        legacy = "# Requirements\nThis is an informational historical note.\n"
        self.assertFalse(MOD.is_pending_decision(legacy, "decision_requests/old.md"))
        self.assertTrue(MOD.is_pending_decision("status: pending\nNeed approval", "decision_requests/x.md"))
        self.assertTrue(MOD.is_pending_decision("Decision: ASK_USER", "decision_requests/x.md"))
        self.assertTrue(MOD.is_pending_decision("plain text", "decision_requests/ask_expand_400.md"))

    def test_ask_user_detection(self):
        self.assertTrue(MOD.contains_ask_user("decision=ASK_USER"))
        self.assertTrue(MOD.contains_ask_user("ACTION REQUIRED"))
        self.assertFalse(MOD.contains_ask_user("decision=CONTINUE"))

    def test_compact(self):
        self.assertEqual(MOD.compact(" a   b \n c "), "a b c")
        self.assertEqual(MOD.compact("123456", 5), "12...")


if __name__ == "__main__":
    unittest.main()
