from dataclasses import replace
import json
import pytest
from veriarbor.governance import (EvidenceDerivation,count_independent,EvaluationScope,
    LegacyPolicy,legacy_scope,require_legacy,ClaimEvidenceRelation)
from veriarbor.execution_authority import CriticalCheckRegistry,CriticalCheckSpec,DecisionRecord


def checker_a(decisions,context):
    return 'PASS' if len(decisions)>=context['checker_policy']['minimum'] else 'FAIL'


def checker_b(decisions,context):
    return 'UNKNOWN'


def test_checker_identity_code_policy_version_and_roundtrip():
    r=CriticalCheckRegistry();r.register('x',checker_a,version='1.2',policy={'minimum':1})
    first=r.identity('x');assert r.identity('x')==first
    r=CriticalCheckRegistry();r.register('x',checker_a,version='1.2',policy={'minimum':2})
    assert r.identity('x').policy_hash!=first.policy_hash
    assert r.identity('x').implementation_hash==first.implementation_hash
    r=CriticalCheckRegistry();r.register('x',checker_b,version='2')
    assert r.identity('x').implementation_hash!=first.implementation_hash
    assert r.audit_identities({'x':first.as_dict()})[0]['status']=='HISTORICAL_CHECKER_VERSION_MISMATCH'
    result=r.evaluate(CriticalCheckSpec('c','a→b','x',expected_version='1.2'),(DecisionRecord('d','a→b','rule',check_id='c'),),{})
    assert result.status=='UNKNOWN' and result.reason=='CHECKER_IDENTITY_MISMATCH'


@pytest.mark.parametrize('keys,expected',[(['a','a'],1),(['a','b'],2)])
def test_independent_rows(keys,expected):
    assert count_independent([EvidenceDerivation(str(i),independence_key=k) for i,k in enumerate(keys)])==expected


def test_multimodal_duplicate_derivation_cannot_mint_events():
    rows=[EvidenceDerivation(m,underlying_event_id='one') for m in ('text','audio','vision')]
    rows.append(EvidenceDerivation('copy',('text',),independence_key='fake-new',derivation_type='DUPLICATE'))
    assert count_independent(rows)==1
    with pytest.raises(ValueError,match='INDEPENDENCE_POLICY_VIOLATION'):
        count_independent([EvidenceDerivation('no-identity')])
    with pytest.raises(ValueError,match='cyclic'):
        count_independent([EvidenceDerivation('a',('b',),derivation_type='DERIVED'),EvidenceDerivation('b',('a',),derivation_type='DERIVED')])


@pytest.mark.parametrize('strategy,allowed',[('FULL_POPULATION',True),('RANDOM_SAMPLE',True),
    ('STRATIFIED_SAMPLE',True),('TOP_K_BIASED',False),('DIAGNOSTIC',False),('UNKNOWN',False),('HUMAN_SELECTED',False)])
def test_evaluation_scope(strategy,allowed):
    s=EvaluationScope('e','population','sample','hash',strategy,'selection','NONE','population',
        ('POPULATION','DIAGNOSTIC'),{},population_hash='hash',generalization_target='target')
    assert s.allows('GENERALIZATION_VERIFIED','POPULATION') is allowed
    assert s.allows('UTILITY_VERIFIED','DIAGNOSTIC')
    assert EvaluationScope(**json.loads(json.dumps(s.as_dict())))==s


def test_legacy_explicit_allowlist_and_events():
    with pytest.raises(ValueError,match='LEGACY_NOT_ALLOWED'):require_legacy()
    with pytest.raises(ValueError,match='LEGACY_NOT_ALLOWED'):
        with legacy_scope(LegacyPolicy(),caller='x',reason='test',event_sink=lambda e:None):pass
    events=[]
    with legacy_scope(LegacyPolicy(True,('test.migration',)),caller='test.migration',reason='offline migration',event_sink=events.append):
        require_legacy(project_id='p',run_id='r')
    assert events[0]['caller']=='test.migration' and events[0]['reason']=='offline migration'
    assert events[0]['project_id']=='p' and events[0]['run_id']=='r' and events[0]['timestamp']
    with pytest.raises(ValueError,match='LEGACY_NOT_ALLOWED'):require_legacy()


def test_relation_immutable_and_versioned():
    relation=ClaimEvidenceRelation('r','claim',('e',),'SUPPORTS',{'checker_id':'x'},{'project_id':'p'},'rule')
    assert ClaimEvidenceRelation(**json.loads(json.dumps(relation.as_dict())))==relation
    with pytest.raises(TypeError):relation.scope['project_id']='forged'
