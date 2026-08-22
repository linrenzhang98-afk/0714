#!/usr/bin/env python3
"""Strict zero-data identity preflight for the reviewed ETYY Kraken2 executable."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


KRAKEN2 = "/home/suma/anaconda3/envs/mgshotgun/bin/kraken2"
EXPECTED_REALPATH = "/home/suma/anaconda3/envs/mgshotgun/share/kraken2-2.17.1/libexec/kraken2"
EXPECTED_SIZE = 8189
EXPECTED_SHA256 = "73655abe4655e0509c167e3f2532a6c92845572520a216704c9fc91bbfe77ec3"
EXPECTED_VERSION = "Kraken version 2.17.1"
CONTROLLED_ENVIRONMENT = {
    "PATH": "/home/suma/anaconda3/envs/mgshotgun/bin:/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
}


class IdentityError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify() -> None:
    executable = Path(KRAKEN2)
    if os.path.realpath(KRAKEN2) != EXPECTED_REALPATH:
        raise IdentityError("Kraken2 realpath mismatch")
    if executable.stat().st_size != EXPECTED_SIZE:
        raise IdentityError("Kraken2 executable size mismatch")
    if sha256(executable) != EXPECTED_SHA256:
        raise IdentityError("Kraken2 executable SHA256 mismatch")
    result = subprocess.run(
        [KRAKEN2, "--version"],
        shell=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env=CONTROLLED_ENVIRONMENT,
    )
    if result.returncode != 0:
        raise IdentityError("Kraken2 version probe returned nonzero")
    first_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
    if first_line != EXPECTED_VERSION:
        raise IdentityError("Kraken2 version line mismatch")


def main() -> int:
    try:
        verify()
    except (IdentityError, OSError, subprocess.SubprocessError) as exc:
        print(f"ETYY_KRAKEN2_IDENTITY_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("ETYY_KRAKEN2_IDENTITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
