import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "build_common_kraken2_assignment_layer.py"
SPEC = importlib.util.spec_from_file_location("common_layer", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


REPORT = """50.00\t10\t10\tU\t0\tunclassified
50.00\t10\t0\tR\t1\troot
30.00\t6\t2\tG\t10\t  Genus alpha
20.00\t4\t4\tS\t11\t    Genus alpha species
"""


class CommonLayerTests(unittest.TestCase):
    def test_direct_and_clade_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.kreport"
            path.write_text(REPORT)
            parsed = MODULE.parse_report(path)
            self.assertEqual(parsed["total_input_reads"], 20)
            self.assertEqual(parsed["classified_reads"], 10)
            self.assertEqual(parsed["taxa"]["G"][10], ("Genus alpha", 2, 6))
            self.assertEqual(parsed["taxa"]["S"][11], ("Genus alpha species", 4, 4))

    def test_absent_taxon_is_zero(self):
        sample = {"report": {"taxa": {"S": {}, "G": {}}}}
        self.assertEqual(MODULE.direct_count(sample, "S", 99), 0)

    def test_duplicate_taxid_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.kreport"
            path.write_text(REPORT + "1.00\t1\t1\tS\t11\tduplicate\n")
            with self.assertRaises(MODULE.LayerError):
                MODULE.parse_report(path)

    def test_direct_rank_sum_cannot_exceed_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.kreport"
            path.write_text(REPORT.replace("20.00\t4\t4\tS", "20.00\t12\t12\tS"))
            with self.assertRaises(MODULE.LayerError):
                MODULE.parse_report(path)

    def test_bray_and_paired_tests(self):
        distance = MODULE.bray_curtis([[1.0, 0.0], [0.8, 0.2], [0.0, 1.0], [0.2, 0.8]])
        labels = ["A", "A", "B", "B"]
        self.assertGreater(MODULE.permanova_stat(distance, labels)[0], 0)
        self.assertGreaterEqual(MODULE.dispersion_stat(distance, labels)[0], 0)

    def test_bounded_diagnostic_preserves_exception_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagnostic.json"
            MODULE._DIAGNOSTIC_CONTEXT.update({
                "stage": "C_report_path_resolution",
                "first_failing_run_if_any": "RUN1",
                "expected_path": "/approved/root",
                "observed_path": "/missing/report.kreport",
                "source_gate_status": "STAGE_C_RUNNING",
            })
            try:
                raise MODULE.LayerError("report missing")
            except MODULE.LayerError as exc:
                MODULE.write_diagnostic(output, exc)
            payload = json.loads(output.read_text())
            self.assertEqual(payload["stage"], "C_report_path_resolution")
            self.assertEqual(payload["exception_type"], "LayerError")
            self.assertEqual(payload["first_failing_run_if_any"], "RUN1")
            self.assertTrue((Path(tmp) / "diagnostic.txt").is_file())


if __name__ == "__main__":
    unittest.main()
