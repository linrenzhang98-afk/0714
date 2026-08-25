import json
import subprocess
import sys
from pathlib import Path

import scripts.probe_r_czm_environment as probe


def test_no_rscript_condition(monkeypatch):
    monkeypatch.setattr(probe, "R_PAIRS", (("/definitely/missing/Rscript", "/definitely/missing/R"),))
    report = probe.build_report("synthetic-no-r")
    assert report["probe_status"] == "CZM_ENVIRONMENT_NOT_READY"
    assert report["reason"] == "RSCRIPT_NOT_FOUND"
    assert report["czm_probe"]["attempted"] is False


def test_parse_missing_package_fixture():
    parsed = probe.parse_r_output(
        "\n".join(
            [
                "KV\tr_version\tR version 4.4.0",
                "KV\tr_home\t/usr/lib/R",
                "KV\tr_library_paths\t/usr/lib/R/library",
                "PKG\tzCompositions.installed\tFALSE",
                "PKG\tNADA.installed\tTRUE",
                "PKG\tNADA.version\t1.6-1",
            ]
        )
    )
    assert parsed["r_version"] == "R version 4.4.0"
    assert parsed["packages"]["zCompositions"]["installed"] == "FALSE"
    assert parsed["packages"]["NADA"]["version"] == "1.6-1"


def test_malformed_r_output_is_reported():
    parsed = probe.parse_r_output("KV\tr_version\tR\nnot-a-protocol-line\n")
    assert parsed["malformed_lines"] == ["not-a-protocol-line"]


def test_probe_source_has_no_network_or_installation_calls():
    source = Path(probe.__file__).read_text(encoding="utf-8")
    for forbidden in ("install.packages", "BiocManager", "download.file", "curl", "wget", "shell=True"):
        assert forbidden not in source


def test_script_compiles_and_writes_bounded_outputs(tmp_path):
    output = tmp_path / "out"
    completed = subprocess.run(
        [sys.executable, "scripts/probe_r_czm_environment.py", "--job-id", "synthetic", "--output-dir", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    report = json.loads((output / "r_czm_environment_probe.json").read_text())
    assert report["biological_analysis_executed"] is False
    assert (output / "result.json").is_file()
    assert (output / "r_czm_environment_probe_summary.md").is_file()
