from pathlib import Path
import json,hashlib,sys
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor'
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
from cgkn.adapters.veriarbor.guidance_adapter import project_continuation
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=read(R/'profile.json');store=FileRunStore(R/'state');S=store.run_dir(p['project_id'],p['run_id']);d=read(S/'goal_acceptance.json')
assert not any(n['status']=='RUNNING' for n in read(S/'run_state.json')['nodes'].values())
view=GoalAcceptance(store,p['project_id'],p['run_id'],d['requirements'],d['checker_bindings']).view()
gid='accept-e1b521a1e0a607c6f7f6';goal=next(g for g in view['goals'] if g['id']==gid)
binding={'artifact_hashes':{name:sha(R/'candidate'/name) for name in ('promotion_publish.py','early_main.py')},
         'goal_receipts':{gid:(goal.get('evidence') or {}).get('receipt_hash')}}
assert binding['artifact_hashes']['promotion_publish.py']=='c3d9f8917f484c7001a5bffe8c8a72bf330a783c3edf8233689a5291373c3592'
assert binding['goal_receipts'][gid] is None
refs=[str(M/'media-publish-edges-attempt40/receipt.json'),str(M/'MEDIA_GUI_V5_ACTIVATION.json')]
f={'cost_policy':'Qwen Flash Agent, DeepSeek Flash Worker only; no Pro/Max. Reuse current trusted measurement keys and preserve UNKNOWN/cost history.',
'milestone_completion_request':'Complete the original M11/M12 and final delivery. Required M11 GUI functionality is actual M11 API dispatch, safe media serving, attachment/save/load preview with visible imported image/video controls and visible failure messages, continuing review/approval/local publish/receipt. Original91 is the authoritative GUI writer. Native M11 qualified-revision-3 now checks actual GUI media dispatch and preview after backend integrity/positive publication/idempotency. Use each current independent failure to identify its actual file owner; an HTTP failure at early_main.py M11 dispatch is not automatically a media API117 module-path failure. Once M11 passes, finish M12 GUI navigation, startup/config, full local workflow, scheduler, analytics, restart, invalidation, documentation, final packaging and all retained test-owner debts. Do not weaken assertions or declare library tests/product node success as final product PASS. Original acceptance/delivery/ledger/Corpus remain sole authorities.',
'fresh_runtime_diagnosis':{'applicability':binding,
    'next_step':'Current publication sourceC3 has the hashlib import and actual file integrity guard. Four local approval/publish negative tests PASS and native100M7PASS. CurrentM11 has no check on this completed source: reuse original122 once to observe qualified-revision-3. No source repair is justified until that current observation. This next-step instruction expires automatically when its artifact/evidence preconditions change.',
    'resolved':'Prior A0 NameError and prior media module-path diagnoses no longer apply. Do not add hashlib again. No valid current failure authorizes117/89 repair now.',
    'evidence_refs':refs},
'admission_correction':'Rely on current canonical goal evidence and current writer_target_ids, not stale scope integers or earlier leaf goals. Missing evidence -> reuse suitable existing measurement; current genuine FAILED -> repair actual matching writer; current VERIFIED -> reuse certificate. Respect VerificationKey dedup. Strategy problem plus two mechanism dimensions and bound falsifying_evidence array are required. Preserve existing dependency ordering, no117cycle for89. A GUIDANCE_NOT_APPLICABLE diagnosis is history, not an action request.',
'gui_writer_policy':'Only91 writes early_main.py. Preserve working86/117 and89 unless a new current counterexample actually targets them. Original87 fixture debt has independent proof in m6-fixture-qualification-7885a399/receipt.json; other test debts remain in veriarbor-33.json. Tests must match actual public APIs and real invalid fixtures without weakening assertions.',
'redecision':{'strategy_revision':hashlib.sha256(json.dumps(binding,sort_keys=True).encode()+b'explicit guidance applicability after either artifact or goal receipt delta').hexdigest(),'reason':'Fixed sourceC3 and native100PASS make prior import guidance stale. Operational next-step guidance now has explicit artifact and goal-receipt preconditions, automatically retired after either changes. This removes repeated FIRST/repair instructions from durable general completion requirements.','evidence_refs':refs}}
assert project_continuation(f,view)['fresh_runtime_diagnosis']['status']=='GUIDANCE_APPLICABLE'
with (M/'continuation-feedback/veriarbor-44.json').open('x',encoding='utf8') as out:json.dump({'expected_gui_sha256':sha(R/'candidate/early_main.py'),'feedback':f},out,indent=2)
print(json.dumps({'prepared':44,'bound_guidance':binding,'M11':goal['verdict']}))
