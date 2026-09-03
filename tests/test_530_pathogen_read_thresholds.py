import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_530_pathogen_read_thresholds as audit
from scripts.etty_bounded_job import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "automation/production/20260905T120000Z-0714-real-530-pathogen-read-threshold-audit.json"


class PathogenReadThresholdTests(unittest.TestCase):
    def test_mutually_exclusive_read_bins(self):
        result = audit.count_bins([1, 2, 5, 6, 10, 11, 50, 51, 100, 101, 1001])
        self.assertEqual(sum(result[key]["n"] for key in ("exactly_1", "2_to_5", "6_to_10", "11_to_50", "51_to_100", "greater_than_100")), 11)
        self.assertEqual(result["greater_than_1000_flag"]["n"], 1)

    def test_fraction_bin_boundaries(self):
        result = audit.fraction_bins([0, 0.0009, 0.001, 0.009, 0.01, 0.09, 0.1, 0.5, 0.5001])
        self.assertEqual(sum(value["n"] for value in result.values()), 9)
        self.assertEqual(result["less_than_0.1_percent"]["n"], 2)
        self.assertEqual(result["greater_than_50_percent"]["n"], 1)

    def test_shape_is_descriptive_not_optimized(self):
        self.assertEqual(audit.shape_label([1, 1, 2, 2, 20])["descriptive_shape"], "strongly_concentrated_at_1_to_2_reads")
        self.assertEqual(audit.shape_label([1, 2, 4, 8, 1000])["bimodality"], "NOT_CLEARLY_SUPPORTED_BY_DESCRIPTIVE_AUDIT")

    def test_exact_panel_contract_has_eleven(self):
        self.assertEqual(len(audit.EXPECTED_PANEL), 11)
        self.assertEqual(audit.EXPECTED_PANEL["1773"][0], "Mycobacterium tuberculosis")

    def test_source_has_no_forbidden_hypothesis_methods(self):
        source = Path(audit.__file__).read_text()
        for token in ("fisher_exact(", "permanova(", "permdisp(", "cmultRepl(", "clr_transform(", "bh_fdr(", "ANCOMBC", "ALDEx2("):
            self.assertNotIn(token, source)

    def test_job_is_bounded_descriptive_and_zero_download(self):
        job = json.loads(DEFINITION.read_text())
        with patch("scripts.etty_bounded_job.confined", side_effect=lambda path, roots: Path(path)):
            validate_manifest(job)
        self.assertFalse(job["acquire"])
        self.assertFalse(job["hypothesis_testing"])
        self.assertFalse(job["panel_changed"])
        self.assertFalse(job["final_threshold_selected"])
        self.assertEqual(job["transfer_cap_bytes"], 1)
        self.assertTrue(all(Path(name).suffix in {".json", ".md", ".txt"} for name in job["handoff_allowlist"]))


if __name__ == "__main__":
    unittest.main()
