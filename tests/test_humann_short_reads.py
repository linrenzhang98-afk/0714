import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("short_reads", ROOT / "scripts/run_prjna1056765_humann_short_reads.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class ShortReadTests(unittest.TestCase):
    def test_exact_cohort_and_validation_cap(self):
        cfg = json.loads((ROOT / "config/prjna1056765_humann_short_read_validation.json").read_text())
        matrix, status = MOD.cohort(cfg)
        self.assertEqual(len(matrix), 30)
        self.assertEqual(set(r["run"] for r in matrix), set(status))
        self.assertEqual(cfg["validation_samples"], ["SRR27343495", "SRR27343566"])
        self.assertNotIn(cfg["smoke_sample"], cfg["validation_samples"])

    def test_four_columns_percent_and_strict_threshold(self):
        rows = MOD.profile_rows([
            {"name": "Alpha beta", "taxonomy_id": "1", "fraction_total_reads": "0.0001"},
            {"name": "Gamma delta", "taxonomy_id": "2", "fraction_total_reads": "0.00010001"},
        ], 0.01)
        self.assertEqual(rows, [["s__Gamma_delta", "2", "0.010001", ""]])
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "profile.tsv"
            MOD.write_profile(path, rows)
            with path.open() as handle:
                parsed = list(csv.reader(handle, delimiter="\t"))
            self.assertTrue(all(len(row) == 4 for row in parsed))
            self.assertEqual(parsed[0], MOD.PROFILE_HEADER)

    def test_taxonomy_is_not_fuzzily_remapped(self):
        self.assertEqual(MOD.clade_name("Escherichia coli"), "s__Escherichia_coli")
        with self.assertRaises(RuntimeError):
            MOD.clade_name("bad|taxonomy")

    def test_index_requires_complete_shards(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            for suffix in ("1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"):
                (path / f"x_bowtie2_index.{suffix}").touch()
            self.assertEqual(len(MOD.index_shards(path)), 6)


if __name__ == "__main__":
    unittest.main()
