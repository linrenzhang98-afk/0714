#!/usr/bin/env python3
"""QIIME2 amplicon pipeline wrapper.

This wrapper validates inputs and writes an executable shell plan. It does not
delete raw data or overwrite existing results. In publication-oriented automatic
mode, DADA2 uses explicit truncation parameters when present; otherwise it uses
no truncation for a first-pass run and records that choice in the validation
report.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_job(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def command_exists(command: str) -> bool:
    if Path(command).is_absolute():
        return Path(command).exists()
    return subprocess.run(["bash", "-lc", f"command -v {sh_quote(command)}"], check=False).returncode == 0


def qiime_shell_command(qiime_bin: str) -> str:
    cleanup = "unset R_HOME R_LIBS R_LIBS_USER R_LIBS_SITE PYTHONPATH"
    if Path(qiime_bin).is_absolute():
        qiime_dir = str(Path(qiime_bin).parent)
        return f"{cleanup}; export PATH={sh_quote(qiime_dir)}:${{PATH:-}}; {sh_quote(qiime_bin)}"
    return f"{cleanup}; {sh_quote(qiime_bin)}"


def require_file(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists() or not path.is_file():
        errors.append(f"{label} not found: {path}")


def run_checked(args: list[str], log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if log_path is not None:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "args": args,
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            }, ensure_ascii=False) + "\n")
    return result


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_download(path: Path, url: str, sha256: str | None, errors: list[str]) -> None:
    if path.exists():
        if sha256 and sha256_file(path).lower() != sha256.lower():
            errors.append(f"checksum mismatch for existing file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"download failed for {url}: {exc}")
        return
    if sha256 and sha256_file(path).lower() != sha256.lower():
        errors.append(f"checksum mismatch after download: {path}")


def is_gzip_file(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


def ensure_gzip_fastq(path: Path, destination: Path, errors: list[str]) -> Path:
    if destination.exists() and is_gzip_file(destination):
        return destination
    if not path.exists():
        errors.append(f"FASTQ file not found for gzip conversion: {path}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("rb") as src, gzip.open(destination, "wb") as dst:
            shutil.copyfileobj(src, dst)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"gzip conversion failed for {path}: {exc}")
    return destination


def write_manifest_from_sra(params: dict[str, Any], out_dir: Path, errors: list[str]) -> Path | None:
    run_accessions = params.get("run_accessions", [])
    if not isinstance(run_accessions, list) or not run_accessions:
        errors.append("params.run_accessions must be a non-empty list when manifest is not provided")
        return None

    work_dir = Path(params.get("work_dir", out_dir / "work"))
    sra_dir = work_dir / "sra"
    fastq_dir = work_dir / "fastq"
    qiime_fastq_dir = out_dir / "input_fastq"
    sra_dir.mkdir(parents=True, exist_ok=True)
    fastq_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "command_log.jsonl"
    threads = int(params.get("threads", max(1, (os.cpu_count() or 2) - 1)))
    run_to_sample = params.get("run_to_sample", {})
    if not isinstance(run_to_sample, dict):
        run_to_sample = {}

    manifest = out_dir / "manifest.tsv"
    rows = ["sample-id\tforward-absolute-filepath\treverse-absolute-filepath"]
    for run in [str(r).strip() for r in run_accessions if str(r).strip()]:
        sample_id = str(run_to_sample.get(run, run))
        sra_path = sra_dir / run / f"{run}.sra"
        if not sra_path.exists():
            result = run_checked(["prefetch", run, "--output-directory", str(sra_dir)], log_path)
            if result.returncode != 0:
                errors.append(f"prefetch failed for {run}: {result.stderr[-300:]}")
                continue

        forward = fastq_dir / f"{run}_1.fastq"
        reverse = fastq_dir / f"{run}_2.fastq"
        if not forward.exists() or not reverse.exists():
            source = sra_path if sra_path.exists() else sra_dir / f"{run}.sra"
            result = run_checked(
                ["fasterq-dump", str(source), "--split-files", "--outdir", str(fastq_dir), "--threads", str(threads)],
                log_path,
            )
            if result.returncode != 0:
                errors.append(f"fasterq-dump failed for {run}: {result.stderr[-300:]}")
                continue
        if not forward.exists() or not reverse.exists():
            errors.append(f"paired FASTQ files missing for {run}")
            continue
        forward_gz = ensure_gzip_fastq(forward, qiime_fastq_dir / f"{run}_1.fastq.gz", errors)
        reverse_gz = ensure_gzip_fastq(reverse, qiime_fastq_dir / f"{run}_2.fastq.gz", errors)
        if errors:
            continue
        rows.append(f"{sample_id}\t{forward_gz.resolve()}\t{reverse_gz.resolve()}")

    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and plan QIIME2 amplicon analysis")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job_path = Path(args.job)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    job = load_job(job_path)
    params = job.get("params", {})

    execute_mode = params.get("execute_mode", "plan_only")
    manifest_value = params.get("manifest", "")
    manifest = Path(manifest_value) if manifest_value else Path()
    metadata = Path(params.get("metadata", ""))
    classifier_value = params.get("taxonomy_classifier", "")
    classifier = Path(classifier_value) if classifier_value else Path()
    classifier_url = params.get("taxonomy_classifier_url", "")
    classifier_sha256 = params.get("taxonomy_classifier_sha256", "")
    qiime_bin = str(params.get("qiime_bin", "qiime"))
    read_type = params.get("read_type", "paired")
    threads = int(params.get("threads", max(1, (os.cpu_count() or 2) - 1)))
    trunc_len_f = params.get("trunc_len_f")
    trunc_len_r = params.get("trunc_len_r")
    trim_left_f = int(params.get("trim_left_f", 0))
    trim_left_r = int(params.get("trim_left_r", 0))
    sampling_depth = int(params.get("diversity_sampling_depth", 1000))
    metadata_column = str(params.get("metadata_group_column", "analysis_group"))
    full_modes = {"full_auto", "publication_full"}
    qiime_cmd = qiime_shell_command(qiime_bin)

    errors: list[str] = []
    if not manifest_value and params.get("run_accessions"):
        for command in ["prefetch", "fasterq-dump"]:
            if shutil.which(command) is None:
                errors.append(f"{command} command not found in PATH or active environment")
        if not errors and execute_mode in ({"sra_demux", "demux_only"} | full_modes):
            generated_manifest = write_manifest_from_sra(params, out_dir, errors)
            if generated_manifest is not None:
                manifest = generated_manifest
        else:
            manifest = out_dir / "manifest.tsv"
    require_file(manifest, "manifest", errors)
    require_file(metadata, "metadata", errors)
    if read_type not in {"paired", "single"}:
        errors.append("read_type must be paired or single")
    if not command_exists(qiime_bin):
        errors.append(f"qiime command not found: {qiime_bin}")
    if execute_mode in full_modes and classifier_value and classifier_url:
        ensure_download(classifier, str(classifier_url), str(classifier_sha256 or ""), errors)
    if classifier_value and execute_mode in full_modes:
        require_file(classifier, "taxonomy_classifier", errors)

    decision_log = out_dir / "decision_request.md"
    warnings: list[str] = []
    if read_type == "paired" and (trunc_len_f is None or trunc_len_r is None) and execute_mode not in full_modes:
        decision_log.write_text(
            "# Decision Required\n\n"
            "DADA2 paired-end truncation lengths are missing.\n\n"
            "Run demux summarize first, inspect quality plots, then set `trunc_len_f` and `trunc_len_r` in the job JSON.\n",
            encoding="utf-8",
        )
    if read_type == "paired" and (trunc_len_f is None or trunc_len_r is None) and execute_mode in full_modes:
        trunc_len_f = 0
        trunc_len_r = 0
        warnings.append("DADA2 full_auto used no truncation because trunc_len_f/trunc_len_r were not provided.")

    report = {
        "job_id": job.get("job_id"),
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline": "amplicon_qiime2",
        "errors": errors,
        "warnings": warnings + (["DADA2 denoising is omitted until truncation parameters are provided"] if decision_log.exists() else []),
        "execute_mode": execute_mode,
        "target_outputs": [
            "species/genus composition",
            "taxa barplot",
            "alpha and beta diversity",
            "group difference testing",
            "publication-oriented interpretation notes",
        ],
    }
    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"mkdir -p {sh_quote(str(out_dir / 'qiime2'))}",
        f"{qiime_cmd} tools import --type 'SampleData[PairedEndSequencesWithQuality]' --input-path {sh_quote(str(manifest))} --output-path {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --input-format PairedEndFastqManifestPhred33V2"
        if read_type == "paired"
        else f"{qiime_cmd} tools import --type 'SampleData[SequencesWithQuality]' --input-path {sh_quote(str(manifest))} --output-path {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --input-format SingleEndFastqManifestPhred33V2",
        f"{qiime_cmd} demux summarize --i-data {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'demux.qzv'))}",
    ]
    if read_type == "paired" and trunc_len_f is not None and trunc_len_r is not None:
        commands.append(
            f"{qiime_cmd} dada2 denoise-paired "
            f"--i-demultiplexed-seqs {sh_quote(str(out_dir / 'qiime2' / 'demux.qza'))} "
            f"--p-trim-left-f {trim_left_f} --p-trim-left-r {trim_left_r} "
            f"--p-trunc-len-f {int(trunc_len_f)} --p-trunc-len-r {int(trunc_len_r)} "
            f"--p-n-threads {threads} "
            f"--o-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} "
            f"--o-representative-sequences {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qza'))} "
            f"--o-denoising-stats {sh_quote(str(out_dir / 'qiime2' / 'denoising-stats.qza'))}"
        )
        commands.append(
            f"{qiime_cmd} feature-classifier classify-sklearn "
            f"--i-classifier {sh_quote(str(classifier))} "
            f"--i-reads {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qza'))} "
            f"--o-classification {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))}"
        )
        commands.extend([
            f"{qiime_cmd} feature-table summarize --i-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} --m-sample-metadata-file {sh_quote(str(metadata))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'table.qzv'))}",
            f"{qiime_cmd} feature-table tabulate-seqs --i-data {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qza'))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'rep-seqs.qzv'))}",
            f"{qiime_cmd} metadata tabulate --m-input-file {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qzv'))}",
            f"{qiime_cmd} taxa barplot --i-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} --i-taxonomy {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))} --m-metadata-file {sh_quote(str(metadata))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'taxa-bar-plots.qzv'))}",
            f"{qiime_cmd} taxa collapse --i-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} --i-taxonomy {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))} --p-level 6 --o-collapsed-table {sh_quote(str(out_dir / 'qiime2' / 'genus-table.qza'))}",
            f"{qiime_cmd} taxa collapse --i-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} --i-taxonomy {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))} --p-level 7 --o-collapsed-table {sh_quote(str(out_dir / 'qiime2' / 'species-table.qza'))}",
            f"{qiime_cmd} feature-table relative-frequency --i-table {sh_quote(str(out_dir / 'qiime2' / 'genus-table.qza'))} --o-relative-frequency-table {sh_quote(str(out_dir / 'qiime2' / 'genus-relative-table.qza'))}",
            f"{qiime_cmd} feature-table relative-frequency --i-table {sh_quote(str(out_dir / 'qiime2' / 'species-table.qza'))} --o-relative-frequency-table {sh_quote(str(out_dir / 'qiime2' / 'species-relative-table.qza'))}",
            f"{qiime_cmd} diversity core-metrics --i-table {sh_quote(str(out_dir / 'qiime2' / 'table.qza'))} --p-sampling-depth {sampling_depth} --m-metadata-file {sh_quote(str(metadata))} --output-dir {sh_quote(str(out_dir / 'qiime2' / 'core-metrics'))}",
            f"{qiime_cmd} diversity alpha-group-significance --i-alpha-diversity {sh_quote(str(out_dir / 'qiime2' / 'core-metrics' / 'shannon_vector.qza'))} --m-metadata-file {sh_quote(str(metadata))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'shannon-group-significance.qzv'))}",
            f"{qiime_cmd} diversity beta-group-significance --i-distance-matrix {sh_quote(str(out_dir / 'qiime2' / 'core-metrics' / 'bray_curtis_distance_matrix.qza'))} --m-metadata-file {sh_quote(str(metadata))} --m-metadata-column {sh_quote(metadata_column)} --p-pairwise --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'bray-curtis-group-significance.qzv'))}",
            f"mkdir -p {sh_quote(str(out_dir / 'exports'))}",
            f"{qiime_cmd} tools export --input-path {sh_quote(str(out_dir / 'qiime2' / 'genus-relative-table.qza'))} --output-path {sh_quote(str(out_dir / 'exports' / 'genus_relative_table'))}",
            f"{qiime_cmd} tools export --input-path {sh_quote(str(out_dir / 'qiime2' / 'species-relative-table.qza'))} --output-path {sh_quote(str(out_dir / 'exports' / 'species_relative_table'))}",
            f"{qiime_cmd} tools export --input-path {sh_quote(str(out_dir / 'qiime2' / 'taxonomy.qza'))} --output-path {sh_quote(str(out_dir / 'exports' / 'taxonomy'))}",
            f"if {qiime_cmd} composition ancombc --help >/dev/null 2>&1; then "
            f"{qiime_cmd} composition ancombc --i-table {sh_quote(str(out_dir / 'qiime2' / 'genus-table.qza'))} --m-metadata-file {sh_quote(str(metadata))} --p-formula {sh_quote(metadata_column)} --o-differentials {sh_quote(str(out_dir / 'qiime2' / 'genus-ancombc.qza'))} "
            f"&& {qiime_cmd} composition tabulate --i-data {sh_quote(str(out_dir / 'qiime2' / 'genus-ancombc.qza'))} --o-visualization {sh_quote(str(out_dir / 'qiime2' / 'genus-ancombc.qzv'))}; "
            "else echo 'QIIME2 composition ancombc unavailable; skipping ANCOM-BC.'; fi",
        ])
    (out_dir / "run_plan.sh").write_text("\n".join(commands) + "\n", encoding="utf-8")

    if errors:
        return 2
    if execute_mode in ({"demux_only", "sra_demux"} | full_modes):
        log_path = out_dir / "command_log.jsonl"
        for raw in commands[2:5]:
            result = run_checked(["bash", "-lc", raw], log_path)
            if result.returncode != 0:
                errors.append(f"command failed: {raw}")
                report["errors"] = errors
                (out_dir / "validation_report.json").write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                return 2
        if execute_mode in full_modes:
            for raw in commands[5:]:
                result = run_checked(["bash", "-lc", raw], log_path)
                if result.returncode != 0:
                    errors.append(f"command failed: {raw}")
                    report["errors"] = errors
                    (out_dir / "validation_report.json").write_text(
                        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    return 2
            report["completed_outputs"] = {
                "table_qza": str(out_dir / "qiime2" / "table.qza"),
                "taxonomy_qza": str(out_dir / "qiime2" / "taxonomy.qza"),
                "taxa_barplot_qzv": str(out_dir / "qiime2" / "taxa-bar-plots.qzv"),
                "core_metrics_dir": str(out_dir / "qiime2" / "core-metrics"),
                "exports_dir": str(out_dir / "exports"),
            }
            (out_dir / "validation_report.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
