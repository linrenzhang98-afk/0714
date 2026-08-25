import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install_r_czm_isolated as installer


def lock_fixture():
    return {
        "total_expected_download_bytes": 3,
        "packages": [
            {"package": "MASS", "install_new": False, "installation_order": 0},
            {"package": "NADA", "version": "1", "install_new": True, "installation_order": 1, "source_filename": "NADA_1.tar.gz", "expected_bytes": 1, "expected_sha256": hashlib.sha256(b"a").hexdigest(), "source_url": "https://cran.r-project.org/src/contrib/NADA_1.tar.gz"},
            {"package": "truncnorm", "version": "1", "install_new": True, "installation_order": 2, "source_filename": "truncnorm_1.tar.gz", "expected_bytes": 1, "expected_sha256": hashlib.sha256(b"b").hexdigest(), "source_url": "https://cran.r-project.org/src/contrib/truncnorm_1.tar.gz"},
            {"package": "zCompositions", "version": "1.6.2", "install_new": True, "installation_order": 3, "source_filename": "zCompositions_1.6.2.tar.gz", "expected_bytes": 1, "expected_sha256": hashlib.sha256(b"c").hexdigest(), "source_url": "https://cran.r-project.org/src/contrib/zCompositions_1.6.2.tar.gz"},
        ],
    }


class IsolatedInstallTests(unittest.TestCase):
    def test_dependency_lock_order_and_suggests_exclusion(self):
        packages = installer.lock_new_packages(lock_fixture())
        self.assertEqual([p["package"] for p in packages], ["NADA", "truncnorm", "zCompositions"])
        self.assertNotIn("testthat", [p["package"] for p in packages])

    def test_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw)
            for package in installer.lock_new_packages(lock_fixture()):
                (source / package["source_filename"]).write_bytes(b"x")
            _, reason = installer.validate_tarballs(lock_fixture(), source)
            self.assertEqual(reason, "SOURCE_CHECKSUM_MISMATCH:NADA")

    def test_isolated_path_confinement(self):
        self.assertTrue(installer.confined_isolated_path(installer.ISOLATED_PARENT / "zCompositions-1.6.2-R-4.5.3"))
        self.assertFalse(installer.confined_isolated_path(Path("/tmp/not-allowed")))
        self.assertFalse(installer.confined_isolated_path(installer.ISOLATED_PARENT / ".." / "escape"))

    def test_system_library_immutability_comparison(self):
        self.assertEqual(installer.system_library_unchanged({"MASS": "1"}, {"MASS": "1"}), (True, True))
        self.assertEqual(installer.system_library_unchanged({"MASS": "1"}, {"MASS": "2"}), (True, False))
        self.assertEqual(installer.system_library_unchanged({"MASS": "1"}, {"MASS": "1", "survival": "1"}), (False, False))

    def test_existing_nonempty_target_stops_before_r_access(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "zCompositions-1.6.2-R-4.5.3"
            target.mkdir(); (target / "partial").write_text("x")
            with patch.object(installer, "ISOLATED_PARENT", Path(raw)):
                report = installer.build_report("synthetic", lock_fixture(), Path(raw), target)
            self.assertEqual(report["reason"], "ISOLATED_LIBRARY_ALREADY_NONEMPTY")

    def test_malformed_r_output(self):
        values, malformed = installer.parse_protocol("KV\tx\ty\ninvalid\n")
        self.assertEqual(values["x"], "y")
        self.assertEqual(malformed, ["invalid"])

    def test_version_mismatch_does_not_return_ready(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "zCompositions-1.6.2-R-4.5.3"
            with patch.object(installer, "ISOLATED_PARENT", Path(raw)), patch.object(installer, "r_runtime_info", return_value=("R version 4.4.0", None)):
                report = installer.build_report("synthetic", lock_fixture(), Path(raw), target)
            self.assertEqual(report["status"], "CZM_ISOLATED_LIBRARY_NOT_READY")
            self.assertEqual(report["reason"], "R_VERSION_MISMATCH_OR_UNAVAILABLE")

    def test_czm_deterministic_parser_validation(self):
        class Completed:
            returncode = 0
            stderr = ""
            stdout = "\n".join([
                "KV\tczm_rows\t4", "KV\tczm_cols\t5",
                "KV\tczm_values\t" + ",".join(["0.2"] * 20),
                "KV\tczm_repeat_values\t" + ",".join(["0.2"] * 20),
                "KV\tczm_row_sums\t1,1,1,1", "KV\tczm_loaded_namespaces\tzCompositions"
            ])
        with patch.object(installer, "run_r", return_value=Completed()):
            report, reason = installer.validate_czm(Path("/synthetic"))
        self.assertIsNone(reason)
        self.assertTrue(report["passed"])
        self.assertEqual(report["output_sha256"], report["repeat_output_sha256"])

    def test_source_contains_no_biological_paths_or_network_calls(self):
        source = Path(installer.__file__).read_text()
        for forbidden in ("urllib", "requests", "download.file", "install.packages", "kraken2", "bracken", "PRJNA1056765", "PRJCA046985", "shell=True"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
