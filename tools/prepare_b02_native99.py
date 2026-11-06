from pathlib import Path
import hashlib,json
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
def read(p):return json.loads(p.read_text(encoding='utf8'))
source=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest();assert source.startswith('f269c86e')
qualification=M/'B02_DISPATCH_CHECKER_QUALIFICATION/activation.json'
feedback=read(M/'continuation-feedback/veriarbor-96.json');f=feedback['feedback']
f['milestone_completion_request']='Run ONLY existing registered goal block-observation-B02-upload-port through original GoalAcceptance DAG on current f269c86e source using active qualified-revision-11. It covers B02 adapter explicit milestone dispatch and unrelated concurrency, plus prior upload/preview observation. Previous158 failure is stale after143a36. No Worker yet; no full M12; controller holds after new native receipt.'
f['fresh_runtime_diagnosis']={'current_block':'B02','source_sha256':source,'browser_failure':str(M/'b02-current-f269c86e/receipt.json'),'failure':'Explicit M1+media.import with browser data incorrectly reaches M11; actual isolated handler probes also prove global adapter lock serializes unrelated milestones. Existing path import now passes.','qualified_checker':read(qualification),'native_failure_required_before_repair':True}
f['redecision']={'strategy_revision':hashlib.sha256((source+str(qualification)).encode()).hexdigest(),'reason':'New source delta and concrete dispatch/concurrency failures with qualified checker11; obtain current exact native failure before business repair','evidence_refs':[str(qualification),str(M/'b02-current-f269c86e/receipt.json')]}
with (M/'continuation-feedback/veriarbor-99.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
print('Prepared native B02-only measurement on current source; no product edits.')
