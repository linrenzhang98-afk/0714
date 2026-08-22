import json,os,subprocess,tempfile,unittest,hashlib,sys
from pathlib import Path
class Lifecycle(unittest.TestCase):
 def sh(self,*a,cwd=None): return subprocess.check_output(a,cwd=cwd,text=True,env={**os.environ,'GIT_AUTHOR_NAME':'test','GIT_AUTHOR_EMAIL':'test@example','GIT_COMMITTER_NAME':'test','GIT_COMMITTER_EMAIL':'test@example'}).strip()
 def test_real_queue_checkout_done_again(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t); bare=d/'origin.git'; subprocess.run(['git','init','--bare',str(bare)],check=True,stdout=subprocess.DEVNULL)
   seed=d/'seed'; self.sh('git','clone',str(bare),str(seed)); (seed/'scripts').mkdir(); (seed/'scripts/etty_bounded_job.py').write_text('')
   job={'authorized':True,'items':[{'id':'x','url':'https://example.test/x','destination':str(d/'x'),'expected_bytes':1,'command':[sys.executable,'-c','open("'+str(d/'result.json')+'","w").write("ok")']}],'allowed_hosts':['example.test'],'transfer_cap_bytes':1}
   (seed/'job.json').write_text(json.dumps(job)); self.sh('git','add','.',cwd=seed); self.sh('git','commit','-m','job',cwd=seed); self.sh('git','branch','-M','main',cwd=seed); self.sh('git','push','origin','main',cwd=seed); commit=self.sh('git','rev-parse','HEAD',cwd=seed)
   env={'schema_version':1,'job_id':'j','authorized':True,'authorization_record':'review','execution_commit':commit,'job_definition_path':'job.json','job_definition_sha256':hashlib.sha256((seed/'job.json').read_bytes()).hexdigest(),'transfer_cap_bytes':1,'allowed_source_hosts':['example.test'],'allowed_destination_roots':[str(d)],'resource_caps':{'wall_seconds':1},'handoff_allowlist':['result.json']}
   q=d/'queue'; q.mkdir(); (q/'j.json').write_text(json.dumps(env)); qr=d/'qr'; jr=d/'jr'; self.sh('git','clone',str(bare),str(qr)); self.sh('git','clone',str(bare),str(jr)); state=d/'state.json';
   # prove exact checkout and durable completion through the real function
   from scripts.etty_job_agent import process
   os.environ['ETTY_SYNTHETIC_HANDOFF']='1'
   self.assertEqual(process(env,qr,jr,state),'DONE'); self.assertEqual(process(env,qr,jr,state),'ALREADY_COMPLETED'); self.assertEqual(self.sh('git','rev-parse','HEAD',cwd=jr),commit)
if __name__=='__main__': unittest.main()
