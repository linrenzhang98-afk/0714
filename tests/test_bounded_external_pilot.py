import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deep_runner", ROOT / "pipelines/metagenome_deep_review_runner.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BoundedExternalPilotTests(unittest.TestCase):
    def test_frozen_job_scope(self):
        job = json.loads((ROOT / "jobs/20260821T100000Z-prjca046985-bounded-technical-pilot.json").read_text())
        params = job["params"]
        self.assertEqual(params["execute_mode"], "bounded_external_pilot")
        self.assertEqual({row["run_accession"] for row in params["pilot_runs"]}, {"CRR2423962", "CRR2423909"})
        self.assertEqual(sum(row["expected_bytes"] for row in params["pilot_runs"]), 10_526_255)
        self.assertEqual(params["maximum_download_bytes"], 10_526_255)
        self.assertFalse(params["host_filtering"])
        self.assertTrue(all(row["host_status"] == "HOST_DEPLETED" for row in params["pilot_runs"]))

    def test_workspace_watchdog_terminates_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = ["/bin/bash", "-c", f"dd if=/dev/zero of='{root / 'growth'}' bs=1M count=2 status=none; sleep 5"]
            result = MODULE.run_bounded_command(command, root / "command.log", root, 1024, time.monotonic() + 10, 256 * 1024**2)
            self.assertEqual(result["stop_reason"], "workspace cap exceeded during command")
            self.assertNotEqual(result["returncode"], 0)

    def test_wall_watchdog_terminates_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = MODULE.run_bounded_command(["/bin/sleep", "5"], root / "command.log", root, 1024**2, time.monotonic() + 1, 256 * 1024**2)
            self.assertEqual(result["stop_reason"], "total wall-time cap reached during command")
            self.assertNotEqual(result["returncode"], 0)

    def test_address_space_limit_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = ["/usr/bin/python3", "-c", "x=bytearray(256*1024*1024)"]
            result = MODULE.run_bounded_command(command, root / "command.log", root, 1024**2, time.monotonic() + 10, 64 * 1024**2)
            self.assertNotEqual(result["returncode"], 0)

    def test_partial_retry_never_exceeds_cumulative_budget(self):
        class BrokenResponse:
            headers = {"Content-Length": "10"}

            def __init__(self, url):
                self.url = url
                self.calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def geturl(self):
                return self.url

            def read(self, _):
                self.calls += 1
                if self.calls == 1:
                    return b"123456"
                raise OSError("truncated transfer")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            budget = {"consumed": 0, "maximum": 10}
            url = "https://example.invalid/frozen.fastq.gz"
            with mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=lambda *_args, **_kwargs: BrokenResponse(url)):
                with self.assertRaises(RuntimeError):
                    MODULE.bounded_download(url, root / "frozen.fastq.gz", 10, budget, 2, root, 1024**2, time.monotonic() + 10)
            self.assertLessEqual(budget["consumed"], 10)


if __name__ == "__main__":
    unittest.main()
