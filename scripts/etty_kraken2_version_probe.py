#!/usr/bin/env python3
"""Capture bounded runtime identity for the reviewed ETYY Kraken2 executable."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


KRAKEN2 = "/home/suma/anaconda3/envs/mgshotgun/bin/kraken2"
TEXT_LIMIT = 4000


def bounded(value: str) -> str:
    return value[:TEXT_LIMIT]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.executable != KRAKEN2:
        parser.error(f"--executable must be exactly {KRAKEN2}")

    executable = Path(args.executable)
    try:
        result = subprocess.run(
            [args.executable, "--version"],
            shell=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        stdout = bounded(result.stdout)
        stderr = bounded(result.stderr)
        payload = {
            "probe_type": "kraken2_version_runtime_probe",
            "executable": args.executable,
            "realpath": os.path.realpath(args.executable),
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_stripped": stdout.strip(),
            "stderr_stripped": stderr.strip(),
            "combined_nonempty_lines": [
                line for line in (stdout + "\n" + stderr).splitlines() if line.strip()
            ],
            "executable_size_bytes": executable.stat().st_size,
            "executable_sha256": sha256(executable),
            "python_executable": sys.executable,
            "environment": {
                "PATH": bounded(os.environ.get("PATH", "")),
                "LANG": bounded(os.environ.get("LANG", "")),
                "LC_ALL": bounded(os.environ.get("LC_ALL", "")),
            },
        }
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"version probe invocation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(args.output)
    except OSError as exc:
        print(f"version probe output failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
