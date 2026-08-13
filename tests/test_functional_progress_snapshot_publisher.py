import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_functional_progress_snapshot.sh"


def run(args, cwd, env=None):
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class FunctionalProgressSnapshotPublisherTests(unittest.TestCase):
    def test_status_only_publish_does_not_move_local_head_or_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            remote = root / "remote.git"
            work = root / "work"

            self.assertEqual(run(["git", "init", "--bare", str(remote)], root).returncode, 0)
            self.assertEqual(run(["git", "init", "-b", "main", str(work)], root).returncode, 0)
            self.assertEqual(run(["git", "config", "user.name", "Test User"], work).returncode, 0)
            self.assertEqual(run(["git", "config", "user.email", "test@example.invalid"], work).returncode, 0)
            (work / "README.md").write_text("base\n", encoding="utf-8")
            self.assertEqual(run(["git", "add", "README.md"], work).returncode, 0)
            self.assertEqual(run(["git", "commit", "-m", "base"], work).returncode, 0)
            self.assertEqual(run(["git", "remote", "add", "origin", str(remote)], work).returncode, 0)
            self.assertEqual(run(["git", "push", "-u", "origin", "main"], work).returncode, 0)

            local_head_before = run(["git", "rev-parse", "HEAD"], work).stdout.strip()
            status_dir = work / "reports_public" / "metagenome_functional_profile"
            status_dir.mkdir(parents=True)
            summary = {
                "state": "running",
                "route": "short_read_shared_index",
                "done_count": 1,
                "running_count": 1,
                "queued_count": 28,
                "failed_count": 0,
            }
            (status_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
            (status_dir / "runner_status.txt").write_text("state=running\n", encoding="utf-8")

            env = os.environ.copy()
            env["REPO_DIR"] = str(work)
            env["PYTHON_BIN"] = sys.executable
            result = run(["bash", str(SCRIPT)], work, env=env)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("functional_status_snapshot=published", result.stdout)

            local_head_after = run(["git", "rev-parse", "HEAD"], work).stdout.strip()
            self.assertEqual(local_head_before, local_head_after)
            porcelain = run(["git", "status", "--porcelain"], work).stdout
            self.assertTrue(porcelain.strip().startswith("?? reports_public"), porcelain)

            published = run(
                ["git", f"--git-dir={remote}", "show", "main:reports_public/metagenome_functional_profile/summary.json"],
                root,
            )
            self.assertEqual(published.returncode, 0, published.stdout)
            self.assertEqual(json.loads(published.stdout)["done_count"], 1)

            second = run(["bash", str(SCRIPT)], work, env=env)
            self.assertEqual(second.returncode, 0, second.stdout)
            self.assertIn("functional_status_snapshot=no_change", second.stdout)


if __name__ == "__main__":
    unittest.main()
