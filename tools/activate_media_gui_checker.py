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
controls=read(M/'media-gui-v5-controls/receipt.json');assert controls['status']=='PASS'
raw=put_evidence(store,pid,rid,controls)
proof={'kind':'CheckerRevisionQualification','status':'QUALIFIED',
       'previous_checker_hash':controls['previous_checker_hash'],'checker_hash':controls['checker_hash'],
       'requirement_policy':'UNCHANGED','historical_evidence_policy':'RETAIN_ORIGINAL_VERDICTS',
       'requirement_scope':['M11'],
       'controls':[{'kind':c['kind'],'passed':c['passed'],'evidence_ref':raw,'name':c['name']} for c in controls['controls']],
       'reason':'Frozen M11 explicitly requires actual image/video GUI preview. Extend original real browser workflow with actual M11 HTTP dispatch, attached-content readback and visible preview bytes/controls. Preserve all prior API and browser assertions. Only M11 observer scope changes; final M12 attachment-control validation still required.'}
ref=put_evidence(store,pid,rid,proof)
decision={'checker_key':'independent','previous_checker_hash':controls['previous_checker_hash'],
          'source_path':str(R/'consumer-revisions/media-gui-v5.py'),'source_sha256':controls['checker_hash'],
          'qualification_ref':ref,'reason':proof['reason']}
revision=bind_checker_revision(store,pid,rid,'independent',p['independent_consumer'],decision)
d=read(S/'goal_acceptance.json');a=GoalAcceptance(store,pid,rid,d['requirements'],d['checker_bindings'])
executor=ExternalAcceptanceExecutor(R/'candidate',R,session_acceptance=a,consumer=p['independent_consumer'],qualified_revision=revision)
chain=[];current=executor
while current:
    chain.append({'version':current.checker_version,'scope':sorted(current._revision_scope) if current._revision_scope else None,'hash':current.consumer['sha256']})
    current=current._previous_executor
assert [r['version'] for r in chain]==['qualified-revision-3','qualified-revision-2','qualified-revision-1']
assert chain[-1]['hash']=='5201a3c5aa6c9e829890787e3a5d6b8f60d3de104b301fb9df5eeb28faeb1007'
with (M/'MEDIA_GUI_V5_ACTIVATION.json').open('x',encoding='utf8') as f:json.dump({'revision':revision,'decision':decision,'scope':['M11'],'actual_executor_fallback_chain':chain,'acceptance_granted':False,'provider_calls':0},f,indent=2)
print(json.dumps({'active':revision['checker_version'],'fallback_chain':chain,'acceptance_granted':False}))
