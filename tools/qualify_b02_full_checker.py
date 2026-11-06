"""Qualify complete local B02 observer using actual positive/negative/mutation runs."""
from pathlib import Path
import json,hashlib,shutil,sys
from m12_b02_acceptance import run
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
positive_path=Path(sys.argv[1]);out=M/sys.argv[2];out.mkdir(exist_ok=False)
positive=json.loads(positive_path.read_text(encoding='utf8'))
checker=hashlib.sha256(Path(__file__).with_name('m12_b02_acceptance.py').read_bytes()).hexdigest()
assert positive['status']=='PASS' and len(positive['checks'])>=39 and positive['checker_sha256']==checker
assert all(hashlib.sha256((R/'candidate'/name).read_bytes()).hexdigest()==value for name,value in positive['subject_hashes'].items())
negative=run(M/'b02-partial-60d5e9d3/snapshot',out/'negative')
assert negative['status']=='FAIL' and negative['image_response']['status']==400
mutant=out/'mutation-source';shutil.copytree(positive_path.parent/'snapshot',mutant,ignore=shutil.ignore_patterns('__pycache__'))
api=mutant/'milestones/milestone_dbb8341c8910593063a8/api.py';source=api.read_text(encoding='utf8')
assert source.count('"sha256": record["sha256"],')==1
api.write_text(source.replace('"sha256": record["sha256"],','"sha256": "0" * 64,'),encoding='utf8')
mutation=run(mutant,out/'wrong-media-hash')
assert mutation['status']=='FAIL' and 'real identity/hash/project binding' in mutation['error']
receipt={'status':'PASS','checker_sha256':checker,'checker_dependencies':positive['checker_dependencies'],
    'controls':[{'kind':'positive','name':'current real PNG/MP4/browser/negative inputs/restart/adapter-edge flow','passed':True,
                 'evidence_path':str(positive_path),'evidence_sha256':hashlib.sha256(positive_path.read_bytes()).hexdigest(),'collected_checks':positive['checks']},
        {'kind':'negative','name':'previous source without adapter rejected with actualHTTP400','passed':True,'receipt':negative},
        {'kind':'mutation','name':'HTTP200 with incorrect media hash rejected','passed':True,'receipt':mutation},
        {'kind':'positive','name':'actual source and all backend dependencies exactly bound','passed':True,'subject_hashes':positive['subject_hashes']},
        {'kind':'positive','name':'success and injected downstream failure both clean real temporary path','passed':True,'edge_evidence':positive['adapter_edge']}],
    'historical_failures_retained':True,'product_mutations':0,'provider_calls':0,'complete_m12_executed':False}
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','qualification':str(out/'receipt.json'),'positive_checks':len(positive['checks'])}))
