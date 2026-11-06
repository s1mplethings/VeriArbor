"""Read-only original-state shadow and derived maps. Not a new authority."""
import json, hashlib, sys
from pathlib import Path
H=Path('F:/CGKN-LeanLoop-V1-20261101');M=H/'migration/veriarbor'
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
from cgkn.state.provenance import ProvenanceGate
from cgkn.adapters.veriarbor.substitution_adapter import milestone_block, replacements
from cgkn.adapters.veriarbor.verification_adapter import goal_verification_keys
from veriarbor.compatibility import compare_blocks
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):
    with p.open('x',encoding='utf-8') as out:json.dump(d,out,indent=2,ensure_ascii=False)
p=read(R/'profile.json');S=R/'state'/p['project_id']/p['run_id'];authority=S/'goal_acceptance.json'
before=sha(authority);data=read(authority);store=FileRunStore(R/'state')
acceptance=GoalAcceptance(store,p['project_id'],p['run_id'],data['requirements'],data['checker_bindings'])
view=acceptance.view();assert before==sha(authority)
baseline=read(M/'block-port-shadow-before.json')
diff={g['id']:{'before':baseline['verdicts'].get(g['id']),'after':g['verdict']} for g in view['goals']
      if baseline['verdicts'].get(g['id'])!=g['verdict']}
assert not diff,diff
blocks={};unqualified=[]
for g in view['goals']:
    if not g.get('milestone_contract'):continue
    try:blocks[g['id']]=milestone_block(g,view['subject_identities']).as_dict()
    except (KeyError,ValueError) as exc:unqualified.append({'goal':g['id'],'reason':str(exc)})
gate=ProvenanceGate(store,p['project_id'],p['run_id'])
with gate.read_binding_snapshot():
    proofs,checkers=replacements(acceptance,gate)
put(M/'BLOCK_MAP.json',{'kind':'DerivedBlockMap','authority':str(authority),'authority_sha256':before,'blocks':blocks,'unqualified':unqualified})
put(M/'PORT_MAP.json',{'kind':'DerivedPortMap','ports':{k:{'inputs':v['input_ports'],'outputs':v['output_ports'],'effects':v['effect_contract']} for k,v in blocks.items()},'legacy_policy':'Exact opaque frozen semantics; no inferred structural compatibility for legacy textual contracts'})
put(M/'ADAPTER_MAP.json',{'kind':'DerivedAdapterMap','production_generated_adapters':[],'adapter_chains':[],'reason':'No incompatible port change has yet been admitted; identity migration needs no transform adapter.'})
put(M/'CERTIFICATE_MAP.json',{'kind':'DerivedCertificateMap','authority':str(authority),'current_verification_keys':goal_verification_keys(view),
    'replacement_certificates':[{'old':p.old_certificate.fingerprint,'new':p.new_certificate.fingerprint,'block':p.candidate.block_id,'artifacts':p.candidate.variant.artifacts,'authenticated':p.evidence_authenticated} for p in proofs],
    'known_limits':'Legacy aggregate predicates remain aggregate, not invented fine-grained Block/Edge checks.'})
put(M/'BLOCK_PORT_SHADOW_RESULTS.json',{'kind':'BlockPortV1Shadow','authority_sha256':before,'authority_unchanged':before==sha(authority),
    'goal_rows':len(view['goals']),'verdict_differences':diff,'mapped_blocks':len(blocks),'unqualified':unqualified,
    'certified_identical_replacement_pairs':len(proofs),'no_business_source_writes':True,'no_provider_calls':True,
    'production_runtime_scope':'GoalAcceptance identical dependency carry and compiler check dedup; DAG historical retry validation remains conservative until its own certified boundary integration.'})
print(json.dumps({'shadow_diff':len(diff),'blocks':len(blocks),'replacement_pairs':len(proofs),'unqualified':len(unqualified)}))
