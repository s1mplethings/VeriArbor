from pathlib import Path
import json, hashlib, sys
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor'
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.provenance import put_evidence
from cgkn.state.checker_revision import bind_checker_revision
def read(p):return json.loads(p.read_text(encoding='utf8'))
profile=read(R/'profile.json');store=FileRunStore(R/'state');pid=profile['project_id'];rid=profile['run_id']
assert not any(n['status']=='RUNNING' for n in read(store.run_dir(pid,rid)/'run_state.json')['nodes'].values())
controls=read(M/'MEDIA_CHECKER_V4_QUALIFICATION.json')
assert controls['status']=='PASS' and all(c['passed'] for c in controls['controls'])
raw=put_evidence(store,pid,rid,controls)
diagnostic=put_evidence(store,pid,rid,read(M/'media-checker-v4-current73/receipt.json'))
proof={'kind':'CheckerRevisionQualification','status':'QUALIFIED',
       'previous_checker_hash':controls['previous_checker_hash'],'checker_hash':controls['checker_hash'],
       'requirement_policy':'UNCHANGED','historical_evidence_policy':'RETAIN_ORIGINAL_VERDICTS',
       'requirement_scope':['M11'],
       'controls':[{'kind':c['kind'],'passed':c['passed'],'evidence_ref':raw,'name':c['name']} for c in controls['controls']],
       'current_candidate_counterexample_ref':diagnostic,
       'unchanged_functions_and_classes':controls['unchanged_functions_and_classes'],
       'reason':'Strengthen existing fresh media validation/idempotency requirement only; no previous assertion removed. Other requirements retain previous independent checker identity.'}
ref=put_evidence(store,pid,rid,proof)
decision={'checker_key':'independent','previous_checker_hash':controls['previous_checker_hash'],
          'source_path':str(R/'consumer-revisions/media-integrity-v4.py'),'source_sha256':controls['checker_hash'],
          'qualification_ref':ref,'reason':proof['reason']}
revision=bind_checker_revision(store,pid,rid,'independent',profile['independent_consumer'],decision)
with (M/'MEDIA_CHECKER_V4_ACTIVATION.json').open('x',encoding='utf8') as f:json.dump({'revision':revision,'decision':decision,'acceptance_granted':False,'scope':['M11']},f,indent=2)
print(json.dumps({'version':revision['checker_version'],'scope':['M11'],'acceptance_granted':False}))
