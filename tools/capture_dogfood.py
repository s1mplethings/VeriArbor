"""Gate the requested local M7 checkpoint on original authenticated acceptance."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

H = Path(r'F:\CGKN-LeanLoop-V1-20261101')
R = Path(r'F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05')
sys.path.insert(0, str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
from scripts.local_packager import package_project
from scripts import real_test_execution, customer_runtime_runner, canonical_evidence_hash
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf8') as f: json.dump(v,f,ensure_ascii=False,indent=2)

profile = read(R/'profile.json')
run = R/'state'/profile['project_id']/profile['run_id']
state = read(run/'run_state.json')
assert not any(n['status']=='RUNNING' for n in state['nodes'].values())
d = read(run/'goal_acceptance.json')
view = GoalAcceptance(FileRunStore(R/'state'),profile['project_id'],profile['run_id'],d['requirements'],d['checker_bindings']).view()
assert view['obligations']['M7']['verdict']=='VERIFIED', 'M7 is not authentically VERIFIED'
out = R/'DOGFOOD_MVP'
out.mkdir(exist_ok=False)
put(out/'authenticated-acceptance.json',view)
source = out/'application'
shutil.copytree(R/'candidate',source,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
identities = {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
put(out/'original-source-identities.json',identities)
assert all(sha(R/'candidate'/rel)==value for rel,value in identities.items())
checker = R/'consumer-revisions/gui-locators-v3.py'
assert sha(checker)=='5201a3c5aa6c9e829890787e3a5d6b8f60d3de104b301fb9df5eeb28faeb1007'
put(out/'request.json',{'workspace':str(source),'requirements':{'M7':{}}})
argv=[sys.executable,'-X','utf8',str(checker),'--request',str(out/'request.json')]
result=subprocess.run(argv,cwd=out,env={**os.environ,'PYTHONUTF8':'1'},capture_output=True,text=True,encoding='utf8',timeout=240)
(out/'checker-output.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
assert result.returncode==0
observation=json.loads(result.stdout.strip().splitlines()[-1])
assert observation['execution']=='VALID' and observation['observed']['value'] is True
assert all(sha(source/rel)==value for rel,value in identities.items()), 'Checker altered application source'
assert all(sha(R/'candidate'/rel)==value for rel,value in identities.items()), 'Live source changed during snapshot check'
limits=['Local M7 DOGFOOD checkpoint only. M8–M12 and final product acceptance/delivery remain pending.',
        'Uses local test HTTP publication, not authorization to publish to an external real account.',
        'The early GUI has no Signals/evidence/claim authoring page; claim setup uses the existing M2/M3 public API. Full navigation is an M12 obligation.',
        'Startup uses the original local D:\\anaconda\\python.exe interpreter.']
(out/'README.md').write_text('# Promotion Studio — M7 DOGFOOD\n\nRun `start.ps1` in PowerShell. Open http://127.0.0.1:8767.\n\nProjects → Campaigns → Content → Review → Approve → Local Publish → Receipts.\n\n'+ '\n'.join('- '+x for x in limits)+'\n\nThe unchanged original M7 checker passed again on this frozen snapshot. Its output and GUI screenshot are included. This is not final product acceptance.\n',encoding='utf8')
(out/'start.ps1').write_text("$ErrorActionPreference='Stop'\n$env:PYTHONUTF8='1'\n& 'D:\\anaconda\\python.exe' (Join-Path $PSScriptRoot 'application\\early_main.py') --serve --port 8767 --data (Join-Path $PSScriptRoot 'local-data')\n",encoding='utf8')
(out/'TEST_REPORT.md').write_text('# M7 snapshot verification\n\ncommands_run:\n'+subprocess.list2cmdline(argv)+'\n\nresults:\n'+json.dumps(observation,ensure_ascii=False)+'\n',encoding='utf8')
(out/'DELIVERY_NOTES.md').write_text('\n'.join(limits),encoding='utf8')
# Use the existing packaging evidence producers. CLI help is only a startup
# smoke; full GUI behavior remains established by the unchanged checker above.
shutil.copy2(out/'README.md',source/'DOGFOOD_README.md')
if not (source/'README.md').exists(): shutil.copy2(out/'README.md',source/'README.md')
(source/'start.ps1').write_text("$ErrorActionPreference='Stop'\n$env:PYTHONUTF8='1'\n& 'D:\\anaconda\\python.exe' (Join-Path $PSScriptRoot 'early_main.py') --serve --port 8767 --data (Join-Path $PSScriptRoot 'local-data')\n",encoding='utf8')
(source/'screenshots').mkdir(exist_ok=True)
shutil.copy2(out/'gui-early.png',source/'screenshots/browser_visual_evidence.png')
shutil.copy2(out/'DELIVERY_NOTES.md',source/'DELIVERY_NOTES.md')
identity={'run_id':profile['run_id'],'candidate_id':profile['run_id']+'-M7-DOGFOOD',
    'candidate_hash':canonical_evidence_hash.candidate_source_hash(source),
    'commit_sha':real_test_execution.current_commit_sha(source)}
test=real_test_execution.run_tests(source,python_executable=sys.executable,timeout=180,**identity)
put(out/'packaging-test-result.json',test)
assert test['status']=='PASS', 'Original candidate tests failed on DOGFOOD snapshot'
probe={'entrypoint':'early_main.py','args':['--help'],'stdout_contains':'--serve',
    'source_ref':str(source/'early_main.py'),'source_sha256':canonical_evidence_hash.sha256_file(source/'early_main.py')}
runtime=customer_runtime_runner.run(source,cli_probe=probe,**identity)
put(out/'packaging-runtime-result.json',runtime)
assert customer_runtime_runner.inspect(source)['status']=='PASS'
package_dir=R/'dogfood-packages'
manifest=package_project(source,output_dir=package_dir,startup_command='powershell -NoProfile -File start.ps1',
    run_log_path=out/'checker-output.log',screenshot_path=out/'gui-early.png',known_limits=limits)
assert manifest['status'] in {'PASS','PASS_WITH_LIMITS'}, manifest
put(out/'receipt.json',{'kind':'LocalM7DogfoodCheckpoint','M7':'VERIFIED','final_product_complete':False,
    'local_url':'http://127.0.0.1:8767','startup_script':str(out/'start.ps1'),
    'source_identities_ref':str(out/'original-source-identities.json'),'independent_observation':observation,
    'package_manifest':manifest,'host_business_patches':0,'known_limits':limits})
print(json.dumps({'dogfood':str(out),'package_status':manifest['status'],'final_product_complete':False}))
