import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_530_pathogen_profile_formal as formal
from scripts.etty_bounded_job import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "automation/production/20260905T180000Z-0714-real-530-pathogen-profile-formal-analysis.json"


class PathogenProfileFormalTests(unittest.TestCase):
    def test_frozen_panel_and_threshold_contract(self):
        contract, panel = formal.load_contract()
        self.assertEqual(contract["primary_threshold_direct_assigned_reads_greater_or_equal"], 5)
        self.assertEqual(contract["sensitivity_thresholds_direct_assigned_reads_greater_or_equal"], [1, 10])
        self.assertEqual(len([row for row in panel if row["category"] == "A"]), 6)
        self.assertEqual(len([row for row in panel if row["category"] == "B"]), 4)
        self.assertEqual(len([row for row in panel if row["category"] == "S"]), 1)

    def test_bh_and_holm(self):
        for observed, expected in zip(formal.adjust_bh([0.01, 0.04, 0.2]), [0.03, 0.06, 0.2]):
            self.assertAlmostEqual(observed, expected)
        for observed, expected in zip(formal.adjust_holm([0.01, 0.04, 0.2]), [0.03, 0.08, 0.2]):
            self.assertAlmostEqual(observed, expected)

    def test_r_environment_preserves_system_path(self):
        with patch.dict("os.environ", {"PATH": "/usr/bin:/bin"}, clear=False):
            env = formal.r_environment()
        self.assertTrue(env["PATH"].startswith(formal.MGSHOTGUN_BIN + ":"))
        self.assertIn("/usr/bin", env["PATH"])
        self.assertIn("/bin", env["PATH"])

    def test_source_has_no_abandoned_analysis_calls(self):
        source = Path(formal.__file__).read_text()
        for token in ("cmultRepl(", "clr_transform(", "aitchison_distance(", "ANCOMBC", "ALDEx2("):
            self.assertNotIn(token, source)

    def test_job_is_zero_download_and_bounded(self):
        job = json.loads(DEFINITION.read_text())
        with patch("scripts.etty_bounded_job.confined", side_effect=lambda path, roots: Path(path)):
            validate_manifest(job)
        self.assertFalse(job["acquire"])
        self.assertFalse(job["network_acquisition"])
        self.assertFalse(job["package_installation"])
        self.assertFalse(job["pooled_530_model"])
        self.assertFalse(job["czm"])
        self.assertFalse(job["clr_aitchison"])
        self.assertEqual(job["primary_threshold_reads"], 5)
        self.assertEqual(job["sensitivity_thresholds"], [1, 10])
        self.assertTrue(all(Path(name).suffix in {".json", ".md", ".txt"} for name in job["handoff_allowlist"]))


if __name__ == "__main__":
    unittest.main()
