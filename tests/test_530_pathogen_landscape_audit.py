import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_530_pathogen_landscape as audit
from scripts.etty_bounded_job import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "automation/production/20260905T063000Z-0714-real-530-pathogen-landscape-audit-handoff-recovery.json"


class PathogenLandscapeAuditTests(unittest.TestCase):
    def write_inputs(self, root: Path):
        samples = ["S1", "S2", "S3", "S4"]
        matrix = root / "counts.tsv"
        with matrix.open("w", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["taxid", "rank", "scientific_name", "prevalence", "present_5pct", "present_10pct", "present_20pct", *samples])
            writer.writerow(["1", "S", "Pseudomonas aeruginosa", "", "", "", "", 10, 0, 4, 0])
            writer.writerow(["2", "S", "Rothia mucilaginosa", "", "", "", "", 0, 2, 1, 1])
            writer.writerow(["3", "S", "Unknown species", "", "", "", "", 0, 0, 0, 3])
        metadata = root / "metadata.tsv"
        with metadata.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["run", "diagnosis"], delimiter="\t")
            writer.writeheader()
            for sample, group in zip(samples, ["A", "A", "B", "B"]):
                writer.writerow({"run": sample, "diagnosis": group})
        return matrix, metadata

    def test_descriptive_metrics_and_candidate_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            matrix_path, metadata_path = self.write_inputs(Path(directory))
            with patch.dict(audit.EXPECTED, {"anchor": {"samples": 4, "features": 3, "groups": {"A": 2, "B": 2}}}):
                matrix = audit.read_matrix(matrix_path, "anchor")
                summary, tables = audit.audit_cohort("anchor", matrix, audit.read_groups(metadata_path, "anchor"))
        self.assertEqual(summary["detected_species_per_sample"]["median"], 1.5)
        self.assertAlmostEqual(summary["top1_dominance"]["median"], 0.9)
        self.assertEqual(summary["panel_structure"]["single_panel_pathogen"]["n"], 2)
        self.assertEqual(summary["panel_structure"]["no_panel_pathogen_detected"]["n"], 2)
        self.assertEqual(tables["top_prevalence"][0]["scientific_name"], "Rothia mucilaginosa")

    def test_relevance_is_fail_conservative(self):
        self.assertEqual(audit.relevance("Pseudomonas aeruginosa"), "confirmed_known_respiratory_pathogen")
        self.assertEqual(audit.relevance("Candida albicans"), "plausible_opportunist")
        self.assertEqual(audit.relevance("Rothia mucilaginosa"), "likely_commensal_or_background")
        self.assertEqual(audit.relevance("Unreviewed organism"), "uncertain")

    def test_quantile_contract(self):
        self.assertEqual(audit.quantiles([1, 2, 3, 4]), {"minimum": 1.0, "q1": 1.75, "median": 2.5, "q3": 3.25, "maximum": 4.0})

    def test_source_excludes_forbidden_analyses(self):
        source = Path(audit.__file__).read_text()
        for forbidden in ("cmultRepl(", "clr_transform(", "permanova(", "permdisp(", "bray_curtis_distance(", "ANCOMBC", "ALDEx2("):
            self.assertNotIn(forbidden, source)

    def test_job_is_bounded_zero_download_and_descriptive_only(self):
        job = json.loads(DEFINITION.read_text())
        with patch("scripts.etty_bounded_job.confined", side_effect=lambda path, roots: Path(path)):
            validate_manifest(job)
        self.assertFalse(job["acquire"])
        self.assertFalse(job["network_acquisition"])
        self.assertFalse(job["package_installation"])
        self.assertFalse(job["kraken2_rerun"])
        self.assertFalse(job["bracken"])
        self.assertFalse(job["pooled_530_model"])
        self.assertEqual(job["transfer_cap_bytes"], 1)
        self.assertLessEqual(job["wall_seconds"], 1800)
        self.assertTrue(all(Path(name).suffix in {".json", ".md", ".txt"} for name in job["handoff_allowlist"]))


if __name__ == "__main__":
    unittest.main()
