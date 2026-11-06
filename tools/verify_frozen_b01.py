"""Authenticate B01 certificate and compare current certified sections, no browser."""
from pathlib import Path
import hashlib,json,sys
from veriarbor.block import Block
from veriarbor.certificate import Certificate
from veriarbor.variant import Variant
from dataclasses import replace
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    projection=json.loads((M/'B01_PROJECT_BOOTSTRAP_CERTIFICATE.json').read_text(encoding='utf8'))
    ref=projection['canonical_evidence_ref'];path=R/'state'/ref['path'];assert sha(path)==ref['sha256']
    payload=json.loads(path.read_text(encoding='utf8'))
    for evidence in payload['evidence_refs']:
        target=R/'state'/evidence['path'];assert sha(target)==evidence['sha256']
        observed=json.loads(target.read_text(encoding='utf8'))
        assert observed['receipt']['status']==observed['qualification']['status']=='PASS'
    source=(R/'candidate/main.py').read_text(encoding='utf8')
    bounds={'project-bootstrap':('// --- Projects ---','async function loadProjectsForCampaigns()'),
        'project-dom':('<!-- Projects View -->','<!-- Signals View -->'),'startup':('// Init','</script>'),
        'shared-browser-runtime':('<script>','// --- Projects ---'),'shared-render-helpers':('// Helpers','// Init'),
        'state-endpoint':('    def _serve_state(','    def _serve_media(')}
    sections={}
    for key,(a,b) in bounds.items():
        start=source.index(a);end=source.index(b,start);sections['main.py#'+key]=hashlib.sha256(source[start:end].encode()).hexdigest()
    assert sections==payload['relevant_section_hashes'],'B01 certified boundary changed'
    assert sha(R/'candidate/milestones/milestone_20f2614f6ae8403d4a4e/api.py')==payload['neighbor_contract_hashes']['M1_project_api_source']
    block=Block.from_dict(payload['block']);cert=Certificate(**payload['certificate'])
    current=replace(block,variants=(Variant(block.active_variant,tuple(sections.items()),'VERIFIED'),))
    checker=sha(Path('D:/VeriArbor/tools/m12_b01_acceptance.py'))
    assert cert.matches(current,{'B01.browser':checker},evidence_authenticated=True)
    return {'status':'FROZEN_CERTIFICATE_CURRENT','block_id':'B01','current_full_source_sha256':sha(R/'candidate/main.py'),
        'certificate_ref':ref,'certificate_fingerprint':cert.fingerprint,'reused_acceptance_count':len(cert.acceptance_ids),
        'current_sections':sections,'browser_reruns':0,'provider_calls':0,'full_m12_verified':False}
if __name__=='__main__':
    result=verify();out=M/('B01_REUSE_'+result['current_full_source_sha256'][:8]+'.json')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result))
