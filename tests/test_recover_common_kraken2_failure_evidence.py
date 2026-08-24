import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/recover_common_kraken2_failure_evidence.py"
JOB = "20260823T110000Z-prjna1056765-prjca046985-common-kraken2-layer-diagnostic"


def make_state(root: Path, diagnostic: bool = True) -> None:
    (root / f"{JOB}-handoff").mkdir()
    (root / f"{JOB}.execution.json").write_text(json.dumps({"items": {
        "CRR2423908": {"id": "CRR2423908", "status": "failed", "returncode": 1,
        "stdout_tail": "o" * 5001, "stderr_tail": "e" * 5002, "started_at": "s",
        "finished_at": "f", "command_hash": "h", "command": ["excluded"]}}}), encoding="utf-8")
    if diagnostic:
        (root / f"{JOB}-handoff/diagnostic.json").write_text(json.dumps({
            "stage": "parse", "exception_type": "ValueError", "exception_message": "m" * 5003,
            "traceback": "t" * 5004, "first_failing_path_if_any": "p", "first_failing_run_if_any": "r",
            "expected_path": "e", "observed_path": "o", "source_gate_status": "FAIL"}), encoding="utf-8")
        (root / f"{JOB}-handoff/diagnostic.txt").write_text("corroboration", encoding="utf-8")


class RecoveryTests(unittest.TestCase):
    def run_recovery(self, diagnostic: bool = True):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        state = root / "state"
        state.mkdir()
        make_state(state, diagnostic)
        out = root / "out"
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--state-root", str(state), "--output-dir", str(out)],
            check=False,
        )
        result = json.loads((out / "recovered_failure_evidence.json").read_text(encoding="utf-8"))
        return temporary, process, result

    def test_execution_state_and_diagnostic_present_and_bounded(self):
        temporary, process, result = self.run_recovery()
        self.addCleanup(temporary.cleanup)
        self.assertEqual(process.returncode, 0)
        self.assertTrue(result["diagnostic_json_present"])
        self.assertTrue(result["diagnostic_txt_present"])
        self.assertEqual(len(result["execution"]["stdout_tail"]), 4000)
        self.assertEqual(len(result["execution"]["stderr_tail"]), 4000)
        self.assertEqual(len(result["diagnostic"]["exception_message"]), 4000)
        self.assertEqual(len(result["diagnostic"]["traceback"]), 4000)
        self.assertEqual(result["execution"]["job_item_id"], "CRR2423908")
        self.assertEqual(result["execution"]["command_hash"], "h")

    def test_diagnostic_absent_still_exits_successfully(self):
        temporary, process, result = self.run_recovery(False)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(process.returncode, 0)
        self.assertTrue(result["execution_state_present"])
        self.assertFalse(result["diagnostic_json_present"])
        self.assertEqual(result["execution"]["status"], "failed")
        self.assertEqual(
            result["inference"]["likely_root_cause"],
            "command returned nonzero; specific cause not identified by recovered evidence",
        )

    def test_source_has_no_recursive_scan_network_or_parser(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("rglob", "os.walk", "requests", "urllib", "build_common_kraken2_assignment_layer"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
