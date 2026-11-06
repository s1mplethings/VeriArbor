"""Reconcile bounded file effects after a recorded provider stream reset."""
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
O=R/'continuations/veriarbor-71'; project='iter132-promotion-studio';run='promotion-05';node='sem-node-0143'
store=FileRunStore(R/'state'); S=store.run_dir(project,run)
key='1599a38cb9de4b30a4dabb295edbb84e'
identity='sha256:ceb3bea98fdc25c3bd44e75c40e64928e2242d95032ee812ed5ce6daa147b395'
request_path=S/'provider_calls'/key/'request.json'; request=read(request_path)
execution=dict(project_id=project,run_id=run,node_id=node,attempt_id='attempt-0015')
assert request['execution_identity']==execution
assert not request_path.with_name('response.json').exists()
client=GatewayCompletionClient('http://127.0.0.1:1','unused-read-only')
cached=client.recover_cached(request_identity=identity,schema=request['request'].get('schema'),cache_dir=H/'.cgkn/domestic-gateway/recovery-responses')
assert cached is None, 'Complete cache exists; inspect instead of reconciliation'
ledger=Path('F:/CGKN-ITER-076/global-provider-budget.json');before=read(ledger)
call=next(x for x in before['calls'] if x['request_identity']==identity)
assert call['status']=='INTERRUPTED_UNKNOWN'
stage=S/'candidates'/node/'attempt-0015'
leaf=next(n for n in read(S/'capability_tree.json')['nodes'] if n['id']==node)['config']['leaf_contract']
assert leaf['target_scope']==['main.py']
protected={'main.py':'8981690ec13e83042dc170ec62f202e67fb12b6ac4378a34a3cb1e0f36fe0afd'}
assert all(sha(R/'candidate'/p)==sha(stage/p)==h for p,h in protected.items())
reads={p:sha(stage/p) for p in leaf['read_scope']}
assert all(sha(R/'candidate'/p)==h for p,h in reads.items())
assert not (S/'publication_intents'/node/'attempt-0015.json').exists()
calls=[p for p in (S/'provider_calls').glob('*/request.json') if read(p).get('execution_identity')==execution]
assert len(calls)==2
completed=[]
for p in calls:
 if p==request_path:continue
 response=read(p.with_name('response.json'));text=response.get('text','')
 action=json.loads(text)
 assert action['op'] in (0,1), 'Earlier action may have written; inspect'
 completed.append({'request':str(p),'response_sha256':sha(p.with_name('response.json')),'op':action['op']})
assert read(request_path.with_name('error.json'))['outcome_unknown']
after=before
runner=DAGRunner(ExecutorRegistry(),store,reconciliation_executors=('verify.local-file-effects@1',))
prior=store.load_result(project,run,node)
assert prior.attempt_id=='attempt-0015' and prior.error.details['outcome_unknown']
old={str(p.relative_to(S)):sha(p) for p in (S/'attempts').rglob('*.json')}
ledger_hash=sha(ledger)
proof={'kind':'LocalBoundedFileEffectInspection','disposition':'NOT_APPLIED',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_receipt_sha256':digest(prior.as_dict()),'target_scope':leaf['target_scope'],
 'stage_and_workspace_match_previous_source':protected,'read_dependencies_match_stage':reads,
 'completed_read_only_actions':completed,'publication_intent_absent':True,
 'complete_response_cache_absent':True,'original_request_ref':reference(store.root,request_path),
 'scope':'Local file effects only. Gateway trace records ReadError/ConnectionResetError after partial streaming; complete cache absent. Upstream usage/cost UNKNOWN retained; no original request replay.'}
ref=put_evidence(store,project,run,proof)
checker=BlockExecutionResult(project_id=project,run_id=run,node_id='verify-veriarbor-stream-reset71',attempt_id='attempt-0001',executor_ref='verify.local-file-effects@1',status=BlockStatus.SUCCEEDED,outputs={'effect_reconciliation':{'source_receipt_hash':digest(prior.as_dict()),'disposition':'NOT_APPLIED','evidence_refs':[ref]}})
store.save_result(checker);result=runner.reconcile_effects(project,run,node,checker)
assert sha(ledger)==ledger_hash and all(sha(S/p)==h for p,h in old.items())
put(O/'recovery-observation.json',{'proof':proof,'result':result.as_dict(),'upstream_outcome':'UNKNOWN_RETAINED','provider_calls':0,'host_business_patches':0,'old_attempts_unchanged':True,'other_ledger_rows_unchanged':True})
print('Recovered local effects NOT_APPLIED; upstream INTERRUPTED_UNKNOWN preserved; zero Provider dispatches.')
