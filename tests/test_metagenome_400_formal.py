import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class Metagenome400FormalTests(unittest.TestCase):
    def test_checked_in_cohort_audit(self):
        with tempfile.TemporaryDirectory() as td:
            result=subprocess.run([sys.executable,str(ROOT/"scripts/audit_prjna1056765_metagenome_400.py"),"--out",td],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads((Path(td)/"data_availability.json").read_text())
            self.assertEqual(data["analysis_cohort_runs"],400)
            self.assertEqual(data["production_status_counts"],{"done":400})
            self.assertEqual(data["deep_review_overlap"],30)
            inventory=(Path(td)/"metadata_inventory.tsv").read_text()
            self.assertIn("NOT independent; abundance-derived",inventory)

    def test_completed_formal_outputs_preserve_inference_boundaries(self):
        import csv
        root=ROOT/"reports_public/metagenome_400_formal"
        summary=json.loads((root/"summary.json").read_text())
        self.assertEqual(summary["cohort_n"],400)
        self.assertEqual(summary["diagnosis_species_FDR_lt_0.05"],5)
        with (root/"statistics/permanova_permdisp.tsv").open() as handle:
            inference=list(csv.DictReader(handle,delimiter="\t"))
        self.assertTrue(all(row["permutations"]=="9999" for row in inference))
        bray=next(row for row in inference if row["metric"]=="Bray-Curtis" and row["sample_set"]=="full")
        self.assertLess(float(bray["PERMDISP_p"]),.05)
        humann=json.loads((root/"integration_30/humann_publication_review/summary.json").read_text())
        self.assertEqual(len(humann["pathway_zero_biological_samples"]),6)
        self.assertEqual(humann["scope"],"selected_deep_review_functional_exploration_only")


if __name__=="__main__": unittest.main()
