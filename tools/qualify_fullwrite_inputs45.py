"""Inspect real full-file repair context in isolation, without a Provider call."""
from pathlib import Path
import hashlib,json,shutil,sys
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor'
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
sys.path.insert(0,str(H))
from cgkn.execution import BlockExecutionRequest,TaskContext
from cgkn.executors.llm import LLMExecutor
from cgkn.providers import ModelRoleConfig,ProviderCompletion

out=M/'full-write-inputs45';out.mkdir(exist_ok=False)
root=out/'snapshot';root.mkdir()
node=next(x for x in json.loads((S/'capability_tree.json').read_text(encoding='utf8'))['nodes'] if x['id']=='sem-node-0143')
config=node['config'];leaf=config['leaf_contract']
assert config['repair_contract']['strategy_semantics']['full_file_write'] is True
paths=sorted(set(leaf['target_scope']+leaf['read_scope']))
expected={}
for name in paths:
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(R/'candidate'/name,target)
    expected[name]=hashlib.sha256(target.read_bytes()).hexdigest()
seen=[]
class DiagnosticClient:
    def complete(self,**kwargs):
        packed=json.loads(kwargs['user'])
        def expand(value):
            if isinstance(value,dict):
                if set(value)=={'$context_ref'}:return expand(packed['context_values'][value['$context_ref']])
                return {k:expand(v) for k,v in value.items()}
            if isinstance(value,list):return [expand(v) for v in value]
            return value
        decoded=expand(packed)
        observed={x['path']:hashlib.sha256(x['content'].encode('utf8')).hexdigest() for x in decoded['context']['observations'] if x.get('action')=='read_file'}
        assert observed==expected,(observed.keys(),expected.keys())
        assert all(row.get('observed_content_sha256')==expected[row['path']] for row in decoded['tables']['paths'])
        seen.append({'input_bytes':len(kwargs['user'].encode('utf8')),'inline_hashes':observed,'write_operations':decoded['tables']['allowed_write_operations']})
        return ProviderCompletion(json.dumps({'escalation':True,'expected_local_effect':'Read-only context qualification; do not write'}),'fixture','local-only',{})
request=BlockExecutionRequest(project_id='diagnostic',run_id='inputs45',node_id='source',attempt_id='1',component_ref=node['capability_ref'],executor_ref='llm.cheap@1',task_context=TaskContext(leaf['leaf_goal'],config))
result=LLMExecutor(root,DiagnosticClient(),ModelRoleConfig('worker','qwen'),semantic_protocol=True,protocol_trace=lambda row:None).execute(request)
assert len(seen)==1
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value==hashlib.sha256((R/'candidate'/name).read_bytes()).hexdigest() for name,value in expected.items())
report={'kind':'FullWriteActualContextQualification','status':'PASS','provider_calls':0,'candidate_modified':False,'observed':seen[0],'executor_status':result.status.value,'scope':'Current target plus all 12 declared verified dependencies are losslessly inline before the first model response. No generated implementation or product acceptance.'}
with (out/'receipt.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({'status':'PASS','inline_files':len(expected),'input_bytes':seen[0]['input_bytes'],'provider_calls':0}))
