import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

PROJECT = Path(__file__).parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass
    def do_GET(self):
        if self.path == "/transient.bin":
            self.send_error(503, "synthetic transient failure")
            return
        super().do_GET()


class Lifecycle(unittest.TestCase):
    def git(self, *args, cwd=None):
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, env=env).strip()

    def test_real_cli_acquire_execute_handoff_then_noop(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            web = root / "web"
            web.mkdir()
            payload = b"synthetic-payload"
            (web / "source.bin").write_bytes(payload)
            handler = lambda *a, **k: QuietHandler(*a, directory=web, **k)
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                bare = root / "origin.git"
                subprocess.run(["git", "init", "--bare", str(bare)], check=True, stdout=subprocess.DEVNULL)
                seed = root / "seed"
                self.git("clone", str(bare), str(seed))
                (seed / "scripts").mkdir()
                shutil.copy2(PROJECT / "scripts/etty_bounded_job.py", seed / "scripts/etty_bounded_job.py")
                shutil.copy2(PROJECT / "scripts/etty_job_agent.py", seed / "scripts/etty_job_agent.py")
                (seed / "scripts/__init__.py").write_text("")
                self.git("add", "scripts", cwd=seed)
                self.git("-c", "user.name=test", "-c", "user.email=test@example", "commit", "-m", "agent", cwd=seed)
                self.git("branch", "-M", "main", cwd=seed)
                self.git("push", "origin", "main", cwd=seed)
                self.git("checkout", "-b", "etty-handoff", cwd=seed)
                self.git("push", "origin", "etty-handoff", cwd=seed)
                self.git("checkout", "main", cwd=seed)

                destination_root = root / "data"
                destination_root.mkdir()
                counter = root / "counter.txt"
                python_version = subprocess.check_output([sys.executable, "--version"], text=True, stderr=subprocess.STDOUT).strip()
                command = [sys.executable, "-c", f"from pathlib import Path; p=Path({str(counter)!r}); p.write_text(str(int(p.read_text())+1) if p.exists() else '1')"]
                job = {
                    "authorized": True, "acquire": True,
                    "allowed_hosts": ["127.0.0.1"], "allowed_destination_roots": [str(destination_root)],
                    "transfer_cap_bytes": len(payload), "allowed_executables": [sys.executable],
                    "executable_path": sys.executable, "version_command": [sys.executable, "--version"],
                    "version_expected": python_version, "allowed_working_roots": [str(root)],
                    "allowed_environment_keys": [], "wall_seconds": 5,
                    "items": [{"id": "synthetic", "url": f"http://127.0.0.1:{server.server_port}/source.bin",
                               "destination": str(destination_root / "source.bin"), "expected_bytes": len(payload),
                               "sha256": hashlib.sha256(payload).hexdigest(), "command": command, "cwd": str(root)}],
                }
                (seed / "job.json").write_text(json.dumps(job))
                failure_job=json.loads(json.dumps(job)); failure_job["items"][0].update({"id":"transient","url":f"http://127.0.0.1:{server.server_port}/transient.bin","destination":str(destination_root/"transient.bin"),"expected_bytes":1,"command":[sys.executable,"-c","raise SystemExit('must not execute')"]})
                (seed / "failure_job.json").write_text(json.dumps(failure_job))
                self.git("add", "job.json", "failure_job.json", cwd=seed)
                self.git("-c", "user.name=test", "-c", "user.email=test@example", "commit", "-m", "job", cwd=seed)
                execution_commit = self.git("rev-parse", "HEAD", cwd=seed)
                envelope = {
                    "schema_version": 1, "job_id": "synthetic-job", "authorized": True,
                    "authorization_record": "synthetic-test", "execution_commit": execution_commit,
                    "job_definition_path": "job.json", "job_definition_sha256": hashlib.sha256((seed / "job.json").read_bytes()).hexdigest(),
                    "transfer_cap_bytes": len(payload), "allowed_source_hosts": ["127.0.0.1"],
                    "allowed_destination_roots": [str(destination_root)],
                    "resource_caps": {"allowed_executables": [sys.executable], "executable_path": sys.executable,
                                      "version_command": [sys.executable, "--version"], "version_expected": python_version,
                                      "allowed_working_roots": [str(root)], "allowed_environment_keys": [], "wall_seconds": 5},
                    "handoff_allowlist": ["result.json"],
                }
                failure_envelope={**envelope,"job_id":"failure-job","job_definition_path":"failure_job.json","job_definition_sha256":hashlib.sha256((seed/"failure_job.json").read_bytes()).hexdigest()}
                queue_dir = seed / "automation/etty_jobs"
                queue_dir.mkdir(parents=True)
                (queue_dir / "synthetic.json").write_text(json.dumps(envelope))
                (queue_dir / "failure.json").write_text(json.dumps(failure_envelope))
                (queue_dir / "malformed.json").write_text("not json\n")
                (queue_dir / "README.md").write_text("must be ignored\n")
                self.git("add", "automation", cwd=seed)
                self.git("-c", "user.name=test", "-c", "user.email=test@example", "commit", "-m", "queue", cwd=seed)
                self.git("push", "origin", "main", cwd=seed)

                runtime, queue_repo, job_repo, handoff_repo = (root / name for name in ("runtime", "queue", "job", "handoff"))
                for checkout in (runtime, queue_repo, job_repo, handoff_repo):
                    self.git("clone", str(bare), str(checkout))
                self.git("checkout", "--detach", self.git("rev-parse", "origin/main", cwd=runtime), cwd=runtime)
                self.git("checkout", "-B", "etty-handoff", "origin/etty-handoff", cwd=handoff_repo)
                state = root / "state/jobs.json"
                cli = [sys.executable, "-m", "scripts.etty_job_agent", "--queue-repo", str(queue_repo),
                       "--job-repo", str(job_repo), "--handoff-repo", str(handoff_repo), "--state", str(state), "--once"]
                test_env = {**os.environ, "ETTY_SYNTHETIC_HTTP": "1", "ETTY_SYNTHETIC_HANDOFF": "1",
                            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
                first = subprocess.run(cli, cwd=runtime, env=test_env, text=True, capture_output=True, check=True)
                self.assertIn("DONE", first.stdout)
                self.assertIn("malformed.json SAFE_STOP",first.stdout)
                self.assertNotIn("README.md",first.stdout)
                self.assertEqual(counter.read_text(), "1")
                self.assertEqual(self.git("rev-parse", "HEAD", cwd=job_repo), execution_commit)
                self.assertEqual(json.loads(state.read_text())["synthetic-job"]["status"], "done")
                remote_result = self.git("show", "origin/etty-handoff:handoffs/synthetic-job/result.json", cwd=handoff_repo)
                self.assertEqual(json.loads(remote_result)["status"], "done")
                failure_result=json.loads(self.git("show","origin/etty-handoff:handoffs/failure-job/result.json",cwd=handoff_repo))
                self.assertEqual(failure_result["status"],"SAFE_STOP")
                self.assertEqual(failure_result["phase"],"acquisition")
                self.assertEqual(failure_result["failed_item_ids"],["transient"])
                self.assertLessEqual(len(failure_result["error"]),500)
                handoff_head = self.git("rev-parse", "origin/etty-handoff", cwd=handoff_repo)
                network_bytes = json.loads((state.parent / "synthetic-job.acquisition.json").read_text())["network_bytes"]
                self.assertEqual(network_bytes, len(payload))

                second = subprocess.run(cli, cwd=runtime, env=test_env, text=True, capture_output=True, check=True)
                self.assertIn("ALREADY_COMPLETED", second.stdout)
                self.assertEqual(counter.read_text(), "1")
                self.git("fetch", "origin", "etty-handoff", cwd=handoff_repo)
                self.assertEqual(self.git("rev-parse", "origin/etty-handoff", cwd=handoff_repo), handoff_head)
            finally:
                server.shutdown()
                thread.join()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
