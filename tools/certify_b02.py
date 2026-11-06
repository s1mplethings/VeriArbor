"""Seal qualified B02 evidence in original FileRunStore; never grant M12."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,datetime,sys
from cgkn.state import FileRunStore
from cgkn.state.provenance import put_evidence
from veriarbor.block import Block
from veriarbor.port import Port
from veriarbor.contract import Contract
from veriarbor.effects import EffectContract
from veriarbor.variant import Variant
from veriarbor.certificate import Certificate
from veriarbor.compatibility import compare_ports,PortCompatibility
from verify_frozen_b01 import verify as verify_b01
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt_path=Path(sys.argv[1]);qualification_path=Path(sys.argv[2])
receipt=read(receipt_path);qualification=read(qualification_path)
assert receipt['status']==qualification['status']=='PASS'
assert receipt['concurrent_preview']['passed'] is True
assert receipt['checker_dependencies']['B02_concurrency']==sha(Path('D:/VeriArbor/tools/b02_upload_port_observer.py'))
assert len(receipt['checks'])>=39 and receipt['adapter_edge']['status']=='PASS'
assert receipt['dispatch_boundary']['status']=='PASS'
assert receipt['checker_dependencies']['B02_dispatch']==sha(Path('D:/VeriArbor/tools/b02_dispatch_boundary_probe.py'))
assert receipt['checker_sha256']==qualification['checker_sha256']==sha(Path('D:/VeriArbor/tools/m12_b02_acceptance.py'))
assert receipt['source_sha256']==sha(R/'candidate/main.py')
assert all(sha(R/'candidate'/name)==expected for name,expected in receipt['subject_hashes'].items())
assert receipt['checker_dependencies']['B01_preflight']==sha(Path('D:/VeriArbor/tools/m12_b01_acceptance.py'))
assert {'positive','negative','mutation'}<={c['kind'] for c in qualification['controls']}
assert all(c['passed'] is True for c in qualification['controls'])
b01=verify_b01();store=FileRunStore(R/'state');pid='iter132-promotion-studio';rid='promotion-05'
source=(R/'candidate/main.py').read_text(encoding='utf8')
bounds={'adapter':('HANDLERS = {','class ThreadedHTTPServer'),
    'media-serving':('    def _serve_media(','    def _serve_index('),
    'media-dom':('    <!-- Media View -->','    <script>'),'media-browser':('// --- Media ---','// Helpers')}
sections={}
for name,(a,b) in bounds.items():
    start=source.index(a);end=source.index(b,start);sections['main.py#'+name]=hashlib.sha256(source[start:end].encode()).hexdigest()
meaning='Import exact user-selected media bytes and kind into the selected project through the existing M11 core.'
schema=lambda fields:{'type':'object','properties':{k:{'type':'string'} for k in fields},'required':fields,'additionalProperties':False}
browser=Port('BrowserFilePort','1','input',Contract.create(schema(['project_id','kind','filename','data']),meaning))
server=Port('ServerPathPort','1','input',Contract.create(schema(['project_id','kind','path']),meaning))
output=Port('OwnedMediaPort','1','output',Contract.create(schema(['id','project_id','kind','sha256','path','status']),
    'Existing M11 persistent identity and exact bytes; project-owned previews survive process restart.'))
effects=EffectContract(reads=('browser selected file','M1 project identity','M11 media metadata'),
    writes=('isolated temporary file','existing M11 durable media copy','media UI'),external_effects=('loopback HTTP only',),
    persistence='M11 durable copy survives process restart independently of temporary file',
    idempotency='import creates new media identity; no implicit deduplication promised',
    concurrency='original threaded server retained; shared M11 store coordinated at adapter boundary; 12 simultaneous preview reads preserve exact bytes',
    ordering='decode -> confined temporary path -> original M11 import -> cleanup on success/failure',
    rollback='original bounded patch receipts; temporary files cleaned; backend failure preserved')
variant=Variant('B02-'+receipt['source_sha256'][:8],tuple(sections.items()),'VERIFIED')
block=Block('B02','BrowserUploadAdapterBlock',(browser,),(output,),effects,(variant,),variant.variant_id)
observation=put_evidence(store,pid,rid,{'kind':'QualifiedIndependentBlockObservation','block_id':'B02','receipt':receipt,
    'raw_receipt_path':str(receipt_path),'raw_receipt_sha256':sha(receipt_path),'qualification':qualification,
    'source_sections':sections,'full_source_sha256':receipt['source_sha256'],'B01_reuse':b01,'acceptance_scope':'B02 only; no M12 completion granted'})
certificate=Certificate('B02',variant.variant_id,*block.boundary_hashes,tuple('B02:'+x for x in receipt['checks']),
    tuple(sections.items()),(('B02.browser',receipt['checker_sha256']),),
    ('Explicit effectful product adapter; automatic field-rename adapter is not used.','Full VeriArbor V1 and M12 remain separate gates.'),
    (observation['path'],),datetime.datetime.now(datetime.timezone.utc).isoformat())
authenticated=certificate.matches(block,{'B02.browser':receipt['checker_sha256']},evidence_authenticated=True)
assert authenticated
class ExplicitCertifiedAdapterWitness:
    def connects(self,old,new):
        return authenticated and old==browser and new==server and receipt['adapter_edge']['status']=='PASS'
assert compare_ports(browser,server)==PortCompatibility.BREAKING
assert compare_ports(browser,server,ExplicitCertifiedAdapterWitness())==PortCompatibility.ADAPTABLE
payload={'kind':'AuthenticatedLocalBlockCertificate','block_id':'B02','status':'VERIFIED','reuse_status':'FROZEN_REUSABLE',
    'certificate':asdict(certificate),'certificate_fingerprint':certificate.fingerprint,'block':block.as_dict(),
    'source_sha256_at_verification':receipt['source_sha256'],'relevant_section_hashes':sections,
    'neighbor_contract_hashes':{'M11_api_source':sha(R/'candidate/milestones/milestone_dbb8341c8910593063a8/api.py'),
        'B01_certificate':b01['certificate_fingerprint']},'evidence_refs':[observation],
    'compatibility_witness':{'classification':'ADAPTABLE','source_port':asdict(browser),'target_port':asdict(server),
        'implementation':'Worker-authored explicit temporary-file adapter in current product; runtime edge probe observes actual M11 call and cleanup',
        'automatic_adapter_generated':False,'full_veriarbor_v1_completed':False},
    'invalidation_triggers':['Certified source section changes','M11 contract/implementation changes','B01 project identity boundary changes','checker identity/qualification changes'],
    'authority':'Original FileRunStore evidence plus VeriArbor Certificate; not full GoalAcceptance','host_business_patches':0}
ref=put_evidence(store,pid,rid,payload)
(M/'B02_BROWSER_UPLOAD_ADAPTER_CERTIFICATE.json').write_text(json.dumps({**payload,'canonical_evidence_ref':ref},ensure_ascii=False,indent=2),encoding='utf8')
(M/'B02_BROWSER_UPLOAD_ACCEPTANCE.json').write_text(json.dumps({'kind':'DerivedBlockAcceptanceView','status':'PASS','source_sha256':receipt['source_sha256'],
    'canonical_observation':observation,'evidence_path':str(receipt_path),'checker_qualification':str(qualification_path)},ensure_ascii=False,indent=2),encoding='utf8')
status=read(M/'M12_BLOCK_STATUS.json');status['blocks']['B02']='VERIFIED_FROZEN_REUSABLE';status['blocks']['B03']='READY_NOT_STARTED';status['M12']='INSUFFICIENT_CURRENT_EVIDENCE';status['B02_certificate_ref']=ref
(M/'M12_BLOCK_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'B02':'VERIFIED_FROZEN_REUSABLE','certificate_ref':ref,'M12':'NOT_VERIFIED','host_business_patches':0}))
