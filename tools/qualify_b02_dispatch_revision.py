from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out=M/'B02_DISPATCH_CHECKER_QUALIFICATION';out.mkdir(exist_ok=False)
helper=Path(__file__).with_name('b02_dispatch_boundary_probe.py')
def run(workspace,name):
    p=subprocess.run([sys.executable,str(helper),str(workspace),str(out/name)],capture_output=True,text=True,encoding='utf8',timeout=30)
    assert p.returncode==0,p.stderr
    result=json.loads(p.stdout);(out/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf8');return result
fixture=out/'contract-reference';fixture.mkdir()
# Minimal transport test double, not a copy or patch of Promotion business code.
(fixture/'main.py').write_text("HANDLERS={}\ndef handle(folder, request):\n    return HANDLERS[request['milestone']](folder, request)\n",encoding='utf8')
positive=run(fixture,'positive');assert positive['status']=='PASS'
negative=run(R/'candidate','current-negative');assert negative['status']=='FAIL' and not negative['explicit_milestone_preserved'] and not negative['nonmedia_concurrency_preserved']
(fixture/'main.py').write_text("import threading\nHANDLERS={}\nlock=threading.Lock()\ndef handle(folder, request):\n    with lock:\n        return HANDLERS[request['milestone']](folder, request)\n",encoding='utf8')
mutation=run(fixture,'serialized-mutation');assert mutation['explicit_milestone_preserved'] and not mutation['nonmedia_concurrency_preserved']
previous=R/'consumer-revisions/block-concurrent-media-v12.py';old=previous.read_text(encoding='utf8');oldhash=hashlib.sha256(previous.read_bytes()).hexdigest()
head=old[:old.index('PREVIOUS_PATH=')]
probe_source=helper.read_text(encoding='utf8').split("if __name__=='__main__':")[0]
revision=R/'consumer-revisions/block-dispatch-boundary-v13.py'
wrapper='''\n_original_observe=observe
def observe(workspace,out):
    result=_original_observe(workspace,out)
    result['dispatch_boundary']=probe(workspace,Path(out)/'dispatch-boundary')
    if result['dispatch_boundary']['status']!='PASS':
        result.update(status='FAIL',error='Adapter boundary: '+json.dumps(result['dispatch_boundary']))
    (Path(out)/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return result
'''
revision.write_text(head+'\n'+probe_source+'\n'+wrapper+'\nPREVIOUS_PATH='+repr(str(previous))+'\nPREVIOUS_HASH='+repr(oldhash)+'\n'+old[old.index('def main():'):],encoding='utf8')
request=out/'wrong-object.json';request.write_text(json.dumps({'goal_id':'block-observation-B02-upload-port','workspace':str(R/'candidate'),'subjects':{'main.py':'0'*64}}),encoding='utf8')
p=subprocess.run([sys.executable,str(revision),'--request',str(request)],cwd=out,capture_output=True,text=True,encoding='utf8',timeout=30)
assert p.returncode!=0 and 'object/version mismatch' in p.stderr
receipt={'status':'PASS','checker_hash':hashlib.sha256(revision.read_bytes()).hexdigest(),'previous_checker_hash':oldhash,'revision_path':str(revision),
 'controls':[{'kind':'positive','name':'independent explicit dispatch contract reference and unrelated operations overlap','passed':True,'receipt':positive},
 {'kind':'negative','name':'current adapter reroutes M1 and serializes unrelated milestones','passed':True,'receipt':negative},
 {'kind':'mutation','name':'serialized reference mutation rejected independently','passed':True,'receipt':mutation},
 {'kind':'mutation','name':'object mismatch rejected before browser','passed':True},
 {'kind':'positive','name':'previous browser observer byte source preserved','passed':head in revision.read_text(encoding='utf8') and hashlib.sha256(previous.read_bytes()).hexdigest()==oldhash}],
 'scope':'B02 adapter must preserve original explicit dispatch and unrelated milestone concurrency; existing browser/concurrent preview observation retained; no full M12',
 'product_sources_modified':False,'source_sha256':hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()}
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':'PASS','qualification':str(out/'receipt.json')}))
