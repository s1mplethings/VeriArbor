from pathlib import Path
import json,sys
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor'
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
from cgkn.state.provenance import put_evidence
from cgkn.state.checker_revision import bind_checker_revision
from cgkn.application.software_project.acceptance import ExternalAcceptanceExecutor
def read(p):return json.loads(p.read_text(encoding='utf8'))
p=read(R/'profile.json');store=FileRunStore(R/'state');pid=p['project_id'];rid=p['run_id'];S=store.run_dir(pid,rid)
assert not any(n['status']=='RUNNING' for n in read(S/'run_state.json')['nodes'].values())
controls=read(M/'M12_GUI_V9_QUALIFICATION.json');assert controls['status']=='PASS'
raw=put_evidence(store,pid,rid,controls)
proof={'kind':'CheckerRevisionQualification','status':'QUALIFIED',
 'previous_checker_hash':controls['previous_checker_hash'],'checker_hash':controls['checker_hash'],
 'requirement_policy':'UNCHANGED','historical_evidence_policy':'RETAIN_ORIGINAL_VERDICTS','requirement_scope':['M12'],
 'controls':[{'kind':c['kind'],'passed':c['passed'],'evidence_ref':raw,'name':c['name']} for c in controls['controls']],
 'reason':'Current GUI has one visible Platform URL in Content and one hidden in Schedule. Six actual browser controls qualify visible-field selection, retain rejection of all-hidden and multiple-visible ambiguity, and include actual candidate DOM. Preserve all v8 business assertions and old failures; only M12.'}
ref=put_evidence(store,pid,rid,proof)
decision={'checker_key':'independent','previous_checker_hash':controls['previous_checker_hash'],
 'source_path':str(R/'consumer-revisions/final-gui-complete-v9.py'),'source_sha256':controls['checker_hash'],
 'qualification_ref':ref,'reason':proof['reason']}
revision=bind_checker_revision(store,pid,rid,'independent',p['independent_consumer'],decision)
d=read(S/'goal_acceptance.json');a=GoalAcceptance(store,pid,rid,d['requirements'],d['checker_bindings'])
executor=ExternalAcceptanceExecutor(R/'candidate',R,session_acceptance=a,consumer=p['independent_consumer'],qualified_revision=revision)
chain=[];current=executor
while current:
 chain.append({'version':current.checker_version,'scope':sorted(current._revision_scope) if current._revision_scope else None,'hash':current.consumer['sha256']})
 current=current._previous_executor
assert [r['version'] for r in chain]==['qualified-revision-7','qualified-revision-6','qualified-revision-5','qualified-revision-4','qualified-revision-3','qualified-revision-2','qualified-revision-1']
with (M/'M12_GUI_V9_ACTIVATION.json').open('x',encoding='utf8') as out:json.dump({'revision':revision,'decision':decision,'scope':['M12'],'actual_executor_fallback_chain':chain,'acceptance_granted':False,'provider_calls':0},out,indent=2)
print(json.dumps({'active':revision['checker_version'],'fallback_chain':chain,'acceptance_granted':False}))
