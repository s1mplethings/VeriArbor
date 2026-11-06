from pathlib import Path
import json, hashlib, datetime
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
H=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
S=R/'state/iter132-promotion-studio/promotion-05'
O=R/'continuations/veriarbor-29'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f: json.dump(x,f,indent=2)
before=read(O/'accounting-before.json')
after=read(Path('F:/CGKN-ITER-076/global-provider-budget.json'))
assert after['calls'][:len(before['calls'])]==before['calls']
new=after['calls'][len(before['calls']):]
assert len(new)==1 and all(c['status']=='SUCCEEDED' for c in new)
state=read(S/'run_state.json')
assert not any(v['status'] in {'UNKNOWN','RUNNING','INTERRUPTED_UNKNOWN'} for v in state['nodes'].values())
identities=read(H/'m11-generated-tests-350e97b9/receipt.json')['source_identities']
assert all(sha(R/'candidate'/p)==v for p,v in identities.items())
response=read(S/'provider_calls/239fd113cede47e7a87529ed107f9621/response.json')
doc={'kind':'NativeProcessExitRecoveryObservation','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'original_exec_session':2543,'reported_exit_code':1,'windows_exception':'0xc0000005 in python312.dll',
 'native_stack_dump':'Partial log at first60second dump; exact causal attribution unproven. New faulthandler instrumentation removed before next continuation. Interpreter remains original frozen3.12.3.',
 'original_normal_finish_receipts':'ABSENT; not fabricated','ledger_prefix_unchanged':True,'calls':new,
 'provider_response':{'path':str(S/'provider_calls/239fd113cede47e7a87529ed107f9621/response.json'),'sha256':sha(S/'provider_calls/239fd113cede47e7a87529ed107f9621/response.json')},
 'candidate_identical_to_frozen_diagnostic':True,'running_or_unknown_nodes':[],
 'state_hashes':{p:sha(S/p) for p in ['run_state.json','capability_tree.json','execution_dag.json','agent_checkpoint.json','goal_acceptance.json']},
 'upstream_replay':False,'new_unknowns':0,'host_business_patches':0}
put(O/'recovery-observation.json',doc)
put(O/'accounting-recovery.json',{'kind':'PostExitAccountingObservation','prefix_unchanged':True,'calls':new,'estimated_cost_delta':after['totals']['estimated_cost']-before['totals']['estimated_cost'],'settled_vendor_cost':'UNKNOWN_NOT_INVOICED'})
feedback=read(H/'continuation-feedback/veriarbor-29.json')
feedback['feedback']['fresh_runtime_diagnosis']['native_exit29']=str(O/'recovery-observation.json')
put(H/'continuation-feedback/veriarbor-30.json',feedback)
print(json.dumps({'status':'LOCAL_STATE_RECONCILED','new_completed_calls':len(new),'candidate_unchanged':True,'new_unknowns':0}))
