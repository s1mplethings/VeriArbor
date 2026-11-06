"""Read-only derived correlation; never another accounting authority."""
import datetime
import ast
import hashlib
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
R = Path(r'F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05')
S = R / 'state/iter132-promotion-studio/promotion-05'
L = Path(r'F:\CGKN-ITER-076\global-provider-budget.json')
sys.path.insert(0, r'F:\CGKN-LeanLoop-V1-20261101')
from cgkn.protocol.adaptive_context import resolve_response_refs
def read(p): return json.loads(p.read_text(encoding='utf8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def schema_variants(request):
    schema=request['schema']
    yield schema, None
    if request['schema_name']!='cgkn_next_milestone':return
    # Recover insertion order from the unchanged original constructor, never
    # from timestamps or a guessed match. A final exact HTTP SHA is mandatory.
    source=Path(r'F:\CGKN-LeanLoop-V1-20261101\cgkn\agent\composer.py')
    baseline=read(V/'governance/SOURCE_MANIFEST.json')['files']
    if digest(source)!=baseline['cgkn/agent/composer.py']:
        # Later owner-scope admission work changed this file. Recover historical
        # schema order from the exact retained original, never the changed file.
        receipts=Path(r'F:\CGKN-LeanLoop-V1-20261101\migration\veriarbor\AUTHORITY_SWITCH_RECEIPTS.jsonl')
        row=next(r for r in (json.loads(line) for line in receipts.read_text().splitlines())
                 if r['file']=='cgkn/agent/composer.py'
                 and r['before_sha256']==baseline['cgkn/agent/composer.py'])
        source=Path(row['rollback'])
    assert digest(source)==baseline['cgkn/agent/composer.py']
    function=next(n for n in ast.walk(ast.parse(source.read_text(encoding='utf8')))
                  if isinstance(n,ast.FunctionDef) and n.name=='_next_milestone')
    expression=next(n.value for n in function.body if isinstance(n,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=='schema' for t in n.targets))
    values={'available':schema['properties']['requirement_refs']['items']['enum'],
            'checkers':schema['properties']['checker']['enum']}
    def literal(node):
        if isinstance(node,ast.Constant):return node.value
        if isinstance(node,ast.List):return [literal(x) for x in node.elts]
        if isinstance(node,ast.Dict):return {literal(k):literal(v) for k,v in zip(node.keys,node.values)}
        if isinstance(node,ast.Name) and node.id in values:return values[node.id]
        raise ValueError('Unqualified schema constructor expression')
    restored=literal(expression)
    assert restored==schema, 'Source ordering recovery may not change the schema'
    yield restored, {'path':str(source),'sha256':digest(source),'symbol':'AgentComposer._next_milestone.schema'}

before = read(R / 'continuations/veriarbor-01/accounting-before.json')
ledger = read(L)
assert ledger['calls'][:len(before['calls'])] == before['calls']
calls = ledger['calls'][len(before['calls']):]
identities = {c['request_identity']: c for c in calls}
matches = {}
for p in (S / 'provider_calls').glob('*/request.json'):
    if p.stat().st_mtime < (R / 'continuations/veriarbor-01/accounting-before.json').stat().st_mtime:
        continue
    d = read(p); c = d['config']; q = d['request']
    for chat, schema, schema_source in [(chat,schema,ref)
            for schema,ref in schema_variants(q) for chat in (False,True)]:
        payload = {'model': c['model'], 'messages' if chat else 'input': [
            {'role': 'system', 'content': q['system']}, {'role': 'user', 'content': q['user']}],
            'temperature': c['temperature'], 'max_tokens' if chat else 'max_output_tokens': c['max_output_tokens']}
        if q['schema'] is not None:
            fmt = {'name': q['schema_name'], 'strict': True, 'schema': schema}
            if chat: payload['response_format'] = {'type':'json_schema','json_schema':fmt}
            else: payload['text'] = {'format':{'type':'json_schema', **fmt}}
        payload['cgkn_attempt_id'] = d['identity']
        if c.get('model_id'): payload['cgkn_model_id'] = c['model_id']
        if c.get('reasoning_effort', 'none') != 'none': payload['reasoning'] = {'effort':c['reasoning_effort']}
        payload['stream'] = True
        identity = 'sha256:' + hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        if identity not in identities: continue
        user = json.loads(q['user'])
        context, resolution = resolve_response_refs(user.get('context', {}), user)
        tags = {k:context[k] for k in ('kind','leaf_goal','strategy_semantics','hypothesis',
            'expected_delta','failed_acceptance_ids','evidence_refs','verified_dependency_refs',
            'task_anchor','current_milestone_requirements') if k in context}
        matches.setdefault(identity, []).append({'request_ref': str(p), 'request_sha256':digest(p),
            'local_request_id':d['identity'], 'execution_identity': d.get('execution_identity'),
            'role':c['role'], 'model_id':c.get('model_id'), 'schema_name':q['schema_name'],
            'call_kind':user.get('call_kind'), 'semantic_attempt_id':user.get('semantic_attempt_id'),
            'task_tags':tags, 'exact_alias_resolution':resolution,
            'context_evidence_ref':str(p), 'api_method':'chat_completions' if chat else 'responses',
            'correlation_method':'reconstructed_exact_http_payload_sha256',
            'schema_order_source':schema_source,
            'response_ref':str(p.parent/'response.json') if (p.parent/'response.json').exists() else None,
            'error_ref':str(p.parent/'error.json') if (p.parent/'error.json').exists() else None,
            'causal_frontier_delta':'NOT_MEASURED_PER_CALL; consult canonical goal checks',
            'independence':'Provider output is not independent acceptance'})
        break
# Recorded JSON sorts nested schema keys; an original schema's insertion order
# can therefore be unrecoverable for the exact HTTP digest. For terminal calls,
# cross-check the ledger's hash-pinned response, exact provider request ID,
# model, and response text instead. Do not guess an in-flight identity.
terminal = {c.get('provider_request_id'):c for c in calls
    if c.get('provider_request_id') and c['request_identity'] not in matches}
for response_path in (S/'provider_calls').glob('*/response.json'):
    if not terminal: break
    response=read(response_path)
    call=terminal.get(response.get('request_id'))
    if not call: continue
    p=response_path.parent/'request.json';d=read(p);c=d['config']
    authoritative=Path(call['authoritative_response_ref'])
    assert digest(authoritative)==call['authoritative_response_sha256']
    bound=read(authoritative);raw=bound['response']
    assert bound['request_identity']==call['request_identity']
    assert raw['id']==response['request_id']==call['provider_request_id']
    assert response['model']==call['model']==c['model_id']
    raw_text=raw.get('output_text')
    if raw_text is None: raw_text=raw['choices'][0]['message']['content']
    assert raw_text==response['text']
    user=json.loads(d['request']['user'])
    context,resolution=resolve_response_refs(user.get('context',{}),user)
    matches[call['request_identity']]=[{'request_ref':str(p),'request_sha256':digest(p),
        'local_request_id':d['identity'],'execution_identity':d.get('execution_identity'),
        'role':c['role'],'model_id':c['model_id'],'schema_name':d['request']['schema_name'],
        'call_kind':user.get('call_kind'),'semantic_attempt_id':user.get('semantic_attempt_id'),
        'context_evidence_ref':str(p),'response_ref':str(response_path),
        'correlation_method':'hash_pinned_authoritative_response_exact_id_model_text',
        'authoritative_response_ref':str(authoritative),'authoritative_response_sha256':digest(authoritative),
        'task_tags':{k:context[k] for k in ('kind','leaf_goal','strategy_semantics','hypothesis','expected_delta') if k in context},
        'exact_alias_resolution':resolution,'causal_frontier_delta':'NOT_MEASURED_PER_CALL; consult canonical goal checks',
        'independence':'Provider output is not independent acceptance'}]
    del terminal[response['request_id']]
rows = [{'ledger_call':c, 'correlations':matches.get(c['request_identity'],[])} for c in calls]
out = V / 'governance/call-correlations'
out.mkdir(exist_ok=True)
target = out / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
result = {'kind':'DerivedCallCorrelation','authority':str(L),'historical_prefix_unchanged':True,
    'ledger_snapshot_sha256':hashlib.sha256(json.dumps(ledger,sort_keys=True).encode()).hexdigest(),
    'original_call_count':len(before['calls']),'new_call_count':len(calls),
    'matched_call_count':sum(bool(r['correlations']) for r in rows),'calls':rows,
    'settled_cost':'UNKNOWN_NOT_INVOICED','accounting_authority_mutated':False}
with target.open('x',encoding='utf8') as stream: json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(target),'calls':len(calls),'matched':result['matched_call_count']}))
