from pathlib import Path
import json,datetime
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
p=M/'M12_NOVELTY_GATE_RESULTS.json';doc=read(p);rows=[]
for path in sorted((M/'continuation-feedback').glob('veriarbor-*.json'),key=lambda p:int(p.stem.split('-')[-1])):
    number=int(path.stem.split('-')[-1])
    if number<86:continue
    feedback=read(path)['feedback'];run=R/'continuations'/path.stem
    if not (run/'started.json').exists():continue
    policy=feedback.get('bounded_patch_policy',{});decision=feedback.get('redecision',{})
    rows.append({'continuation':path.stem,'strategy_revision':decision.get('strategy_revision'),'reason':decision.get('reason'),'evidence_refs':decision.get('evidence_refs',[]),'block_id':policy.get('block_id'),'patch_only':policy.get('mode')=='patch_only','goal_observation':policy.get('hold_after_goal_check'),'source_bindings':{name:spec.get('source_sha256') for name,spec in policy.get('files',{}).items()},'max_anchor_chars':{name:spec.get('max_anchor_chars') for name,spec in policy.get('files',{}).items()},'authority':'Original supplied-feedback.json and Provider recording novelty admission; this row is derived only'})
doc['continuation_strategies']=rows;doc['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();doc['provider_call_counts_authority']='Original provider ledger and recorded request/response, not continuation count'
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf8')
failures=[]
for path in sorted((S/'attempts/sem-node-0143').glob('attempt-*.json')):
    a=read(path)
    if int(a['attempt_id'].split('-')[-1])<30:continue
    error=(a.get('error') or {}).get('message','')
    if error:failures.append({'attempt':a['attempt_id'],'error':error,'source_delta':bool(a.get('metadata',{}).get('bounded_patch_receipts'))})
print(json.dumps({'continuations_projected':len(rows),'bounded_writer_failures':failures}))
