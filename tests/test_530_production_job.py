import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.etty_bounded_job import validate_manifest
from shotgun_analysis.production_package import validate_pinned_czm_gate

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "automation/production/20260904T120000Z-0714-real-530-balf-beta-diversity-production.json"


class Real530ProductionJobTests(unittest.TestCase):
    def test_definition_is_bounded_and_zero_acquisition(self):
        job = json.loads(DEFINITION.read_text())
        with patch("scripts.etty_bounded_job.confined", side_effect=lambda path, roots: Path(path)):
            validate_manifest(job)
        self.assertFalse(job["acquire"])
        self.assertFalse(job["network_acquisition"])
        self.assertEqual(job["transfer_cap_bytes"], 1)
        self.assertLessEqual(job["wall_seconds"], 21600)
        self.assertLessEqual(job["memory_cap_bytes"], 16 * 1024**3)
        self.assertLessEqual(job["workspace_cap_bytes"], 20 * 1024**3)

    def test_scope_is_two_separate_species_grids(self):
        job = json.loads(DEFINITION.read_text())
        command = job["items"][0]["command"]
        self.assertIn("run_530_beta_diversity_production.py", command[1])
        self.assertFalse(job["pooled_530_model"])
        self.assertFalse(job["differential_abundance"])
        source = (ROOT / "scripts/run_530_beta_diversity_production.py").read_text()
        for forbidden in ("ANCOM", "ALDEx", "DESeq2", "MaAsLin", "urllib", "requests", "download.file"):
            self.assertNotIn(forbidden, source)

    def test_pinned_gate_passes_offline(self):
        gate = validate_pinned_czm_gate()
        self.assertEqual(gate["status"], "CZM_ISOLATED_LIBRARY_READY")

    def test_required_handoff_is_small_file_types(self):
        job = json.loads(DEFINITION.read_text())
        self.assertTrue(all(Path(name).suffix in {".json", ".md", ".txt"} for name in job["handoff_allowlist"]))
        self.assertIn("analysis_manifest.json", job["handoff_allowlist"])
        self.assertIn("production_summary.md", job["handoff_allowlist"])


if __name__ == "__main__":
    unittest.main()
