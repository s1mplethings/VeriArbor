"""Bind qualified independent B01 evidence into the original FileRunStore."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,datetime
from cgkn.state import FileRunStore
from cgkn.state.provenance import put_evidence
from veriarbor.block import Block
from veriarbor.port import Port
from veriarbor.contract import Contract
from veriarbor.effects import EffectContract
from veriarbor.variant import Variant
from veriarbor.certificate import Certificate
from veriarbor.model import stable_hash

R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
store=FileRunStore(R/'state');pid='iter132-promotion-studio';rid='promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt_path=M/'b01-current-9edfb2e6/receipt.json';receipt=read(receipt_path)
qualification=read(M/'B01_CHECKER_QUALIFICATION/receipt.json')
assert receipt['status']==qualification['status']=='PASS'
assert len(receipt['checks'])==13 and len(qualification['controls'])==8
assert receipt['checker_sha256']==qualification['checker_sha256']==sha(Path('D:/VeriArbor/tools/m12_b01_acceptance.py'))
assert receipt['source_sha256']==sha(R/'candidate/main.py')
source=(R/'candidate/main.py').read_text(encoding='utf8')
sections={
 'main.py#project-bootstrap':source[source.index('// --- Projects ---'):source.index('async function loadProjectsForCampaigns()')],
 'main.py#project-dom':source[source.index('<!-- Projects View -->'):source.index('<!-- Signals View -->')],
 'main.py#startup':source[source.index('// Init'):source.index('</script>')],
 'main.py#shared-browser-runtime':source[source.index('<script>'):source.index('// --- Projects ---')],
 'main.py#shared-render-helpers':source[source.index('// Helpers'):source.index('// Init')],
 'main.py#state-endpoint':source[source.index('    def _serve_state('):source.index('    def _serve_media(')],
}
artifacts=tuple((name,hashlib.sha256(value.encode()).hexdigest()) for name,value in sections.items())
input_contract=Contract.create({'type':'object','properties':{'action':{'type':'string','enum':['start','create','select','refresh']}},'required':['action']},
    'Browser project lifecycle; project.list first, real project.create identity, valid selected project_id before state request.')
output_contract=Contract.create({'type':'object','properties':{'project_id':{'type':['string','null']},'visible_name':{'type':'string'}},'required':['project_id','visible_name']},
    'Real empty/list UI; created name visible and selected; refresh restores validated selection and fetches matching project state; no initialization errors.')
effects=EffectContract(reads=('M1.project.list','M1.project.get','selected-project browser storage'),
 writes=('M1.project.create','selected-project browser storage','project DOM'),external_effects=('loopback HTTP only',),
 persistence='existing M1 store and browser selection; refresh tested',idempotency='project creation not promised idempotent',
 concurrency='existing ThreadingHTTPServer unchanged; GUI sequential awaited requests',ordering='list before selection before state',rollback='source bounded patch journal; isolated acceptance data')
variant=Variant('B01-9edfb2e6',artifacts,'VERIFIED')
block=Block('B01','ProjectBootstrapBlock',(Port('BrowserProjectAction','1','input',input_contract),),
    (Port('SelectedProjectView','1','output',output_contract),),effects,(variant,),variant.variant_id)
observation=put_evidence(store,pid,rid,{'kind':'QualifiedIndependentBlockObservation','block_id':'B01',
    'receipt':receipt,'raw_receipt_path':str(receipt_path),'raw_receipt_sha256':sha(receipt_path),
    'qualification':qualification,'source_sections':dict(artifacts),'full_source_sha256':receipt['source_sha256'],
    'acceptance_scope':'B01 only; no M12 or product completion granted'})
certificate=Certificate('B01',variant.variant_id,*block.boundary_hashes,
    tuple('B01:'+name for name in receipt['checks']),artifacts,(('B01.browser',receipt['checker_sha256']),),
    ('Only B01 is certified; M12/B02-B11 not verified.','Browser refresh tested; full product restart is a later block.'),
    (observation['path'],),datetime.datetime.now(datetime.timezone.utc).isoformat())
assert certificate.matches(block,{'B01.browser':receipt['checker_sha256']},evidence_authenticated=True)
payload={'kind':'AuthenticatedLocalBlockCertificate','block_id':'B01','status':'VERIFIED','reuse_status':'FROZEN_REUSABLE',
    'certificate':asdict(certificate),'certificate_fingerprint':certificate.fingerprint,'block':block.as_dict(),
    'source_sha256_at_verification':receipt['source_sha256'],'relevant_section_hashes':dict(artifacts),
    'neighbor_contract_hashes':{'M1_project_api_source':sha(R/'candidate/milestones/milestone_20f2614f6ae8403d4a4e/api.py'),
        'selected_state_endpoint':dict(artifacts)['main.py#state-endpoint']},
    'evidence_refs':[observation], 'invalidation_triggers':['Any certified section changes','M1 boundary/implementation changes','checker identity/qualification changes','browser/runtime identity becomes incompatible'],
    'authority':'Original FileRunStore evidence; VeriArbor Certificate verifies bound block identity; full GoalAcceptance unchanged',
    'host_business_patches':0}
ref=put_evidence(store,pid,rid,payload)
projection={**payload,'canonical_evidence_ref':ref}
(M/'B01_PROJECT_BOOTSTRAP_CERTIFICATE.json').write_text(json.dumps(projection,ensure_ascii=False,indent=2),encoding='utf8')
(M/'B01_PROJECT_BOOTSTRAP_ACCEPTANCE.json').write_text(json.dumps({'kind':'DerivedBlockAcceptanceView','status':'PASS',
    'source_sha256':receipt['source_sha256'],'canonical_observation':observation,'evidence_path':str(receipt_path),
    'checker_qualification':str(M/'B01_CHECKER_QUALIFICATION/receipt.json')},ensure_ascii=False,indent=2),encoding='utf8')
status=read(M/'M12_BLOCK_STATUS.json');status['blocks']['B01']='VERIFIED_FROZEN_REUSABLE';status['blocks']['B02']='READY_NOT_STARTED';status['M12']='INSUFFICIENT_CURRENT_EVIDENCE';status['B01_certificate_ref']=ref
(M/'M12_BLOCK_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'B01':'VERIFIED_FROZEN_REUSABLE','certificate_ref':ref,'M12':'NOT_VERIFIED','host_business_patches':0}))
