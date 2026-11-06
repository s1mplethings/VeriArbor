from pathlib import Path
import json,hashlib
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
def read(p):return json.loads(p.read_text(encoding='utf8'))
feedback=read(M/'continuation-feedback/veriarbor-101.json');f=feedback['feedback'];source=(R/'candidate/main.py').read_text(encoding='utf8');sha=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()
assert sha.startswith('f269c86e')
policy=f['bounded_patch_policy'];policy['files']['main.py']['max_anchor_chars']=400
policy['read_only_source_context']={'path':'main.py','sha256':sha,'normalization':'Universal newlines only. Blank-line count and indentation significant. This is original source, not replacement code.','fragment':source[source.index('def handle(data_dir, request):'):source.index('def _media_import_adapter(data_dir, request):')]}
policy['acceptance_requirements'].append('New enforced patch grammar constraint: EACH find anchor <=400 normalized characters. Use separate short unique anchors for distinct local changes; the prior long ~1500-character reconstructed anchor is forbidden. Source context below is exact read-only original text. No business replacement is supplied. Existing atomic batch supports up to8 patches. Preserve all existing behavior except current159 failures.')
f['fresh_runtime_diagnosis']['worker_context_diagnostic']=read(M/'B02_WORKER_CONTEXT_DIAGNOSTIC_38.json')
f['milestone_completion_request']+=' Attempt38 repeated the same nonmatching long anchor despite correct source in context. Do not repeat it. New generic qualified gate enforces find anchors<=400 characters, and exact local source is now directly in Worker patch policy. This is a materially new bounded patch strategy, not a reworded retry. No browser since source unchanged.'
f['redecision']={'strategy_revision':hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest(),'reason':'Qualified short-anchor gate55 and direct policy-scoped exact source evidence replace failed long-anchor strategy; native159 failure remains current','evidence_refs':[str(M/'B02_WORKER_CONTEXT_DIAGNOSTIC_38.json'),'D:/VeriArbor/governance/checks/short-anchor-gate55/receipt.json']}
for constraint in f['strategy_constraints']:
    constraint['required_dimensions'].append('max_anchor_chars');constraint['dimension_types']['max_anchor_chars']='integer'
with (M/'continuation-feedback/veriarbor-102.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
print('Prepared short-anchor strategy; unchanged current native failure remains bound.')
