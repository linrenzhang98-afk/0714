#!/usr/bin/env python3
"""Read-only, metadata-only ETYY workstation storage audit."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

ROOTS = {
    "control_plane": Path("/mnt/disk1/0714_control"),
    "legacy_results": Path("/mnt/disk1/db/kraken2/0714"),
    "shared_database": Path("/mnt/disk1/db/kraken2/k2_pluspfp_16gb_20221209"),
}

def tree_bytes(root: Path) -> tuple[int, int]:
    total = count = 0
    if not root.exists(): return 0, 0
    stack = [root]
    while stack:
        d = stack.pop()
        try: entries = os.scandir(d)
        except OSError: continue
        with entries:
            for e in entries:
                try:
                    if e.is_symlink(): continue
                    if e.is_dir(follow_symlinks=False): stack.append(Path(e.path))
                    elif e.is_file(follow_symlinks=False):
                        total += e.stat(follow_symlinks=False).st_size; count += 1
                except OSError: continue
    return total, count

def classify(name: str) -> str:
    n = name.lower()
    if "prjna1056765" in n: return "prjna1056765"
    if "prjca046985" in n: return "prjca046985"
    if any(x in n for x in ("common", "audit", "qc")): return "common_layer_audit_qc"
    if any(x in n for x in ("historical", "legacy", "other")): return "other_0714"
    return "unattributed_0714"

def audit(output: Path, roots: dict[str, Path] = ROOTS, filesystem_root: Path = Path("/mnt/disk1")) -> dict:
    sizes = {}; counts = {}
    for key, root in roots.items(): sizes[key], counts[key] = tree_bytes(root)
    cats = {k: [0, 0] for k in ("prjna1056765", "prjca046985", "common_layer_audit_qc", "other_0714", "unattributed_0714")}
    legacy = roots["legacy_results"]
    if legacy.exists():
        for e in os.scandir(legacy):
            if e.is_symlink(): continue
            b, c = tree_bytes(Path(e.path)) if e.is_dir(follow_symlinks=False) else ((e.stat(follow_symlinks=False).st_size, 1) if e.is_file(follow_symlinks=False) else (0, 0))
            cats[classify(e.name)][0] += b; cats[classify(e.name)][1] += c
    st = os.statvfs(filesystem_root)
    total = st.f_blocks * st.f_frsize; avail = st.f_bavail * st.f_frsize; used = total - st.f_bfree * st.f_frsize
    d = {"audit_type":"read_only_workstation_storage_audit", "roots": {k:{"path":str(roots[k]),"bytes":sizes[k],"file_count":counts[k]} for k in roots},
         "categories": {k:{"bytes":v[0],"file_count":v[1]} for k,v in cats.items()},
         "project_exclusive_total_bytes": sizes["control_plane"] + sizes["legacy_results"],
         "disk":{"total_bytes":total,"used_bytes":used,"available_bytes":avail,"used_percent":round(100*used/total,2) if total else 0},
         "shared_database_not_project_exclusive":True}
    summary = {
        "PROJECT_EXCLUSIVE_TOTAL_BYTES": d["project_exclusive_total_bytes"],
        "PRJNA1056765_BYTES": cats["prjna1056765"][0],
        "PRJCA046985_BYTES": cats["prjca046985"][0],
        "CONTROL_PLANE_BYTES": sizes["control_plane"],
        "OTHER_0714_BYTES": cats["other_0714"][0],
        "UNATTRIBUTED_0714_BYTES": cats["unattributed_0714"][0],
        "SHARED_KRAKEN2_DATABASE_BYTES": sizes["shared_database"],
        "DISK_TOTAL_BYTES": total, "DISK_USED_BYTES": used,
        "DISK_AVAILABLE_BYTES": avail, "DISK_USED_PERCENT": d["disk"]["used_percent"],
    }
    d["summary"] = summary
    output.mkdir(parents=True, exist_ok=True)
    (output/"workstation_storage_audit.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    lines=["WORKSTATION_STORAGE_AUDIT",f"PROJECT_EXCLUSIVE_TOTAL_BYTES={d['project_exclusive_total_bytes']}",f"PRJNA1056765_BYTES={cats['prjna1056765'][0]}",f"PRJCA046985_BYTES={cats['prjca046985'][0]}",f"CONTROL_PLANE_BYTES={sizes['control_plane']}",f"OTHER_0714_BYTES={cats['other_0714'][0]}",f"UNATTRIBUTED_0714_BYTES={cats['unattributed_0714'][0]}",f"SHARED_KRAKEN2_DATABASE_BYTES={sizes['shared_database']}",f"DISK_TOTAL_BYTES={total}",f"DISK_USED_BYTES={used}",f"DISK_AVAILABLE_BYTES={avail}",f"DISK_USED_PERCENT={d['disk']['used_percent']}",f"DISK_TOTAL_GIB={total/2**30:.3f}",f"DISK_TOTAL_TIB={total/2**40:.3f}",f"DISK_USED_GIB={used/2**30:.3f}",f"DISK_AVAILABLE_GIB={avail/2**30:.3f}"]
    lines.extend([f"{key}={value}" for key, value in summary.items()])
    (output/"workstation_storage_audit.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return d

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); args=p.parse_args(); audit(args.output_dir)
