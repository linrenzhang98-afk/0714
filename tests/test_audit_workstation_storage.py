import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_workstation_storage import audit, classify, tree_bytes


class StorageAuditTests(unittest.TestCase):
    def test_metadata_audit_and_required_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = {key: root / key for key in ("control_plane", "legacy_results", "shared_database")}
            for path in roots.values():
                path.mkdir()
            (roots["control_plane"] / "state.json").write_bytes(b"metadata")
            (roots["legacy_results"] / "PRJNA1056765-results").mkdir()
            (roots["legacy_results"] / "PRJNA1056765-results" / "report.kreport").write_bytes(b"not parsed")
            output = root / "out"
            result = audit(output, roots=roots, filesystem_root=root)
            self.assertEqual(result["audit_type"], "read_only_workstation_storage_audit")
            self.assertEqual(result["summary"]["PRJNA1056765_BYTES"], len(b"not parsed"))
            payload = json.loads((output / "workstation_storage_audit.json").read_text(encoding="utf-8"))
            self.assertIn("DISK_TOTAL_BYTES", payload["summary"])
            self.assertIn("DISK_TOTAL_GIB=", (output / "workstation_storage_audit.txt").read_text(encoding="utf-8"))

    def test_conservative_classification(self):
        self.assertEqual(classify("PRJNA1056765-results"), "prjna1056765")
        self.assertEqual(classify("PRJCA046985-work"), "prjca046985")
        self.assertEqual(classify("historical-0714"), "other_0714")
        self.assertEqual(classify("mystery"), "unattributed_0714")

    def test_tree_does_not_follow_symlink_or_read_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "x").write_bytes(b"x")
            (root / "link").symlink_to(root / "x")
            self.assertEqual(tree_bytes(root), (1, 1))

    def test_source_has_no_processing_network_or_delete_operations(self):
        source = Path(__import__("scripts.audit_workstation_storage", fromlist=["__file__"]).__file__).read_text(encoding="utf-8")
        for forbidden in ("urllib", "requests", "subprocess", "hashlib", "unlink(", "rmtree(", "shutil.move"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
