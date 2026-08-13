import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "short_read_production", ROOT / "scripts/run_prjna1056765_humann_short_reads_production.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class ShortReadProductionTests(unittest.TestCase):
    def config(self):
        return json.loads((ROOT / "config/prjna1056765_humann_short_read_production.json").read_text())

    def test_fixed_cohort_is_30_with_exactly_29_non_smoke_samples(self):
        cfg = self.config()
        matrix, status = MOD.cohort(cfg)
        self.assertEqual(len(matrix), 30)
        self.assertEqual(len(status), 30)
        self.assertEqual(cfg["remaining_sample_cap"], 29)
        self.assertIn(cfg["smoke_sample"], status)
        self.assertEqual(sum(row["run"] != cfg["smoke_sample"] for row in matrix), 29)

    def test_runtime_path_pins_new_bowtie_before_humann_environment(self):
        cfg = self.config()
        env = MOD.runtime_env(cfg)
        parts = env["PATH"].split(os.pathsep)
        self.assertEqual(parts[0], cfg["bowtie2_dir"])
        self.assertEqual(parts[1], cfg["humann_env_bin"])

    def test_reused_index_requires_complete_six_shard_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prefix = root / "sample_bowtie2_index"
            suffixes = (".1.bt2", ".2.bt2", ".3.bt2", ".4.bt2", ".rev.1.bt2", ".rev.2.bt2")
            for suffix in suffixes:
                (Path(str(prefix) + suffix)).write_bytes(b"x")
            found_prefix, shards = MOD.find_index_prefix(root)
            self.assertEqual(found_prefix, str(prefix))
            self.assertEqual(len(shards), 6)
            shards[0].unlink()
            with self.assertRaisesRegex(RuntimeError, "complete six-shard"):
                MOD.find_index_prefix(root)

    def test_production_command_bypasses_prescreen_and_index_build(self):
        cfg = self.config()
        cmd = MOD.humann_command(cfg, Path("reads.fastq.gz"), Path("out/sample"))
        self.assertIn("--bypass-nucleotide-index", cmd)
        self.assertIn("--resume", cmd)
        self.assertNotIn("--taxonomic-profile", cmd)
        self.assertNotIn("--metaphlan", cmd)
        self.assertNotIn("--bowtie2", cmd)
        self.assertNotIn("--diamond", cmd)
        self.assertEqual(cmd[cmd.index("--nucleotide-database") + 1], cfg["shared_index_dir"])
        self.assertEqual(cmd[cmd.index("--protein-database") + 1], cfg["uniref90"])

    def test_autopilot_defaults_to_short_read_route_without_recursive_lock_delete(self):
        text = (ROOT / "scripts/autopilot_metagenome_functional_profile.sh").read_text()
        self.assertIn('FUNCTIONAL_SHORT_READ_MODE:-1', text)
        self.assertIn("run_prjna1056765_humann_short_reads_production.py", text)
        self.assertNotIn("rm -rf", text)


if __name__ == "__main__":
    unittest.main()
