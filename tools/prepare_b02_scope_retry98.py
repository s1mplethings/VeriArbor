from pathlib import Path
import json,hashlib
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
source=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()
a=read(S/'attempts/sem-node-0143/attempt-0035.json')
assert source=='61bebcfedac3c0624cdb0bb1a65e208eeb05a95eb664488042b5b84ecb11bdd4'
assert a['status']=='FAILED' and 'PATCH_SCOPE_EXCEEDED' in a['error']['message']
record={'attempt':'attempt-0035','node':'sem-node-0143','verdict':'PATCH_SCOPE_EXCEEDED','source_sha256':source,'applied':False,'source_unchanged':True,'browser_executed':False,'new_failure_evidence':str(S/'attempts/sem-node-0143/attempt-0035.json'),'reason':'Third patch targeted _serve_media outside authorized adapter region; entire batch rejected atomically. Existing _serve_media already calls handle; its implementation remains read-only.'}
out=M/'B02_SCOPE_REJECTION_35.json'
with out.open('x',encoding='utf8') as f:json.dump(record,f,indent=2)
feedback=read(M/'continuation-feedback/veriarbor-97.json')
f=feedback['feedback']
f['fresh_runtime_diagnosis']['new_scope_failure']=record
f['milestone_completion_request']+=' Attempt35 was atomically rejected for a third patch outside scope, not a product execution failure. New evidence is B02_SCOPE_REJECTION_35.json. Author a fresh bounded patch strictly inside the unchanged allowed handle/adapter region. Existing _serve_media calls handle, and must remain byte-identical. No additional serving or GUI edits are authorized.'
f['bounded_patch_policy']['acceptance_requirements'].append('Attempt35 proved the out-of-region _serve_media edit invalid. All patch anchors, including context, must fall within [2212,6351) normalized source characters. No _serve_media edits. Do not resend the rejected batch. Preserve exact source binding; one current attempt only.')
f['redecision']['strategy_revision']=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
f['redecision']['reason']='New concrete scope rejection: remove serving-layer writes from repair scope; preserve original serve-media delegation through handle. Same native current failure remains bound; source unchanged.'
f['redecision']['evidence_refs'].append(str(out))
with (M/'continuation-feedback/veriarbor-98.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
p=M/'M12_PATCH_SCOPE_RESULTS.json';data=read(p);data['attempts'].append(record);data['business_attempt']='B02_ATTEMPT35_REJECTED_NO_MEASUREMENT';p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
p=M/'M12_NOVELTY_GATE_RESULTS.json';data=read(p);data.setdefault('history',[]).append({'continuation':98,'new_failure_evidence':str(out),'source_unchanged':True,'native_failure_receipt':'86c12b1d71d9d43dc63d909532b9e900c6b4812d8a229cc16e31016aa79a0dde','scope_unchanged':True,'strategy_revision':f['redecision']['strategy_revision']});p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record))
