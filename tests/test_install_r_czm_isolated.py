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
    def test_path_prepending_exposes_compiler_wrappers(self):
        with patch.dict("os.environ", {"PATH": "/custom/bin:/usr/bin:/bin"}, clear=True), patch.object(installer.shutil, "which", side_effect=lambda name, path: f"{installer.MGSHOTGUN_BIN}/{name}") as which:
            environment = installer.execution_environment()
            resolved, missing = installer.compiler_probe()
        self.assertEqual(missing, None)
        self.assertTrue(environment["PATH"].startswith(installer.MGSHOTGUN_BIN + ":"))
        self.assertTrue(all(entry in environment["PATH"].split(":") for entry in ("/custom/bin", "/usr/bin", "/bin")))
        self.assertEqual(set(resolved), set(installer.R_REQUIRED_EXECUTABLES))
        self.assertEqual(which.call_args.kwargs["path"], environment["PATH"])

    def test_missing_compiler_fails_closed(self):
        with patch.object(installer.shutil, "which", side_effect=lambda name, path: None if name.endswith("gfortran") else f"/bin/{name}"):
            resolved, missing = installer.compiler_probe()
        self.assertEqual(missing, "x86_64-conda-linux-gnu-gfortran")
        self.assertNotIn(missing, resolved)

    def test_system_tools_resolve_under_exact_r_environment(self):
        expected = {name: f"/usr/bin/{name}" for name in installer.R_REQUIRED_EXECUTABLES}
        with patch.object(installer.shutil, "which", side_effect=lambda name, path: expected[name]):
            resolved, missing = installer.compiler_probe()
        self.assertIsNone(missing)
        self.assertEqual({name: resolved[name] for name in ("sh", "uname", "make")}, {name: expected[name] for name in ("sh", "uname", "make")})

    def test_all_r_subprocesses_receive_execution_path(self):
        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""
        package = {"tarball_path": "/tmp/locked.tar.gz"}
        with patch("subprocess.run", return_value=Completed()) as run:
            installer.run_r("cat('ok')")
            installer.install_package(package, Path("/tmp/isolated"))
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertTrue(call.kwargs["env"]["PATH"].startswith(installer.MGSHOTGUN_BIN + ":"))

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

    def test_exact_locked_partial_nada_state_is_resumable(self):
        valid, unexpected, mismatched = installer.validate_isolated_inventory({"NADA": "1"}, lock_fixture())
        self.assertTrue(valid)
        self.assertEqual(unexpected, [])
        self.assertEqual(mismatched, [])

    def test_unexpected_package_fails_closed(self):
        valid, unexpected, mismatched = installer.validate_isolated_inventory({"NADA": "1", "other": "1"}, lock_fixture())
        self.assertFalse(valid)
        self.assertEqual(unexpected, ["other"])
        self.assertEqual(mismatched, [])

    def test_wrong_nada_version_fails_closed(self):
        valid, unexpected, mismatched = installer.validate_isolated_inventory({"NADA": "2"}, lock_fixture())
        self.assertFalse(valid)
        self.assertEqual(unexpected, [])
        self.assertEqual(mismatched, ["NADA"])

    def test_empty_isolated_library_is_valid(self):
        valid, unexpected, mismatched = installer.validate_isolated_inventory({}, lock_fixture())
        self.assertTrue(valid)
        self.assertEqual(unexpected, [])
        self.assertEqual(mismatched, [])

    def test_matching_package_is_skipped(self):
        missing = installer.missing_locked_packages(lock_fixture(), {"NADA": "1"})
        self.assertEqual([package["package"] for package in missing], ["truncnorm", "zCompositions"])

    def test_existing_unexpected_target_stops_before_install(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "zCompositions-1.6.2-R-4.5.3"
            target.mkdir(); (target / "partial").write_text("x")
            with patch.object(installer, "ISOLATED_PARENT", Path(raw)), patch.object(installer, "compiler_probe", return_value=({name: f"/bin/{name}" for name in installer.MAKECONF_COMPILERS}, None)), patch.object(installer, "r_runtime_info", return_value=("R version 4.5.3", None)), patch.object(installer, "r_inventory", side_effect=[({"MASS": "1", "survival": "1"}, None), ({"partial": "1"}, None)]):
                report = installer.build_report("synthetic", lock_fixture(), Path(raw), target)
            self.assertEqual(report["reason"], "ISOLATED_LIBRARY_CONTENTS_INVALID")

    def test_malformed_r_output(self):
        values, malformed = installer.parse_protocol("KV\tx\ty\ninvalid\n")
        self.assertEqual(values["x"], "y")
        self.assertEqual(malformed, ["invalid"])

    def test_version_mismatch_does_not_return_ready(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "zCompositions-1.6.2-R-4.5.3"
            with patch.object(installer, "ISOLATED_PARENT", Path(raw)), patch.object(installer, "compiler_probe", return_value=({name: f"/bin/{name}" for name in installer.MAKECONF_COMPILERS}, None)), patch.object(installer, "r_runtime_info", return_value=("R version 4.4.0", None)):
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

    def test_validation_mode_never_acquires_or_installs(self):
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "target"
            target.mkdir()
            inventory = {"NADA": "1", "truncnorm": "1", "zCompositions": "1.6.2"}
            system = {"MASS": "1", "survival": "1"}
            with patch.object(installer, "ISOLATED_PARENT", Path(raw)), patch.object(installer, "compiler_probe", return_value=({name: f"/bin/{name}" for name in installer.R_REQUIRED_EXECUTABLES}, None)), patch.object(installer, "r_runtime_info", return_value=("R version 4.5.3", None)), patch.object(installer, "r_inventory", side_effect=[(system, None), (inventory, None), (system, None), (inventory, None)]), patch.object(installer, "validate_tarballs", side_effect=AssertionError("validation mode acquired")), patch.object(installer, "install_package", side_effect=AssertionError("validation mode installed")), patch.object(installer, "validate_czm", return_value=({"passed": True}, None)):
                report = installer.build_report("synthetic", lock_fixture(), Path(raw), target, perform_install=False)
            self.assertEqual(report["status"], "CZM_ISOLATED_LIBRARY_READY")
            self.assertFalse(report["network_acquisition_performed"])
            self.assertFalse(report["package_installation_performed"])

    def test_structure_adapter_accepts_direct_matrix_and_data_frame(self):
        code = installer.validation_code(Path("/synthetic"))
        self.assertIn("is.matrix(candidate) || is.data.frame(candidate)", code)
        self.assertIn("as.matrix(candidate)", code)

    def test_structure_adapter_selects_one_list_component(self):
        code = installer.validation_code(Path("/synthetic"))
        self.assertIn("for (i in seq_along(candidate))", code)
        self.assertIn('selected_component_path', code)

    def test_structure_adapter_fails_on_zero_or_multiple_components(self):
        code = installer.validation_code(Path("/synthetic"))
        self.assertIn("length(candidates) != 1L", code)
        self.assertIn("found %d", code)

    def test_structure_probe_records_bounded_metadata(self):
        code = installer.validation_code(Path("/synthetic"))
        for field in ("_class", "_typeof", "_names", "_dim", "_is_matrix", "_is_data_frame", "_is_list", "_str"):
            self.assertIn(field, code)

    def test_source_contains_no_biological_paths_or_network_calls(self):
        source = Path(installer.__file__).read_text()
        for forbidden in ("urllib", "requests", "download.file", "install.packages", "kraken2", "bracken", "PRJNA1056765", "PRJCA046985", "shell=True"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
