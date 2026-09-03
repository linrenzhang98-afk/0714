import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_530_czm_sparsity as audit


class CzmSparsityAuditTests(unittest.TestCase):
    def test_strict_boundary_and_quantiles(self):
        values = [0.5, 0.8, 0.81, 0.95]
        result = audit.distribution(values)
        self.assertEqual(result["strictly_greater"]["0.8"]["count"], 2)
        self.assertEqual(result["greater_or_equal_0.80"]["count"], 3)
        self.assertEqual(result["quantiles"]["minimum"], 0.5)
        self.assertEqual(result["quantiles"]["maximum"], 0.95)

    def test_sample_species_orientation_and_prevalence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "counts.tsv"
            samples = [f"S{i}" for i in range(20)]
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle, delimiter="\t")
                writer.writerow(["taxid", "rank", "scientific_name", "prevalence", "present_5pct", "present_10pct", "present_20pct", *samples])
                writer.writerow(["1", "S", "one", "", "", "", "", 1, *([0] * 19)])
                writer.writerow(["2", "S", "two", "", "", "", "", 1, 1, *([0] * 18)])
                writer.writerow(["3", "S", "three", "", "", "", "", *([1] * 4), *([0] * 16)])
            with patch.dict(audit.EXPECTED, {"anchor": (20, 3)}):
                result = audit.audit(path, "anchor")
            self.assertEqual(result["artifact_orientation_before_filter"]["rows"], "species")
            self.assertEqual(result["transformation_orientation_after_filter"]["rows"], "samples")
            self.assertEqual(result["thresholds"]["0.05"]["retained_species"], 3)
            self.assertEqual(result["thresholds"]["0.1"]["retained_species"], 2)
            self.assertEqual(result["thresholds"]["0.2"]["retained_species"], 1)
            self.assertEqual(result["thresholds"]["0.2"]["feature_zero_fraction"]["strictly_greater"]["0.8"]["count"], 0)

    def test_source_contains_no_transformation_or_inference_calls(self):
        source = Path(audit.__file__).read_text()
        for forbidden in ("cmultRepl(", "permanova(", "permdisp(", "clr_transform(", "bray_curtis_distance("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
