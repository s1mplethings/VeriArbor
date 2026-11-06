from pathlib import Path
import ast,json,hashlib,datetime
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def milestone(p):
 tree=ast.parse(p.read_text(encoding='utf-8'))
 return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MILESTONE_ID' for t in n.targets))
approval=R/'candidate/milestones/milestone_33270fed0c9054f5ae04/api.py'
wrong=R/'candidate/milestones/milestone_9165a990eed5b9c8801e/api.py'
right=R/'candidate/milestones/milestone_dbb8341c8910593063a8/api.py'
assert sha(approval)=='db223502ff57164389978d41cde5d9f850c756a714f9c8b5fd9085ffea27d511'
tree=ast.parse(approval.read_text(encoding='utf-8'))
loader=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_load_media_module')
strings=[n.value for n in ast.walk(loader) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
assert wrong.parent.name in strings and right.parent.name not in strings
doc={'kind':'CurrentDependencyModuleIdentityDiagnosis','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source':{'path':str(approval),'sha256':sha(approval)},'loader_literals':strings,
 'loaded_module':{'path':str(wrong),'sha256':sha(wrong),'declared_milestone':milestone(wrong)},
 'actual_media_module':{'path':str(right),'sha256':sha(right),'declared_milestone':milestone(right)},
 'observed_current_failure':str(M/'m11-diagnostic-e4737c44-m6-db223502/receipt.json'),
 'finding':'Approval now passes all3validator arguments, but loader still selects a different milestone. Its handle rejects media.get and error is translated into media missing even for a valid M11 import. Actual M11 module remains present and unchanged; repair original approval owner, never relax media-validity tests.',
 'test_coverage':{'current_test_count':10,'original_test_count':12,'original_on_current_failed':0,'missing_current_case':'Original distinct STALE claim rejection. Current combined invalid-claims test only exercises UNSUPPORTED and CONFLICT.',
 'original_suite_receipt':str(M/'m6-original-tests-db223502/receipt.json')},
 'authority':'Read-only diagnosis; original GoalAcceptance and Provider-owned repair remain required','host_business_patches':0}
p=M/'M6_MEDIA_LOADER_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(doc,indent=2),encoding='utf-8')
print(json.dumps({'wrong_milestone':doc['loaded_module']['declared_milestone'],'correct_milestone':doc['actual_media_module']['declared_milestone'],'ref':str(p)}))
