"""Record the local M7 preview and the actual canonical packaging verdict.

Never converts failed packaging or additional tests into public delivery PASS.
The user requested a runnable M7 local checkpoint before M8–M12, whose final
delivery obligations remain active in the original ProjectSession.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

H=Path(r'F:\CGKN-LeanLoop-V1-20261101')
R=Path(r'F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
from scripts import real_test_execution, customer_runtime_runner, canonical_evidence_hash
from scripts.local_packager import package_project
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

out=R/'DOGFOOD_MVP';source=out/'application';profile=read(R/'profile.json')
run=R/'state'/profile['project_id']/profile['run_id'];d=read(run/'goal_acceptance.json')
view=GoalAcceptance(FileRunStore(R/'state'),profile['project_id'],profile['run_id'],d['requirements'],d['checker_bindings']).view()
assert view['obligations']['M7']['verdict']=='VERIFIED'
assert not any(n['status']=='RUNNING' for n in read(run/'run_state.json')['nodes'].values())
identities=read(out/'original-source-identities.json')
assert all(sha(source/rel)==value and sha(R/'candidate'/rel)==value for rel,value in identities.items())
assert (out/'packaging-attempt-01/packaging-test-result.json').exists()
attempt=out/'packaging-attempt-02';attempt.mkdir(exist_ok=False)
identity={'run_id':profile['run_id'],'candidate_id':profile['run_id']+'-M7-DOGFOOD',
    'candidate_hash':canonical_evidence_hash.candidate_source_hash(source),
    'commit_sha':real_test_execution.current_commit_sha(source)}
test=real_test_execution.run_tests(source,python_executable=sys.executable,timeout=180,**identity)
put(attempt/'test-result.json',test)
probe={'entrypoint':'early_main.py','args':['--help'],'stdout_contains':'--serve',
    'source_ref':str(source/'early_main.py'),'source_sha256':canonical_evidence_hash.sha256_file(source/'early_main.py')}
runtime=customer_runtime_runner.run(source,cli_probe=probe,**identity)
put(attempt/'runtime-result.json',runtime)
assert customer_runtime_runner.inspect(source)['status']=='PASS'
limits=['M7 local runtime preview only; M8–M12 and final product delivery remain pending.',
    'The original independent M7 suite passed on the canonical candidate and again on this frozen snapshot.',
    'Additional repository tests: '+str({k:test[k] for k in ('collected','passed','failed','skipped')})+'. Failed tests are retained and must be triaged/repaired before final delivery.',
    'Canonical packager status is reported verbatim; a runnable local preview is not public delivery approval.',
    'Early GUI evidence/claim setup uses the existing M2/M3 public API; full Signals navigation remains an M12 obligation.',
    'No real external account publication was performed; the qualified tests use local HTTP platforms.']
(source/'DELIVERY_NOTES.md').write_text('\n'.join(limits),encoding='utf8')
(out/'KNOWN_LIMITS.md').write_text('\n'.join('- '+x for x in limits)+'\n',encoding='utf8')
manifest=package_project(source,output_dir=R/'dogfood-packages',startup_command='powershell -NoProfile -File start.ps1',
    run_log_path=out/'checker-output.log',screenshot_path=out/'gui-early.png',known_limits=limits)
put(attempt/'canonical-packager-result.json',manifest)
health=[]
for path in ('/health','/'):
    with urllib.request.urlopen('http://127.0.0.1:8767'+path,timeout=5) as response:
        body=response.read();assert response.status==200 and body
        health.append({'path':path,'status':response.status,'bytes':len(body)})
receipt={'kind':'M7LocalDogfoodCheckpoint','M7':'VERIFIED',
    'status':'RUNNABLE_LOCAL_PREVIEW_WITH_LIMITS','local_dogfood_available':True,
    'local_url':'http://127.0.0.1:8767','startup_script':str(out/'start.ps1'),
    'source_identities_ref':str(out/'original-source-identities.json'),
    'independent_checker_output':str(out/'checker-output.log'),
    'canonical_packager_status':manifest['status'],'canonical_packager_result':str(attempt/'canonical-packager-result.json'),
    'packaging_complete':manifest['status'] in ('PASS','PASS_WITH_LIMITS'),
    'additional_test_status':test['status'],'additional_test_counts':{k:test[k] for k in ('collected','passed','failed','skipped')},
    'public_delivery_allowed':False,'final_product_complete':False,'health':health,
    'known_limits':limits,'host_business_patches':0}
put(out/'receipt.json',receipt)
print(json.dumps({k:receipt[k] for k in ('status','M7','canonical_packager_status','packaging_complete','additional_test_counts','local_url')}))
