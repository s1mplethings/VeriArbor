"""Refresh derived M12 views from original receipts, retaining prior context."""
from pathlib import Path
import datetime,hashlib,json
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
source=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
state=read(S/'run_state.json');running=[key for key,n in state['nodes'].items() if n['status']=='RUNNING']
latest=max((R/'continuations').glob('veriarbor-*/started.json'),key=lambda p:p.stat().st_mtime)
check=read(S/'goal_acceptance.json')['checks'][-1]
p=M/'M12_CURRENT_FAILURE_CONTEXT.json';raw=p.read_bytes();archive=M/'context-history'/('M12_CURRENT_FAILURE_CONTEXT-'+hashlib.sha256(raw).hexdigest()[:12]+'.json')
if not archive.exists():archive.write_bytes(raw)
context=read(p);context.update(updated_at=now,bound_source_sha256=source,active_continuation=latest.parent.name,source_writer_may_be_in_flight='sem-node-0143' in running,previous_context_retained=str(archive))
context['latest_native_observation']={'node':check['node_id'],'receipt_hash':check['receipt_hash'],'checker':check['observation']['checker_version'],'verdict':check['verdict'],'source_current':check['subjects'].get('main.py')==source,'observed':check['observation']['observed']}
writer_path=max((S/'attempts/sem-node-0143').glob('attempt-*.json'),key=lambda p:p.stat().st_mtime)
writer=read(writer_path)
context['latest_execution_failure']={'attempt':writer['attempt_id'],'status':writer['status'],'error':writer.get('error'),'path':str(writer_path),'no_source_delta':not bool(writer.get('metadata',{}).get('bounded_patch_receipts'))}
context['next_action']='Continue current Block under exact supplied feedback; require actual source delta before browser and all local checks before certificate.'
if check['subjects'].get('main.py')==source and check['verdict']=='FAILED':
    context['formal_current_failure']={'path':f"attempts/{check['node_id']}/{check['attempt_id']}.json",'receipt_hash':check['receipt_hash']}
    context['actual_current_failure']=check['observation']['observed'];context['checker_identity']=check['observation']['checker_version']
else:context['formal_current_failure']=None
write(p,context)
p=M/'M12_BLOCK_STATUS.json';status=read(p);status.update(updated_at=now,active_continuation=latest.parent.name,current_source_sha256=source,running_nodes=running,latest_native_observation=context['latest_native_observation']);write(p,status)
p=M/'M12_PATCH_SCOPE_RESULTS.json';scope=read(p);known={x['attempt'] for x in scope['attempts']}
for path in sorted((S/'attempts/sem-node-0143').glob('attempt-*.json')):
    a=read(path)
    if int(a['attempt_id'].split('-')[-1])<30 or a['attempt_id'] in known:continue
    receipts=a.get('metadata',{}).get('bounded_patch_receipts',[])
    scope['attempts'].append({'node':a['node_id'],'attempt':a['attempt_id'],'status':a['status'],'error':a.get('error'),'applied':bool(receipts),'patch_receipts':receipts,'acceptance':'NOT_INFERRED_FROM_EXECUTION'})
scope['attempts'].sort(key=lambda x:x['attempt']);scope['updated_at']=now;write(p,scope)
print(json.dumps({'source':source,'continuation':latest.parent.name,'running_nodes':running,'native_verdict':check['verdict'],'native_source_current':check['subjects'].get('main.py')==source}))
