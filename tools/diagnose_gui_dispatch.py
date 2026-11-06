"""Record actual imported handler identities and isolated project creation."""
from pathlib import Path
import hashlib, importlib.util, json, sys
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out=M/sys.argv[1]
assert out.parent==M and not out.exists()
out.mkdir()
path=R/'candidate/main.py';sha=hashlib.sha256(path.read_bytes()).hexdigest()
sys.path.insert(0,str(R/'candidate'))
spec=importlib.util.spec_from_file_location('diagnostic_gui',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=[{'declared_route':tag,'actual_module_identity':handler.__globals__.get('MILESTONE_ID') if handler else None,
       'matches':bool(handler) and tag==handler.__globals__.get('MILESTONE_ID')} for tag,handler in module.HANDLERS.items()]
try:operation={'ok':True,'result':module.handle(str(out/'data'),{'milestone':'M1','op':'project.create','name':'Dispatch diagnostic'})}
except Exception as error:operation={'ok':False,'error':type(error).__name__+': '+str(error)}
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
report={'kind':'ActualGuiDispatchDiagnostic','source_sha256':sha,'routes':rows,'actual_project_create':operation,
        'acceptance_authority':False,'host_business_patches':0,'diagnostic_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
