#!/usr/bin/env python3
"""Example backup task placeholder.

This script intentionally does not copy files. Replace it with a reviewed backup
implementation that writes only inside approved directories.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "job_id": job["job_id"],
        "task": job["task"],
        "status": "placeholder_only",
        "note": "No files were copied by this demo script."
    }
    (out_dir / "backup_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
