from pathlib import Path
import json,hashlib,subprocess,sys,importlib.util,time
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor';V=Path('D:/VeriArbor')
out=M/'metadata-refresh-qualification';out.mkdir(exist_ok=False)
old=M/'rollback/step-21/cgkn/agent/project_loop.py'
test=H/'tests/agent/test_metadata_refresh_without_verdict.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
child='''import importlib.util,sys,pytest
from cgkn.agent.project_loop import ProjectSession
spec=importlib.util.spec_from_file_location('cgkn.agent._metadata_before',sys.argv[1])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
ProjectSession._refresh_milestone_subjects=module.ProjectSession._refresh_milestone_subjects
ProjectSession._reconcile_completed_checks=module.ProjectSession._reconcile_completed_checks
raise SystemExit(pytest.main(['tests/agent/test_metadata_refresh_without_verdict.py','-q','-p','no:cacheprovider']))
'''
(out/'baseline_replay.py').write_text(child,encoding='utf-8')
with (out/'baseline-output.log').open('wb') as f:
 result=subprocess.run([sys.executable,str(out/'baseline_replay.py'),str(old)],cwd=H,stdout=f,stderr=subprocess.STDOUT)
output=(out/'baseline-output.log').read_text(encoding='utf-8',errors='replace')
assert result.returncode==1 and '3 failed, 1 passed' in output
from cgkn.agent.project_loop import ProjectSession
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
spec=importlib.util.spec_from_file_location('cgkn.agent._metadata_benchmark',old)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
state=R/'state/iter132-promotion-studio/promotion-05/goal_acceptance.json'
before=sha(state);data=json.loads(state.read_text(encoding='utf-8'))
loop=ProjectSession.__new__(ProjectSession)
loop.acceptance=GoalAcceptance(FileRunStore(R/'state'),'iter132-promotion-studio','promotion-05',data['requirements'],data['checker_bindings'])
loop.subject_snapshot=lambda paths:{p:data['subjects'].get(p) for p in paths}
def reject_write(*args,**kwargs):raise AssertionError('read-only benchmark must not write')
loop.acceptance.bind_subjects=reject_write
times={}
for name,fn in [('before',module.ProjectSession._refresh_milestone_subjects),('after',ProjectSession._refresh_milestone_subjects)]:
 start=time.monotonic();fn(loop,data['plans'][-1]);times[name]=time.monotonic()-start
assert before==sha(state)
receipt={'kind':'MetadataRefreshQualification','fixed_test_sha256':sha(test),'baseline_source_sha256':sha(old),
 'original_overbroad_test_refs':[str(p) for p in (M/'tool-revisions').glob('test_metadata_refresh_without_verdict-*.py')],
 'test_correction':'Only unused pre-read views are prohibited. Mandatory save/render and per-receipt authentication remain active.',
 'fixed_test_on_original_source':{'exit_code':result.returncode,'failed':3,'passed':1,'output_sha256':sha(out/'baseline-output.log')},
 'fixed_test_on_updated_source':str(V/'governance/checks/metadata-only-refresh-v3/receipt.json'),
 'no_op_subject_refresh_seconds':times,'benchmark_samples':1,'scope':'Read-only unchanged subject metadata operation; no end-to-end performance claim',
 'authority_unchanged':True,'provider_calls':0,'host_business_patches':0}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
