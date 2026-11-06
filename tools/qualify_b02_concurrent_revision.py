"""Qualify bounded concurrent media-read coverage; no product source edits."""
from pathlib import Path
import json,hashlib,shutil,sys,subprocess
from b02_upload_port_observer import observe
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out=M/'B02_CONCURRENT_CHECKER_QUALIFICATION';out.mkdir(exist_ok=False)
previous=R/'consumer-revisions/block-upload-port-v11.py';previous_hash=hashlib.sha256(previous.read_bytes()).hexdigest()
fixture=out/'serialized-reference';fixture.mkdir()
for p in (R/'candidate').glob('*.py'):shutil.copy2(p,fixture/p.name)
shutil.copytree(R/'candidate/milestones',fixture/'milestones',ignore=shutil.ignore_patterns('__pycache__'))
p=fixture/'main.py';source=p.read_text(encoding='utf8')
assert source.count('class ThreadedHTTPServer(ThreadingHTTPServer):')==1
source=source.replace('from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer','from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, HTTPServer')
source=source.replace('class ThreadedHTTPServer(ThreadingHTTPServer):','class ThreadedHTTPServer(HTTPServer):')
p.write_text(source,encoding='utf8')
positive=observe(fixture,out/'positive');assert positive['status']=='PASS',positive
negative=observe(R/'candidate',out/'current-negative');assert negative['status']=='FAIL' and negative.get('concurrent_preview',{}).get('passed') is False,negative
api=fixture/'milestones/milestone_dbb8341c8910593063a8/api.py';raw=api.read_text(encoding='utf8');assert raw.count('"sha256": record["sha256"],')==1
api.write_text(raw.replace('"sha256": record["sha256"],','"sha256": "0" * 64,'),encoding='utf8')
mutation=observe(fixture,out/'wrong-hash');assert mutation['status']=='FAIL' and 'project and bytes binding' in mutation['error']
observer=Path(__file__).with_name('b02_upload_port_observer.py').read_text(encoding='utf8').split("if __name__=='__main__':")[0]
old=previous.read_text(encoding='utf8');tail=old[old.index('def main():'):]
revision=R/'consumer-revisions/block-concurrent-media-v12.py'
revision.write_text(observer+'\nPREVIOUS_PATH='+repr(str(previous))+'\nPREVIOUS_HASH='+repr(previous_hash)+'\n'+tail,encoding='utf8')
request={'goal_id':'block-observation-B02-upload-port','workspace':str(R/'candidate'),'subjects':{'main.py':'0'*64}}
request_path=out/'wrong-object.json';request_path.write_text(json.dumps(request),encoding='utf8')
run=subprocess.run([sys.executable,str(revision),'--request',str(request_path)],cwd=out,capture_output=True,text=True,encoding='utf8',timeout=30)
assert run.returncode!=0 and 'object/version mismatch' in run.stderr
receipt={'status':'PASS','checker_hash':hashlib.sha256(revision.read_bytes()).hexdigest(),'previous_checker_hash':previous_hash,'revision_path':str(revision),
 'controls':[{'kind':'positive','name':'same workflow under serialized reference HTTP transport; test fixture only','passed':True,'receipt':positive},
    {'kind':'negative','name':'current real concurrent preview fails on shared media.json.tmp; source bound','passed':True,'receipt':negative},
    {'kind':'mutation','name':'incorrect response hash rejected independently','passed':True,'receipt':mutation},
    {'kind':'mutation','name':'wrong object hash rejected before browser','passed':True},
    {'kind':'positive','name':'previous checker fallback bytes unchanged','passed':hashlib.sha256(previous.read_bytes()).hexdigest()==previous_hash}],
 'product_sources_modified':False,'scope':'Same B02 owned preview contract under concurrent browser reads; original complete M12 unchanged'}
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in receipt.items() if k!='controls'}))
