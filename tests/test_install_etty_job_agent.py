import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT=Path(__file__).parents[1]


class InstallerSmoke(unittest.TestCase):
    def test_installer_creates_roles_and_import_safe_service(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); bare=root/"origin.git"; seed=root/"seed"; subprocess.run(["git","init","--bare",str(bare)],check=True,stdout=subprocess.DEVNULL)
            subprocess.run(["git","clone",str(bare),str(seed)],check=True,stdout=subprocess.DEVNULL)
            (seed/"scripts").mkdir();
            for name in ("install_etty_job_agent.sh","etty_job_agent.py","etty_bounded_job.py"):
                (seed/"scripts"/name).write_bytes((PROJECT/"scripts"/name).read_bytes())
            subprocess.run(["git","-C",str(seed),"add","scripts"],check=True)
            subprocess.run(["git","-C",str(seed),"-c","user.name=test","-c","user.email=test@example","commit","-m","install"],check=True,stdout=subprocess.DEVNULL)
            subprocess.run(["git","-C",str(seed),"branch","-M","main"],check=True); subprocess.run(["git","-C",str(seed),"push","origin","main"],check=True,stdout=subprocess.DEVNULL)
            env={**os.environ,"ETTY_AGENT_TEST_MODE":"1","ETTY_AGENT_ROOT":str(root/"control"),"ETTY_AGENT_BOOTSTRAP":str(seed),"ETTY_AGENT_REMOTE":str(bare),"HOME":str(root/"home")}
            subprocess.run(["bash",str(seed/"scripts/install_etty_job_agent.sh")],env=env,check=True)
            for name in ("agent_runtime","queue_repo","job_repo","handoff_repo"):
                self.assertTrue((root/"control"/name/".git").is_dir())
            service=(root/"home/.config/systemd/user/etty-job-agent.service").read_text()
            for token in ("python3 -m scripts.etty_job_agent","--queue-repo","--job-repo","--handoff-repo","--state","--once"):
                self.assertIn(token,service)
            self.assertIn("Persistent=true",(root/"home/.config/systemd/user/etty-job-agent.timer").read_text())
            self.assertEqual(subprocess.check_output(["git","-C",str(root/"control/agent_runtime"),"rev-parse","HEAD"],text=True).strip(),subprocess.check_output(["git","-C",str(seed),"rev-parse","HEAD"],text=True).strip())


if __name__ == "__main__": unittest.main()
