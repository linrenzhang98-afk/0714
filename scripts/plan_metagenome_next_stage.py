#!/usr/bin/env python3
"""Plan host-removal and AMR next-stage analysis readiness.

This script only inspects existing files and command availability. It does not
download data, install software, build indexes, or run analysis.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AMRFINDER_CANDIDATE_PATHS = [
    "/home/suma/anaconda3/envs/mgshotgun/bin/amrfinder",
    "/home/suma/anaconda3/envs/clinical_meta/bin/amrfinder",
    "/home/suma/anaconda3/envs/metag_env/bin/amrfinder",
    "/home/suma/anaconda3/bin/amrfinder",
    "/usr/local/bin/amrfinder",
    "/usr/bin/amrfinder",
]
AMRFINDER_ENV_PREFIX = "/home/suma/anaconda3/envs/mgshotgun"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def command_row(name: str) -> dict[str, str]:
    path = shutil.which(name) or ""
    if not path and name == "amrfinder":
        for candidate in AMRFINDER_CANDIDATE_PATHS:
            candidate_path = Path(candidate)
            if candidate_path.exists() and os.access(candidate_path, os.X_OK):
                path = str(candidate_path)
                break
    return {"command": name, "available": "yes" if path else "no", "path": path}


def bowtie2_index_exists(prefix: str) -> bool:
    if not prefix:
        return False
    expected = [f"{prefix}.{suffix}.bt2" for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    expected_large = [f"{prefix}.{suffix}.bt2l" for suffix in ["1", "2", "3", "4", "rev.1", "rev.2"]]
    return all(Path(p).exists() for p in expected) or all(Path(p).exists() for p in expected_large)


def amrfinder_env(command_path: str) -> dict[str, str]:
    env = os.environ.copy()
    if "/envs/mgshotgun/" in command_path:
        env.setdefault("CONDA_PREFIX", AMRFINDER_ENV_PREFIX)
        env["PATH"] = f"{AMRFINDER_ENV_PREFIX}/bin:/home/suma/anaconda3/bin:" + env.get("PATH", "")
    return env


def amrfinder_database_ready(db_dir: str = "") -> bool:
    amrfinder = command_row("amrfinder")["path"]
    if not amrfinder:
        return False
    args = [amrfinder, "-V"]
    if db_dir:
        args.extend(["-d", db_dir])
    result = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=amrfinder_env(amrfinder),
    )
    text = (result.stdout + "\n" + result.stderr).lower()
    return result.returncode == 0 and "database" in text


def setup_recommendations(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("export ") and "=" in line:
            key, value = line.replace("export ", "", 1).split("=", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan metagenome host-removal/AMR next stage")
    parser.add_argument("--deep-review", default="reports_public/metagenome_deep_review/deep_review_samples.tsv")
    parser.add_argument("--summary", default="reports_public/metagenome_deep_review_summary/summary.json")
    parser.add_argument("--out-dir", default="reports_public/metagenome_next_stage")
    parser.add_argument("--host-index-prefix", default=os.environ.get("HOST_INDEX_PREFIX", ""))
    parser.add_argument("--amr-db-dir", default=os.environ.get("AMR_DB_DIR", ""))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_tsv(Path(args.deep_review))
    setup_env = setup_recommendations(Path("reports_public/metagenome_next_stage_setup/env_recommendations.sh"))
    host_index_prefix = args.host_index_prefix or setup_env.get("HOST_INDEX_PREFIX", "")
    amr_db_dir = args.amr_db_dir or setup_env.get("AMR_DB_DIR", "")

    commands = [
        command_row(name)
        for name in [
            "fastp",
            "bowtie2",
            "samtools",
            "kraken2",
            "bracken",
            "abricate",
            "rgi",
            "amrfinder",
            "diamond",
        ]
    ]
    with (out_dir / "tool_readiness.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["command", "available", "path"], delimiter="\t")
        writer.writeheader()
        writer.writerows(commands)

    host_ready = bowtie2_index_exists(host_index_prefix)
    amr_db_ready = amrfinder_database_ready(amr_db_dir)
    command_map = {row["command"]: row["available"] == "yes" for row in commands}
    qc_ready = command_map.get("fastp", False)
    host_tool_ready = command_map.get("bowtie2", False) and command_map.get("samtools", False)
    amr_tool_ready = any(command_map.get(name, False) for name in ["abricate", "rgi", "amrfinder", "diamond"])

    blockers: list[str] = []
    if not rows:
        blockers.append("Deep-review sample table is missing or empty.")
    if not qc_ready:
        blockers.append("fastp is not available.")
    if not host_tool_ready:
        blockers.append("bowtie2 and/or samtools are not available.")
    if not host_ready:
        blockers.append("HOST_INDEX_PREFIX is not configured or Bowtie2 host index files are missing.")
    if not amr_tool_ready:
        blockers.append("No AMR tool detected among abricate, rgi, amrfinder, diamond.")
    if not amr_db_ready:
        blockers.append("AMR_DB_DIR is not configured or AMRFinderPlus cannot validate the database.")

    recommended_stage = "report_interpretation_only"
    if qc_ready and command_map.get("kraken2", False) and command_map.get("bracken", False):
        recommended_stage = "qc_kraken_bracken_completed_or_available"
    if qc_ready and host_tool_ready and host_ready:
        recommended_stage = "host_removal_validation_ready"
    if qc_ready and host_tool_ready and host_ready and amr_tool_ready and amr_db_ready:
        recommended_stage = "host_removal_and_amr_ready"

    lines = [
        "# Metagenome Next-Stage Readiness",
        "",
        f"Generated at: {utc_now()}",
        f"Deep-review samples: {len(rows)}",
        f"Recommended stage: `{recommended_stage}`",
        "",
        "## Readiness",
        "",
        f"- QC ready: {qc_ready}",
        f"- Host-removal tools ready: {host_tool_ready}",
        f"- Host index ready: {host_ready}",
        f"- AMR tool ready: {amr_tool_ready}",
        f"- AMR database ready: {amr_db_ready}",
        f"- Host index prefix: `{host_index_prefix or 'not configured'}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Do not start AMR or host-removal execution until the setup status reports host index and AMRFinderPlus database ready.",
            "The completed deep-review Kraken2/Bracken results are stable enough for report interpretation now.",
            "",
            "## Output Files",
            "",
            "- `tool_readiness.tsv`",
        ]
    )
    (out_dir / "readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if blockers:
        Path("decision_requests").mkdir(exist_ok=True)
        (Path("decision_requests") / "metagenome_host_amr_requirements.md").write_text(
            "# Host-removal / AMR requirements\n\n"
            "The current Kraken2/Bracken analysis is complete. Starting host-removal or AMR requires additional local configuration.\n\n"
            "## Required before execution\n\n"
            + "\n".join(f"- {item}" for item in blockers)
            + "\n\n"
            "The status publisher is configured to prepare the GRCh38 Bowtie2 host index and AMRFinderPlus database automatically.\n",
            encoding="utf-8",
        )
    else:
        request = Path("decision_requests") / "metagenome_host_amr_requirements.md"
        if request.exists():
            request.unlink()
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
