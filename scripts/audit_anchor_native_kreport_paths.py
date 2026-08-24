#!/usr/bin/env python3
"""Bounded metadata-only inventory of frozen native Kraken2 report paths."""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path

RUN_RE = re.compile(r"SRR\d+")
FAILED_GLOB_ASSUMPTION = "prjna1056765_production_descriptive_batch_*/kraken2/SRR27343191.kreport"

def frozen_runs(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h, delimiter="\t"))
    vals = [r.get("run", "") for r in rows]
    if len(vals) != 400 or len(set(vals)) != 400 or not all(RUN_RE.fullmatch(x) for x in vals):
        raise ValueError("frozen membership must contain exactly 400 unique SRR runs")
    return vals

def classify_native_path(path: Path, root: Path, runs: set[str]) -> str | None:
    """Native rule: exact <RUN>.kreport directly beneath any kraken2 directory."""
    if path.is_symlink() or not path.is_file() or not path.is_relative_to(root):
        return None
    try:
        if not path.resolve().is_relative_to(root.resolve()):
            return None
    except OSError:
        return None
    if path.name.endswith("_bracken_species.kreport"):
        return None
    parts = path.relative_to(root).parts
    if len(parts) < 2 or parts[-2] != "kraken2":
        return None
    m = re.fullmatch(r"(SRR\d+)\.kreport", path.name)
    return m.group(1) if m and (not runs or m.group(1) in runs) else None

def native_candidates(root: Path, runs: set[str]) -> dict[str, list[Path]]:
    """Inventory only authoritative historical native report paths."""
    if not root.is_dir():
        raise FileNotFoundError(root)
    out = {r: [] for r in runs}
    for p in root.rglob("*.kreport"):
        run = classify_native_path(p, root, runs)
        if run:
            out[run].append(p)
    return out

def eligible_runs(root: Path) -> set[str]:
    found = set()
    for p in root.rglob("*.kreport"):
        run = classify_native_path(p, root, set())
        if run:
            found.add(run)
    return found

def all_matching_paths(root: Path, run: str) -> list[Path]:
    """List matching report paths using metadata only; never open a report."""
    found = []
    for p in root.rglob("*.kreport"):
        if p.is_symlink() or not p.is_file() or not p.is_relative_to(root):
            continue
        try:
            if not p.resolve().is_relative_to(root.resolve()):
                continue
        except OSError:
            continue
        if run in p.name:
            found.append(p)
    return sorted(found, key=str)

def audit(root: Path, membership: Path, out: Path) -> dict:
    runs = frozen_runs(membership)
    candidates = native_candidates(root, set(runs))
    missing = sorted(r for r in runs if not candidates[r])
    dup = sorted(r for r in runs if len(candidates[r]) > 1)
    rows = []
    for run in sorted(runs):
        paths = sorted(candidates[run], key=str)
        native = paths[0] if len(paths) == 1 else None
        rows.append({"run": run, "native_candidate_count": len(paths),
                     "native_candidate_paths": [str(p) for p in paths],
                     "native_path": str(native) if native else None,
                     "relative_path": str(native.relative_to(root)) if native else None,
                     "file_size_bytes": native.stat().st_size if native else None})
    special_native = candidates.get("SRR27343191", [])
    special_all = all_matching_paths(root, "SRR27343191")
    actual = str(special_native[0]) if len(special_native) == 1 else None
    if actual:
        relative = str(Path(actual).relative_to(root))
        failed_reason = ("actual path matches the failed glob assumption"
                         if Path(relative).match(FAILED_GLOB_ASSUMPTION)
                         else "actual relative path does not match failed glob: " + relative)
    else:
        failed_reason = "no unique authoritative native path recovered"
    data = {"audit_type": "bounded_anchor_native_kreport_path_audit", "approved_root": str(root),
            "frozen_runs": len(runs), "native_unique_runs": sum(bool(candidates[r]) for r in runs),
            "native_report_files": sum(len(candidates[r]) for r in runs), "missing_runs": missing,
            "duplicate_runs": dup, "unexpected_runs": sorted(eligible_runs(root) - set(runs)), "reconciliation_generator_found": False,
            "reconciliation_generator_path": "NONE", "reconciliation_generator_commit": "NONE",
            "srr27343191": {"candidate_count": len(special_all), "candidate_paths": [str(p) for p in special_all],
                            "native_candidate_count": len(special_native),
                            "native_candidate_paths": [str(p) for p in special_native],
                            "authoritative_native_path": actual,
                            "failed_glob_reason": failed_reason},
            "failed_glob_assumption": FAILED_GLOB_ASSUMPTION, "actual_path": actual,
            "path_structure_summary": {"candidate_suffix": "exact <RUN>.kreport under kraken2",
                                        "bracken_excluded_suffix": "*_bracken_species.kreport",
                                        "derived_suffixes_excluded": True},
            "per_run_paths": rows}
    data["path_inventory_status"] = "EXACT_400_RECOVERED" if not missing and not dup and len(runs)==400 else "SAFE_STOP"
    out.mkdir(parents=True, exist_ok=True)
    (out / "anchor_native_report_path_audit.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    (out / "anchor_native_report_path_audit.txt").write_text("PATH_INVENTORY_STATUS="+data["path_inventory_status"]+"\n"+"SRR27343191_ACTUAL_PATH="+str(data["actual_path"])+"\n", encoding="utf-8")
    return data

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--results-root", type=Path, required=True); ap.add_argument("--membership", type=Path, required=True); ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args(); audit(args.results_root, args.membership, args.output_dir); return 0
if __name__ == "__main__": raise SystemExit(main())
