import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.etty_bounded_job import validate_manifest
from shotgun_analysis.production_package import validate_pinned_czm_gate

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "automation/production/20260904T120000Z-0714-real-530-balf-beta-diversity-production.json"
RECOVERY = ROOT / "automation/production/20260904T180000Z-0714-real-530-balf-beta-diversity-nada-gate-recovery.json"


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

    def test_recovery_preserves_bounded_scientific_scope(self):
        old = json.loads(DEFINITION.read_text())
        recovery = json.loads(RECOVERY.read_text())
        for key in ("project", "acquire", "analysis_type", "allowed_hosts", "transfer_cap_bytes",
                    "allowed_executables", "wall_seconds", "memory_cap_bytes", "workspace_cap_bytes",
                    "network_acquisition", "package_installation", "pooled_530_model",
                    "differential_abundance", "handoff_allowlist"):
            self.assertEqual(recovery[key], old[key])
        self.assertNotEqual(recovery["job_id"], old["job_id"])

    def test_failed_definition_and_queue_are_preserved(self):
        self.assertTrue(DEFINITION.is_file())
        self.assertTrue((ROOT / "automation/etty_jobs/20260904T120000Z-0714-real-530-balf-beta-diversity-production.json").is_file())


if __name__ == "__main__":
    unittest.main()
