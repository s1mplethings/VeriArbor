from dataclasses import asdict
import json
import pytest
from veriarbor.execution_authority import NodeExecutionPermit, CriticalCheckSpec, CriticalCheckRegistry, DecisionRecord
from veriarbor.capability import CapabilityContract
from veriarbor.model import stable_hash


def test_permit_deeply_immutable_and_serializable():
    p=NodeExecutionPermit('p','r','project','node','cap','a',1,'hash',{'nested':{'a':[1]}},
                          {},('filesystem',),{'calls':1},'worker',1)
    with pytest.raises(TypeError):p.input_bindings['nested']['a']=2
    with pytest.raises(TypeError):p.budget_scope['calls']=100
    assert NodeExecutionPermit(**json.loads(json.dumps(p.as_dict())))==p


def test_old_contract_fingerprint_and_new_roundtrip():
    c=CapabilityContract('cap','goal')
    old=asdict(c)
    for key in ('critical_checks','requires_claim_support','conflict_collection','claim_unknown_policy','independence_policy'):
        old.pop(key)
    assert CapabilityContract(**old).fingerprint==stable_hash(old)==c.fingerprint
    new=CapabilityContract('cap','goal',critical_checks=({'check_id':'x','semantic_transform':'a→b','checker_id':'checker'},))
    assert CapabilityContract(**json.loads(json.dumps(asdict(new))))==new


def test_missing_and_exception_checker_are_unknown():
    r=CriticalCheckRegistry();spec=CriticalCheckSpec('x','a→b','checker')
    assert r.evaluate(spec,(),{}).reason=='CHECKER_MISSING'
    def broken(*args):raise ValueError('fixture')
    r.register('checker',broken)
    assert r.evaluate(spec,(DecisionRecord('d','a→b','s',check_id='x'),),{}).status=='UNKNOWN'


def test_skill_cannot_promote_old_qualified_claims_without_lineage():
    from .test_capability_skills import manifest,validations
    from veriarbor.skills import promotion_check
    m=manifest()
    assert not promotion_check(m,validations(m))
