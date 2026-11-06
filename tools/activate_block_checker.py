"""Activate a qualified scoped checker using the existing revision authority."""
from pathlib import Path
import json,sys
from cgkn.state import FileRunStore
from cgkn.state.provenance import put_evidence
from cgkn.state.checker_revision import bind_checker_revision
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
def read(p):return json.loads(p.read_text(encoding='utf8'))
controls_path=Path(sys.argv[1]);controls=read(controls_path);assert controls['status']=='PASS'
profile=read(R/'profile.json');store=FileRunStore(R/'state');pid=profile['project_id'];rid=profile['run_id'];root=store.run_dir(pid,rid)
with store.exclusive_file(root/'project_session.lock'):
    assert not any(r['status']=='RUNNING' for r in read(root/'run_state.json')['nodes'].values())
    raw=put_evidence(store,pid,rid,controls)
    proof={'kind':'CheckerRevisionQualification','status':'QUALIFIED','previous_checker_hash':controls['previous_checker_hash'],
        'checker_hash':controls['checker_hash'],'requirement_policy':'UNCHANGED','historical_evidence_policy':'RETAIN_ORIGINAL_VERDICTS',
        'requirement_scope':['M12'],'controls':[{'kind':c['kind'],'name':c['name'],'passed':c['passed'],'evidence_ref':raw} for c in controls['controls']],
        'reason':controls['scope']+'; independent positive, negative, mutation and object binding controls passed. No business implementation or full M12 verification granted.'}
    qualification=put_evidence(store,pid,rid,proof)
    decision={'checker_key':'independent','previous_checker_hash':controls['previous_checker_hash'],'source_path':controls['revision_path'],
        'source_sha256':controls['checker_hash'],'qualification_ref':qualification,'reason':proof['reason']}
    revision=bind_checker_revision(store,pid,rid,'independent',profile['independent_consumer'],decision)
    receipt={'revision':revision,'qualification':qualification,'source_qualification':str(controls_path),'business_writes':0,'acceptance_granted':False}
    (controls_path.parent/'activation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'active_checker':revision['checker_version'],'acceptance_granted':False}))
