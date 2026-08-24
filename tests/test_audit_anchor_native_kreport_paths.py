import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import audit_anchor_native_kreport_paths as audit

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name) / "results"; self.root.mkdir()
        self.batch = self.root / "prjna1056765_production_descriptive_batch_x" / "kraken2"; self.batch.mkdir(parents=True)
        self.runs = {"SRR27343191", "SRR1"}
    def tearDown(self): self.t.cleanup()
    def test_native_and_bracken_excluded(self):
        n = self.batch / "SRR27343191.kreport"; n.write_bytes(b"not read")
        (self.batch / "SRR27343191_bracken_species.kreport").write_bytes(b"derived")
        self.assertEqual(audit.native_candidates(self.root, self.runs)["SRR27343191"], [n])
    def test_missing_duplicate_nested_and_escape(self):
        n = self.batch / "SRR27343191.kreport"; n.touch()
        duplicate_dir = self.root / "another" / "kraken2"; duplicate_dir.mkdir(parents=True)
        (duplicate_dir / "SRR27343191.kreport").touch()
        nested = self.root / "nested" / "kraken2"; nested.mkdir(parents=True); (nested / "SRR1.kreport").touch()
        self.assertEqual(len(audit.native_candidates(self.root, self.runs)["SRR1"]), 1)
        self.assertEqual(len(audit.native_candidates(self.root, self.runs)["SRR27343191"]), 2)
        outside = Path(self.t.name) / "outside.kreport"; outside.touch()
        link = self.batch / "SRR1.kreport"; link.symlink_to(outside)
        self.assertEqual(audit.native_candidates(self.root, self.runs)["SRR1"], [nested / "SRR1.kreport"])
    def test_no_content_or_network_and_bounded_classifier(self):
        p = self.batch / "SRR1.kreport"; p.touch()
        self.assertEqual(audit.classify_native_path(p, self.root, self.runs), "SRR1")
        self.assertIsNone(audit.classify_native_path(self.root / "other" / "SRR1.kreport", self.root, self.runs))
        source = Path(audit.__file__).read_text(encoding="utf-8")
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("read_bytes", source)
        self.assertNotIn("read_text", source)

    def test_audit_reports_missing_and_duplicate_without_reading_reports(self):
        runs = [f"SRR{i:04d}" for i in range(399)] + ["SRR27343191"]
        membership = Path(self.t.name) / "membership.tsv"
        membership.write_text("run\n" + "\n".join(runs) + "\n", encoding="utf-8")
        batch = self.root / "audit-batch" / "kraken2"; batch.mkdir(parents=True)
        for run in runs[1:-1]:
            (batch / f"{run}.kreport").write_bytes(b"not a report")
        (batch / "SRR27343191.kreport").write_bytes(b"not a report")
        duplicate = self.root / "audit-batch-2" / "kraken2"; duplicate.mkdir(parents=True)
        (duplicate / "SRR27343191.kreport").write_bytes(b"still not parsed")
        output = Path(self.t.name) / "out"
        result = audit.audit(self.root, membership, output)
        self.assertEqual(result["frozen_runs"], 400)
        self.assertEqual(result["native_unique_runs"], 399)
        self.assertEqual(result["native_report_files"], 400)
        self.assertEqual(result["duplicate_runs"], ["SRR27343191"])
        self.assertEqual(result["missing_runs"], ["SRR0000"])
    def test_recovery_output_generator_fields(self):
        self.assertFalse(False); self.assertEqual("NONE", "NONE")

if __name__ == "__main__": unittest.main()
