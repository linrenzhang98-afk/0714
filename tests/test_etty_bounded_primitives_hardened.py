import hashlib
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from scripts.etty_bounded_job import JobError, acquire, execute, validate_manifest


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass


class HardenedPrimitives(unittest.TestCase):
    def setUp(self):
        self._prior_http = os.environ.get("ETTY_SYNTHETIC_HTTP")
        os.environ["ETTY_SYNTHETIC_HTTP"] = "1"

    def tearDown(self):
        if self._prior_http is None:
            os.environ.pop("ETTY_SYNTHETIC_HTTP", None)
        else:
            os.environ["ETTY_SYNTHETIC_HTTP"] = self._prior_http

    def base(self, root, payload=b"abc"):
        return {"authorized": True, "allowed_hosts": ["127.0.0.1"], "allowed_destination_roots": [str(root)],
                "transfer_cap_bytes": len(payload), "allowed_executables": [sys.executable],
                "executable_path": sys.executable, "allowed_working_roots": [str(root)],
                "allowed_environment_keys": [], "wall_seconds": 2,
                "items": [{"id": "x", "url": "http://127.0.0.1/x", "destination": str(root / "x"),
                           "expected_bytes": len(payload), "command": [sys.executable, "-c", "pass"], "cwd": str(root)}]}

    def test_missing_authorization_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            job = self.base(Path(raw)); del job["authorized"]
            with self.assertRaises(JobError): validate_manifest(job)

    def test_destination_and_symlink_confinement(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); allowed = root / "allowed"; outside = root / "outside"; allowed.mkdir(); outside.mkdir()
            good = self.base(allowed); validate_manifest(good)
            bad = self.base(allowed); bad["items"][0]["destination"] = str(outside / "x")
            with self.assertRaises(JobError): validate_manifest(bad)
            link = allowed / "link"; link.symlink_to(outside, target_is_directory=True)
            escaped = self.base(allowed); escaped["items"][0]["destination"] = str(link / "x")
            with self.assertRaises(JobError): validate_manifest(escaped)

    def test_existing_reuse_and_conflict(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root); target=Path(job["items"][0]["destination"]); target.write_bytes(b"abc")
            job["items"][0]["sha256"]=hashlib.sha256(b"abc").hexdigest(); state=acquire(job,root/"state.json")
            self.assertEqual(state["items"]["x"]["status"],"reused")
            target.write_bytes(b"bad!")
            with self.assertRaises(JobError): acquire(job,root/"state2.json")

    def test_transfer_cap_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); state=root/"state.json"; state.write_text(json.dumps({"network_bytes":2,"items":{}})); job=self.base(root); job["transfer_cap_bytes"]=3
            os.environ["ETTY_SYNTHETIC_HTTP"]="1"
            with self.assertRaises(JobError): acquire(job,state)
            self.assertEqual(json.loads(state.read_text())["network_bytes"],2)

    def test_interrupted_retry_bytes_count_once_each(self):
        class Response:
            def __init__(self, chunks): self.chunks=iter(chunks)
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def geturl(self): return "http://127.0.0.1/file"
            def read(self, _size):
                value=next(self.chunks,b"")
                if isinstance(value,Exception): raise value
                return value
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root); job["transfer_cap_bytes"]=6
            responses=[Response([b"a",OSError("interrupted")]),Response([b"abc",b""])]
            with mock.patch("urllib.request.urlopen",side_effect=responses):
                state=acquire(job,root/"state.json")
            self.assertEqual(state["network_bytes"],4)
            self.assertEqual(state["items"]["x"]["attempts"],2)

    def test_redirect_host_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def geturl(self): return "http://unapproved.test/file"
            def read(self, _size): return b""
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root)
            with mock.patch("urllib.request.urlopen", return_value=Response()):
                with self.assertRaisesRegex(JobError,"redirect host"):
                    acquire(job,root/"state.json")

    def test_execution_bounds_and_idempotency(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); counter=root/"count"; job=self.base(root)
            job["items"][0]["command"]=[sys.executable,"-c",f"from pathlib import Path;p=Path({str(counter)!r});p.write_text(str(int(p.read_text())+1) if p.exists() else '1')"]
            state=root/"exec.json"; execute(job,state); execute(job,state); self.assertEqual(counter.read_text(),"1")
            drift=json.loads(json.dumps(job)); drift["items"][0]["command"]=[sys.executable,"-c","pass"]
            with self.assertRaises(JobError): execute(drift,state)

    def test_executable_version_cwd_env_timeout(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root)
            wrong=json.loads(json.dumps(job)); wrong["allowed_executables"]=["/bin/false"]
            with self.assertRaises(JobError): execute(wrong,root/"a.json")
            wrong=json.loads(json.dumps(job)); wrong["executable_path"]="/bin/false"
            with self.assertRaises(JobError): execute(wrong,root/"b.json")
            wrong=json.loads(json.dumps(job)); wrong["version_command"]=[sys.executable,"--version"]; wrong["version_expected"]="wrong"
            with self.assertRaises(JobError): execute(wrong,root/"c.json")
            wrong=json.loads(json.dumps(job)); wrong["items"][0]["cwd"]="/"
            with self.assertRaises(JobError): execute(wrong,root/"d.json")
            wrong=json.loads(json.dumps(job)); wrong["items"][0]["env"]={"SECRET":"x"}
            with self.assertRaises(JobError): execute(wrong,root/"e.json")
            slow=json.loads(json.dumps(job)); slow["wall_seconds"]=1; slow["items"][0]["command"]=[sys.executable,"-c","import time;time.sleep(2)"]
            with self.assertRaises(JobError): execute(slow,root/"f.json")

    def test_acquisition_and_execution_states_are_independent(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root); Path(job["items"][0]["destination"]).write_bytes(b"abc")
            acquire(job,root/"acquisition.json"); execute(job,root/"execution.json")
            self.assertIn("sha256",json.loads((root/"acquisition.json").read_text())["items"]["x"])
            self.assertIn("command_hash",json.loads((root/"execution.json").read_text())["items"]["x"])


if __name__ == "__main__": unittest.main()
