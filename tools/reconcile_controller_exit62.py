"""Reconcile a dead original controller; preserve unknown upstream usage."""
import sys, os, json, hashlib, datetime
from pathlib import Path
H=Path('F:/CGKN-LeanLoop-V1-20261101')
sys.path.insert(0,str(H));sys.path.insert(0,str(H/'migration/veriarbor'))
from resume_promotion import read, sha, put
from cgkn.state import FileRunStore
from cgkn.state.provenance import put_evidence, reference
from cgkn.state.task_feedback import digest
from cgkn.orchestration.capability_tree import CapabilityTree
from cgkn.runtime import DAGRunner
from cgkn.executors import ExecutorRegistry
from cgkn.execution import BlockExecutionResult, BlockStatus
from cgkn.providers import GatewayCompletionClient
from scripts import provider_api_budget as budget

R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
O=R/'continuations/veriarbor-62'; project='iter132-promotion-studio';run='promotion-05';node='sem-node-0143'
store=FileRunStore(R/'state'); S=store.run_dir(project,run)
key='53033c820a6f4afbb3b935fbf692d46b'
identity='sha256:14a373502cf372b3080d2b3e8c64eb6da69d86b39580b1fb16c60cfcc24d3b87'
request_path=S/'provider_calls'/key/'request.json'; request=read(request_path)
execution=dict(project_id=project,run_id=run,node_id=node,attempt_id='attempt-0008')
assert request['execution_identity']==execution
assert not request_path.with_name('response.json').exists()
client=GatewayCompletionClient('http://127.0.0.1:1','unused-read-only')
cached=client.recover_cached(request_identity=identity,schema=request['request'].get('schema'),cache_dir=H/'.cgkn/domestic-gateway/recovery-responses')
assert cached is None, 'Complete cache exists; inspect instead of reconciliation'
ledger=Path('F:/CGKN-ITER-076/global-provider-budget.json');before=read(ledger)
call=next(x for x in before['calls'] if x['request_identity']==identity)
assert call['status']=='REQUEST_STARTED' and not budget._process_alive(call['owner_pid'])
stage=S/'candidates'/node/'attempt-0008'
leaf=next(n for n in read(S/'capability_tree.json')['nodes'] if n['id']==node)['config']['leaf_contract']
assert leaf['target_scope']==['main.py']
protected={'main.py':'09283ff67ccec8f78268362d44e66264a598728b19bd040b8ef1c5fcbd08e2f7'}
assert all(sha(R/'candidate'/p)==sha(stage/p)==h for p,h in protected.items())
reads={p:sha(stage/p) for p in leaf['read_scope']}
assert all(sha(R/'candidate'/p)==h for p,h in reads.items())
assert not (S/'publication_intents'/node/'attempt-0008.json').exists()
calls=[p for p in (S/'provider_calls').glob('*/request.json') if read(p).get('execution_identity')==execution]
assert len(calls)==3
completed=[]
for p in calls:
 if p==request_path:continue
 response=read(p.with_name('response.json'));text=response.get('text','')
 action=json.loads(text)
 assert action['op'] in (0,1), 'Earlier action may have written; inspect'
 completed.append({'request':str(p),'response_sha256':sha(p.with_name('response.json')),'op':action['op']})
put(O/'interruption-ledger-before.json',before)
for k,v in before['limits'].items():
 if v is not None:os.environ['CGKN_PROVIDER_'+k.upper()]=str(v)
after=budget.reconcile_incomplete_calls(ledger,process_alive=lambda pid:True if pid!=call['owner_pid'] else budget._process_alive(pid))
assert next(x for x in after['calls'] if x['request_identity']==identity)['status']=='INTERRUPTED_UNKNOWN'
assert [x for x in before['calls'] if x['request_identity']!=identity]==[x for x in after['calls'] if x['request_identity']!=identity]
runner=DAGRunner(ExecutorRegistry(),store,reconciliation_executors=('verify.local-file-effects@1',))
runner.recover_interrupted(project,run,CapabilityTree.from_dict(read(S/'capability_tree.json')))
prior=store.load_result(project,run,node)
assert prior.attempt_id=='attempt-0008' and prior.error.details['outcome_unknown']
old={str(p.relative_to(S)):sha(p) for p in (S/'attempts').rglob('*.json')}
ledger_hash=sha(ledger)
proof={'kind':'LocalBoundedFileEffectInspection','disposition':'NOT_APPLIED',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_receipt_sha256':digest(prior.as_dict()),'target_scope':leaf['target_scope'],
 'stage_and_workspace_match_previous_source':protected,'read_dependencies_match_stage':reads,
 'completed_read_only_actions':completed,'publication_intent_absent':True,
 'complete_response_cache_absent':True,'original_request_ref':reference(store.root,request_path),
 'scope':'Local file effects only. Controller and gateway processes absent; exact cause unproven. Upstream usage/cost UNKNOWN retained; no original request replay.'}
ref=put_evidence(store,project,run,proof)
checker=BlockExecutionResult(project_id=project,run_id=run,node_id='verify-veriarbor-controller-exit62',attempt_id='attempt-0001',executor_ref='verify.local-file-effects@1',status=BlockStatus.SUCCEEDED,outputs={'effect_reconciliation':{'source_receipt_hash':digest(prior.as_dict()),'disposition':'NOT_APPLIED','evidence_refs':[ref]}})
store.save_result(checker);result=runner.reconcile_effects(project,run,node,checker)
assert sha(ledger)==ledger_hash and all(sha(S/p)==h for p,h in old.items())
put(O/'recovery-observation.json',{'proof':proof,'result':result.as_dict(),'upstream_outcome':'UNKNOWN_RETAINED','provider_calls':0,'host_business_patches':0,'old_attempts_unchanged':True,'other_ledger_rows_unchanged':True})
print('Recovered local effects NOT_APPLIED; upstream INTERRUPTED_UNKNOWN preserved; zero Provider dispatches.')
