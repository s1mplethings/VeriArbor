from pathlib import Path
import json,hashlib,re
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
feedback=read(M/'continuation-feedback/veriarbor-102.json');f=feedback['feedback'];policy=f['bounded_patch_policy'];policy['files']['main.py']['max_anchor_chars']=120
source=(R/'candidate/main.py').read_text(encoding='utf8');response=read(S/'provider_calls/e4024553620640d89c2fd531a373e734/response.json')
anchors=[re.sub(r'\r\n|\r|\n','\n',p['find']) for p in json.loads(response['text'])['payload']]
record={'attempt':'attempt-0039','model':'deepseek-flash','source_sha256':hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest(),'anchor_lengths':[len(a) for a in anchors],'anchor_match_counts':[source.count(a) for a in anchors],'applied':False,'browser_executed':False,'new_strategy':'Each anchor <=120 characters, disallowing the repeated comment-spanning bad anchor; Qwen Flash alternate Worker within original routing mechanism. No same-model semantic review claim.'}
with (M/'B02_ANCHOR_REJECTION_39.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
f['cost_policy']='Qwen3.8 Flash Agent and alternate Qwen3.8 Flash Worker only via existing reviewed route. Pro0/Max0. Same-family judgment is SELF_CRITIQUE only, not acceptance. Independent executable/browser39checks decide product truth.'
f['fresh_runtime_diagnosis']['latest_patch_rejection']=record
f['milestone_completion_request']+=' RepeatedDeepSeek anchoring failed even under400charbudget. New strategy: alternate Qwen Flash Worker and mandatory <=120-character unique anchors, no unchanged long comment context. The rejected first anchor was398characters and is now mechanically forbidden. All product scope and current159 failure binding remain unchanged.'
policy['acceptance_requirements']=[v.replace('<=400','<=120').replace('400 characters','120 characters') for v in policy['acceptance_requirements']]
f['redecision']={'strategy_revision':hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest(),'reason':record['new_strategy'],'evidence_refs':[str(M/'B02_ANCHOR_REJECTION_39.json'),'D:/VeriArbor/governance/checks/short-anchor-gate55/receipt.json']}
with (M/'continuation-feedback/veriarbor-103.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
print(json.dumps(record))
