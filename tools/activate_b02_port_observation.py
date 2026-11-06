"""Add a user-requested scoped observation to the original acceptance plan."""
from pathlib import Path
import copy,hashlib,json,sys,uuid
H=Path('F:/CGKN-LeanLoop-V1-20261101');sys.path.insert(0,str(H))
from cgkn.state import FileRunStore,EventRecord
from cgkn.state.acceptance import GoalAcceptance
from cgkn.state.provenance import put_evidence
from cgkn.state.checker_revision import bind_checker_revision
from cgkn.orchestration.capability_tree import CapabilityTree
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');M=H/'migration/veriarbor'
def read(p):return json.loads(p.read_text(encoding='utf8'))
p=read(R/'profile.json');store=FileRunStore(R/'state');pid=p['project_id'];rid=p['run_id'];S=store.run_dir(pid,rid)
with store.exclusive_file(S/'project_session.lock'):
    assert not any(n['status']=='RUNNING' for n in read(S/'run_state.json')['nodes'].values())
    controls=read(M/'B02_PORT_QUALIFICATION/receipt.json');assert controls['status']=='PASS'
    raw=put_evidence(store,pid,rid,controls)
    proof={'kind':'CheckerRevisionQualification','status':'QUALIFIED','previous_checker_hash':controls['previous_checker_hash'],'checker_hash':controls['checker_hash'],
        'requirement_policy':'UNCHANGED','historical_evidence_policy':'RETAIN_ORIGINAL_VERDICTS','requirement_scope':['M12'],
        'controls':[{'kind':c['kind'],'passed':c['passed'],'evidence_ref':raw,'name':c['name']} for c in controls['controls']],
        'reason':'Add user-requested B02 upload-port observation only. Actual working historical browser positive control, current negative control, wrong-hash mutation and exact object binding controls pass. Original complete M12 consumer unchanged and hash-locked fallback. Port PASS cannot certify full B02 or M12.'}
    ref=put_evidence(store,pid,rid,proof)
    decision={'checker_key':'independent','previous_checker_hash':controls['previous_checker_hash'],'source_path':controls['revision_path'],'source_sha256':controls['checker_hash'],'qualification_ref':ref,'reason':proof['reason']}
    revision=bind_checker_revision(store,pid,rid,'independent',p['independent_consumer'],decision)
    d=read(S/'goal_acceptance.json');a=GoalAcceptance(store,pid,rid,d['requirements'],d['checker_bindings']);plan=copy.deepcopy(d['plans'][-1])
    gid='block-observation-B02-upload-port';assert not any(g['id']==gid for g in plan['goals'])
    original=next(g for g in plan['goals'] if g['id']=='accept-c094cd66fb2ff494ecdf')
    goal={'id':gid,'phase_id':original['phase_id'],'requirement_refs':['M12'],'checker':'independent','task_refs':[],
        'subject_refs':['main.py','milestones/milestone_20f2614f6ae8403d4a4e/api.py','milestones/milestone_dbb8341c8910593063a8/api.py'],
        'acceptance':'B02 upload-port observation only: actual browser file input uploads a real PNG under the selected project; HTTP200 returns nonempty media identity, exact file SHA256 and correct project; GET preview returns exact owned bytes; malformed base64 rejected with HTTP400. This is a repair-admission observation, NOT the full B02 certificate. Full B02 requires video, preview, cleanup, negatives, isolation and restart; original complete M12 goal remains required unchanged.',
        'milestone_contract':{'block_id':'B02','scope':'BrowserFilePort -> ServerPathPort -> Existing M11; existing verified M11 contract retained','user_instruction':'M12-BLOCK-CLOSURE-AND-DELIVERY-V1 sections13,22,32','full_m12_goal':original['id']}}
    plan['goals'].append(goal);tree=CapabilityTree.from_dict(read(S/'capability_tree.json'));validated=a.propose(plan,tree);a.commit(validated)
    assert next(g for g in a.data['plans'][-1]['goals'] if g['id']==original['id'])==original
    store.append_event(EventRecord(str(uuid.uuid4()),pid,rid,'USER_BLOCK_OBSERVATION_ADDED',data={'goal_id':gid,'original_m12_unchanged':True,'qualification_ref':ref,'provider_calls':0,'business_writes':0}))
    report={'revision':revision,'goal':goal,'original_m12_unchanged':True,'full_b02_verified':False,'business_writes':0}
    (M/'B02_PORT_OBSERVATION_ACTIVATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'checker':revision['checker_version'],'added_goal':gid,'acceptance_granted':False}))
