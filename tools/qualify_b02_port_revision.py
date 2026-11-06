from pathlib import Path
import hashlib,json,shutil,subprocess,sys
from b02_upload_port_observer import observe
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out=M/'B02_PORT_QUALIFICATION';out.mkdir(exist_ok=False)
previous=R/'consumer-revisions/final-gui-complete-v10.py'
oldhash=hashlib.sha256(previous.read_bytes()).hexdigest()
observer=Path(__file__).with_name('b02_upload_port_observer.py').read_text(encoding='utf8').split("if __name__=='__main__':")[0]
tail='''
def main():
    import runpy
    req=json.loads(Path(sys.argv[2]).read_text(encoding='utf8'))
    if req.get('goal_id')!='block-observation-B02-upload-port':
        fallback=Path(PREVIOUS_PATH)
        if hashlib.sha256(fallback.read_bytes()).hexdigest()!=PREVIOUS_HASH:raise ValueError('previous checker changed')
        runpy.run_path(str(fallback),run_name='__main__');return
    workspace=Path(req['workspace'])
    for name,expected in req['subjects'].items():
        target=(workspace/name).resolve()
        if not target.is_relative_to(workspace.resolve()) or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:raise ValueError('object/version mismatch')
    result=observe(workspace,Path.cwd()/'upload-port-evidence')
    print(json.dumps({'execution':'VALID','observed':{'value':result['status']=='PASS','reason':result.get('error','Browser upload port controls passed; not full B02/M12 completion')}}))
if __name__=='__main__':main()
'''
source=observer+'\nPREVIOUS_PATH='+repr(str(previous))+'\nPREVIOUS_HASH='+repr(oldhash)+'\n'+tail
revision=R/'consumer-revisions/block-upload-port-v11.py';revision.write_text(source,encoding='utf8')
positive=json.loads((M/'B02_PORT_POSITIVE_CONTROL/receipt.json').read_text(encoding='utf8'))
assert positive['status']=='PASS'
negative=observe(R/'candidate',out/'current-negative');assert negative['status']=='FAIL' and negative['upload']['status']==400
snapshot=out/'mutation-source';shutil.copytree(M/'m12-gui-contracts-041a367e/snapshot',snapshot,ignore=shutil.ignore_patterns('__pycache__'))
api=snapshot/'milestones/milestone_dbb8341c8910593063a8/api.py';text=api.read_text(encoding='utf8')
assert text.count('"sha256": record["sha256"],')==1
api.write_text(text.replace('"sha256": record["sha256"],','"sha256": "0" * 64,'),encoding='utf8')
mutation=observe(snapshot,out/'wrong-hash');assert mutation['status']=='FAIL' and 'project and bytes binding' in mutation['error']
# Run the actual frozen revision, including request object/version binding.
request={'goal_id':'block-observation-B02-upload-port','workspace':str(R/'candidate'),'subjects':{'main.py':hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()}}
request_path=out/'request.json';request_path.write_text(json.dumps(request),encoding='utf8')
valid=out/'valid-wrapper';valid.mkdir()
p=subprocess.run([sys.executable,str(revision),'--request',str(request_path)],cwd=valid,capture_output=True,text=True,encoding='utf8',timeout=60)
assert p.returncode==0,p.stderr
envelope=json.loads(p.stdout);assert envelope['execution']=='VALID' and envelope['observed']['value'] is False
request['subjects']['main.py']='0'*64;request_path.write_text(json.dumps(request),encoding='utf8')
p=subprocess.run([sys.executable,str(revision),'--request',str(request_path)],cwd=out,capture_output=True,text=True,encoding='utf8',timeout=30)
assert p.returncode!=0 and 'object/version mismatch' in p.stderr
controls=[{'kind':'positive','name':'historical working upload measured afresh; not current product evidence','passed':True,'receipt':positive},
 {'kind':'negative','name':'current browser400 is rejected','passed':True,'receipt':negative},
 {'kind':'mutation','name':'wrong uploaded hash rejected despiteHTTP200','passed':True,'receipt':mutation},
 {'kind':'positive','name':'native wrapper produces typed current failure','passed':True,'envelope':envelope},
 {'kind':'mutation','name':'wrong current object hash rejected before browser','passed':True},
 {'kind':'positive','name':'original M12 fallback source unchanged and hash locked','passed':hashlib.sha256(previous.read_bytes()).hexdigest()==oldhash}]
receipt={'status':'PASS','checker_hash':hashlib.sha256(revision.read_bytes()).hexdigest(),'previous_checker_hash':oldhash,'controls':controls,'scope':'Only additive B02 upload-port observation; full original M12 preserved','revision_path':str(revision)}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps({k:v for k,v in receipt.items() if k!='controls'}))
