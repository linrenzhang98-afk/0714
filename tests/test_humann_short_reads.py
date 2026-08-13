import csv
import importlib.util
import json
import tempfile
import unittest
from unittest import mock
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
        for invalid in (["SRR27343495"], ["SRR27343495", "SRR27343566", "SRR27343490"]):
            changed = dict(cfg, validation_samples=invalid)
            with self.assertRaisesRegex(RuntimeError, "exactly two"):
                MOD.cohort(changed)

    def test_four_columns_percent_and_strict_threshold(self):
        rows = MOD.profile_rows([
            {"name": "Alpha beta", "taxonomy_id": "1", "fraction_total_reads": "0.0001"},
            {"name": "Gamma delta", "taxonomy_id": "2", "fraction_total_reads": "0.00010001"},
        ], 0.01)
        self.assertEqual(rows, [["g__Gamma|s__Gamma_delta", "2", "0.010001", ""]])
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "profile.tsv"
            MOD.write_profile(path, rows)
            with path.open() as handle:
                parsed = list(csv.reader(handle, delimiter="\t"))
            self.assertTrue(all(len(row) == 4 for row in parsed))
            self.assertEqual(parsed[0], MOD.PROFILE_HEADER)

    def test_taxonomy_is_not_fuzzily_remapped(self):
        self.assertEqual(MOD.clade_name("Escherichia coli"), "g__Escherichia|s__Escherichia_coli")
        with self.assertRaises(RuntimeError):
            MOD.clade_name("bad|taxonomy")
        with self.assertRaises(RuntimeError):
            MOD.clade_name("unclassified")

    def test_tool_directories_and_executable_version_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bowtie_dir = root / "bowtie"
            diamond_dir = root / "diamond"
            bowtie_dir.mkdir()
            diamond_dir.mkdir()
            cfg = {
                "humann": str(root / "humann"),
                "bowtie2_dir": str(bowtie_dir),
                "diamond_dir": str(diamond_dir),
                "required_versions": {"humann": "3.9", "bowtie2": "2.5.5"},
            }
            for path in (root / "humann", bowtie_dir / "bowtie2", bowtie_dir / "bowtie2-build", diamond_dir / "diamond"):
                path.touch()
                path.chmod(0o755)
            outputs = {
                str(root / "humann"): "humann v3.9",
                str(bowtie_dir / "bowtie2"): "bowtie2 version 2.5.5",
                str(bowtie_dir / "bowtie2-build"): "bowtie2-build version 2.5.5",
                str(diamond_dir / "diamond"): "diamond version 2.0.15",
            }
            with mock.patch.object(MOD, "command_output", side_effect=lambda args: outputs[args[0]]) as output:
                versions = MOD.version_gate(cfg)
            self.assertIn("2.5.5", versions["bowtie2"])
            self.assertEqual(output.call_args_list[-1].args[0], [str(diamond_dir / "diamond"), "version"])

            with mock.patch.object(MOD, "command_output", side_effect=lambda args: outputs[args[0]]):
                (bowtie_dir / "bowtie2").unlink()
                with self.assertRaisesRegex(RuntimeError, "bowtie2"):
                    MOD.version_gate(cfg)

            (bowtie_dir / "bowtie2").touch()
            (bowtie_dir / "bowtie2").chmod(0o755)
            outputs[str(bowtie_dir / "bowtie2-build")] = "bowtie2-build version 2.4.5"
            with mock.patch.object(MOD, "command_output", side_effect=lambda args: outputs[args[0]]):
                with self.assertRaisesRegex(RuntimeError, "bowtie2-build version mismatch"):
                    MOD.version_gate(cfg)

    def test_index_requires_complete_shards(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            for suffix in ("1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"):
                (path / f"x_bowtie2_index.{suffix}").touch()
            self.assertEqual(len(MOD.index_shards(path)), 6)

    def test_humann_receives_tool_directories_and_reuses_only_complete_joint_index(self):
        cfg = {
            "humann": "/humann/bin/humann", "uniref90": "/db/uniref", "chocophlan": "/db/chocophlan",
            "bowtie2_dir": "/bowtie/bin", "diamond_dir": "/diamond/bin",
        }
        with tempfile.TemporaryDirectory() as td:
            index = Path(td)
            for suffix in ("1.bt2", "2.bt2", "3.bt2", "4.bt2", "rev.1.bt2", "rev.2.bt2"):
                (index / f"x_bowtie2_index.{suffix}").touch()
            first = MOD.humann_command(cfg, Path("reads.fq"), Path("out1"), Path("profile.tsv"))
            reused = MOD.humann_command(cfg, Path("reads.fq"), Path("out2"), Path("profile.tsv"), index)
            self.assertEqual(first[first.index("--bowtie2") + 1], cfg["bowtie2_dir"])
            self.assertEqual(first[first.index("--diamond") + 1], cfg["diamond_dir"])
            self.assertIn("--taxonomic-profile", first)
            self.assertNotIn("--bypass-nucleotide-index", first)
            self.assertNotIn("--taxonomic-profile", reused)
            self.assertIn("--bypass-nucleotide-index", reused)
            self.assertEqual(reused[reused.index("--nucleotide-database") + 1], str(index))
            MOD.index_shards(index)[0].unlink()
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                MOD.humann_command(cfg, Path("reads.fq"), Path("out3"), Path("profile.tsv"), index)


if __name__ == "__main__":
    unittest.main()
