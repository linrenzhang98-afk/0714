import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Humann30DownstreamTests(unittest.TestCase):
    def test_unavailable_root_is_not_data_qc_failure(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "audit"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/audit_humann_30_outputs.py"),
                "--input-root", str(Path(td) / "absent"),
                "--cohort", str(ROOT / "reports_public/metagenome_functional_profile/run_status.tsv"),
                "--output-dir", str(out),
            ], check=False)
            summary = json.loads((out / "audit_summary.json").read_text())
            self.assertEqual(result.returncode, 3)
            self.assertEqual(summary["audit_state"], "INPUT_UNAVAILABLE")
            self.assertEqual(summary["fail"], 0)
            self.assertEqual(summary["not_run"], 90)

    def test_header_only_pathway_is_real_failure(self):
        spec = importlib.util.spec_from_file_location("audit", ROOT / "scripts/audit_humann_30_outputs.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.tsv"; path.write_text("# Pathway\tsample_Abundance\n")
            row = mod.inspect(path, "SRR27344041", "pathabundance", 1024)
            self.assertEqual(row["status"], "FAIL")
            self.assertIn("header_only", row["flags"])

    def test_synthetic_fixed_30_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inputs=root/"inputs"; out=root/"out"; cohort=root/"cohort.tsv"; species=root/"species.tsv"
            runs=[f"S{i:02d}" for i in range(30)]
            with cohort.open("w",newline="") as h:
                w=csv.writer(h,delimiter="\t"); w.writerow(["run","pathogen_group","status"])
                for i,s in enumerate(runs): w.writerow([s,f"G{i%5}","done"])
            with species.open("w",newline="") as h:
                w=csv.writer(h,delimiter="\t"); w.writerow(["run","pathogen_group","G0 species"])
                for i,s in enumerate(runs): w.writerow([s,f"G{i%5}",i/30])
            for i,s in enumerate(runs):
                d=inputs/s; d.mkdir(parents=True)
                for kind in ("genefamilies","pathabundance","pathcoverage"):
                    (d/f"{s}_{kind}.tsv").write_text(f"# feature\t{s}\nF1\t{i+1}\nF2|taxon\t1\n")
            audit=root/"audit.json"; audit.write_text(json.dumps({"audit_passed":True}))
            result=subprocess.run([sys.executable,str(ROOT/"scripts/run_humann_30_downstream.py"),"--input-root",str(inputs),"--cohort",str(cohort),"--audit-summary",str(audit),"--species-matrix",str(species),"--out",str(out),"--permutations","9"],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((out/"joined/pathabundance.tsv.gz").is_file())
            self.assertTrue((out/"figures/pathabundance_pcoa.svg").is_file())
            self.assertTrue((out/"statistics/pathogen_group_pathway_exploration.tsv").is_file())
            self.assertIn("selected_deep_review_only",(out/"parameters.json").read_text())
            cluster=(out/"statistics/cluster_order.tsv").read_text().splitlines()[0]
            self.assertIn("average_linkage_cluster_k5",cluster)


if __name__ == "__main__": unittest.main()
