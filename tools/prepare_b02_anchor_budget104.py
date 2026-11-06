from pathlib import Path
import json,hashlib,re,sys
from cgkn.executors.llm import plan_bounded_patches
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
feedback=read(M/'continuation-feedback/veriarbor-103.json');f=feedback['feedback'];policy=f['bounded_patch_policy'];policy['files']['main.py']['max_anchor_chars']=400
raw=(R/'candidate/main.py').read_bytes();source=(R/'candidate/main.py').read_text(encoding='utf8');response=read(S/'provider_calls/d6cf035c3b5a4cee8f6d8980dd553c5f/response.json');patches=json.loads(response['text'])['payload']
anchors=[re.sub(r'\r\n|\r|\n','\n',p['find']) for p in patches]
_,receipts=plan_bounded_patches([{'action':'patch_file','path':'main.py',**p} for p in patches],R/'candidate',policy)
assert (R/'candidate/main.py').read_bytes()==raw
record={'kind':'AnchorBudgetQualification','attempt':'attempt-0040','status':'PASS_FOR_PURE_PREFLIGHT_ONLY','source_sha256':hashlib.sha256(raw).hexdigest(),'anchor_lengths':[len(a) for a in anchors],'anchor_match_counts':[source.count(a) for a in anchors],'old_limit':120,'new_limit':400,'scope_ranges_unchanged':True,'preflight_receipts':receipts,'applied':False,'browser_executed':False,'implementation_accepted':False,'reason':'Qwen exact current anchors are valid inside original function range; 120-character limit overconstrained a valid 389-character anchor. Restore bounded400 budget, not broader function authority. Rejected output not applied or supplied to Worker.'}
with (M/'B02_ANCHOR_BUDGET_QUALIFICATION_40.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
f['milestone_completion_request']='Repair current B02 dispatch and unrelated-concurrency defects bound to native159 on f269c86e. Qwen attempt40 matched current source correctly but caller120characteranchorcap rejected it. Pure preflight under400 proves original scope is adequate, so cap restored400; this does not authorize broader function edits. Independently submit a fresh bounded patch using actual source. All other current requirements remain: explicit milestone honored, M11 coordination retained, unrelated handlers concurrent, all frontend/core readonly. Oneattemptthenhold. No historical rejected implementation is supplied or applied.'
f['fresh_runtime_diagnosis']['latest_anchor_budget_qualification']=record
policy['acceptance_requirements']=[v.replace('<=120','<=400').replace('120 characters','400 characters') for v in policy['acceptance_requirements']]
f['redecision']={'strategy_revision':hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest(),'reason':'Qualified current exact anchor evidence corrects over-restrictive120 to400; original function/source/change budgets unchanged; QwenFlash fresh Worker','evidence_refs':[str(M/'B02_ANCHOR_BUDGET_QUALIFICATION_40.json'),str(S/'attempts/sem-node-0159/attempt-0001.json')]}
with (M/'continuation-feedback/veriarbor-104.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in record.items() if k!='preflight_receipts'}))
