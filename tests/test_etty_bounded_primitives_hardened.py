import errno
import hashlib
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from scripts.etty_bounded_job import JobError, acquire, execute, validate_manifest


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass


class Response:
    def __init__(self, chunks, url="http://127.0.0.1/file"):
        self.chunks=iter(chunks); self.url=url
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def geturl(self): return self.url
    def read(self, _size):
        value=next(self.chunks,b"")
        if isinstance(value,BaseException): raise value
        return value


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
            with mock.patch("urllib.request.urlopen",return_value=Response([b"abc",b""])):
                with self.assertRaisesRegex(JobError,"transfer cap"):
                    acquire(job,state,sleep_fn=lambda _delay:None)
            self.assertEqual(json.loads(state.read_text())["network_bytes"],2)

    def test_interrupted_retry_bytes_count_once_each(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root); job["transfer_cap_bytes"]=6
            responses=[Response([b"a",ConnectionResetError("interrupted")]),Response([b"abc",b""])]
            with mock.patch("urllib.request.urlopen",side_effect=responses):
                state=acquire(job,root/"state.json",sleep_fn=lambda _delay:None)
            self.assertEqual(state["network_bytes"],4)
            self.assertEqual(state["items"]["x"]["attempts"],2)

    def test_redirect_host_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root)
            with mock.patch("urllib.request.urlopen", return_value=Response([],"http://unapproved.test/file")):
                with self.assertRaisesRegex(JobError,"redirect host"):
                    acquire(job,root/"state.json")

    def test_transient_item_isolated_then_later_pass_succeeds(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root,b"a"); job["transfer_cap_bytes"]=10
            job["items"]=[{**job["items"][0],"id":item_id,"url":f"http://127.0.0.1/{item_id}","destination":str(root/item_id)} for item_id in ("one","two","three")]
            calls=[]
            def open_url(request,timeout=30):
                item_id=request.full_url.rsplit('/',1)[-1]; calls.append(item_id)
                if item_id=="two" and calls.count("two")<=2: raise urllib.error.URLError("temporary")
                return Response([b"a",b""])
            with mock.patch("urllib.request.urlopen",side_effect=open_url):
                state=acquire(job,root/"state.json",retries_per_pass=2,retry_passes=1,backoff_seconds=(0,),sleep_fn=lambda _delay:None)
            self.assertLess(calls.index("three"),len(calls)-1)
            self.assertEqual(calls[-1],"two")
            self.assertTrue(all(state["items"][item_id]["status"]=="done" for item_id in ("one","two","three")))
            self.assertEqual(state["network_bytes"],3)

    def test_unresolved_transient_finishes_other_items_then_fails_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root,b"a"); job["transfer_cap_bytes"]=10
            job["items"]=[{**job["items"][0],"id":item_id,"url":f"http://127.0.0.1/{item_id}","destination":str(root/item_id)} for item_id in ("one","two","three")]
            def open_url(request,timeout=30):
                if request.full_url.endswith('/two'): raise urllib.error.URLError("temporary")
                return Response([b"a",b""])
            state_path=root/"state.json"
            with mock.patch("urllib.request.urlopen",side_effect=open_url):
                with self.assertRaisesRegex(JobError,"unresolved transient"):
                    acquire(job,state_path,retries_per_pass=2,retry_passes=1,backoff_seconds=(0,),sleep_fn=lambda _delay:None)
            state=json.loads(state_path.read_text())
            self.assertEqual(state["completed_items"],2)
            self.assertEqual(state["failed_item_ids"],["two"])
            self.assertEqual(state["items"]["two"]["status"],"transient_failed")

    def test_network_reset_is_transient_but_local_os_errors_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root)
            with mock.patch("urllib.request.urlopen",side_effect=ConnectionResetError("reset")) as opened:
                with self.assertRaisesRegex(JobError,"unresolved transient"):
                    acquire(job,root/"reset.json",retries_per_pass=1,retry_passes=1,backoff_seconds=(0,),sleep_fn=lambda _delay:None)
            self.assertEqual(opened.call_count,2)
            self.assertEqual(json.loads((root/"reset.json").read_text())["items"]["x"]["last_error_type"],"ConnectionResetError")
            for code in (errno.ENOSPC,errno.EACCES):
                state=root/f"local-{code}.json"
                with mock.patch("urllib.request.urlopen",side_effect=OSError(code,"local failure")) as opened:
                    with self.assertRaisesRegex(JobError,"non-transient acquisition error"):
                        acquire(job,state,retry_passes=2,sleep_fn=lambda _delay:None)
                self.assertEqual(opened.call_count,1)
                self.assertEqual(json.loads(state.read_text())["items"]["x"]["status"],"downloading")

    def test_restart_reuses_success_and_retries_transient_with_cumulative_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root,b"a"); job["transfer_cap_bytes"]=5
            job["items"]=[{**job["items"][0],"id":item_id,"url":f"http://127.0.0.1/{item_id}","destination":str(root/item_id)} for item_id in ("one","two")]
            state_path=root/"state.json"; calls=[]
            def first(request,timeout=30):
                item_id=request.full_url.rsplit('/',1)[-1]; calls.append(item_id)
                if item_id=="two": raise urllib.error.URLError("temporary")
                return Response([b"a",b""])
            with mock.patch("urllib.request.urlopen",side_effect=first):
                with self.assertRaises(JobError): acquire(job,state_path,retries_per_pass=1,retry_passes=0,sleep_fn=lambda _delay:None)
            self.assertEqual(json.loads(state_path.read_text())["network_bytes"],1)
            with mock.patch("urllib.request.urlopen",return_value=Response([b"a",b""])) as opened:
                state=acquire(job,state_path,retries_per_pass=1,retry_passes=1,backoff_seconds=(0,),sleep_fn=lambda _delay:None)
            self.assertEqual(opened.call_count,1)
            self.assertEqual(state["network_bytes"],2)
            self.assertIn(state["items"]["one"]["status"],{"done","reused"})

    def test_checksum_mismatch_is_immediate_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); job=self.base(root); job["items"][0]["sha256"]="0"*64
            with mock.patch("urllib.request.urlopen",return_value=Response([b"abc",b""])) as opened:
                with self.assertRaisesRegex(JobError,"checksum mismatch"):
                    acquire(job,root/"state.json",retry_passes=2,sleep_fn=lambda _delay:None)
            self.assertEqual(opened.call_count,1)

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
