from dataclasses import replace
import pytest
from veriarbor.strategy import StrategyDeclaration, ExperimentBinding, input_set_identity


SCHEMA = {'version':'selection@1', 'fields':{
    'max_items':{'type':'integer','default':3},
    'weights':{'type':'object','default':{'quality':1,'coverage':2}},
    'source_policy':{'type':'string','default':'declared-only'}}}


def test_all_behavior_fields_and_defaults_are_canonical():
    initial = StrategyDeclaration.declare({},schema=SCHEMA)
    same = StrategyDeclaration.declare({'source_policy':'declared-only',
        'weights':{'coverage':2.0,'quality':1},'max_items':3},schema=SCHEMA,
        metadata={'timestamp':'later','run_directory':'another directory'})
    assert initial.fingerprint == same.fingerprint
    assert initial.fingerprint != StrategyDeclaration.declare({'max_items':4},schema=SCHEMA).fingerprint
    parameters = initial.parameters
    parameters['weights']['quality'] = 99
    assert initial.parameters['weights']['quality'] == 1


@pytest.mark.parametrize('parameters',[{'max_clips':5},{'max_items':True},{'weights':{'x':float('nan')}}])
def test_undeclared_or_noncanonical_execution_fields_fail(parameters):
    with pytest.raises(ValueError):
        StrategyDeclaration.declare(parameters,schema=SCHEMA)


def test_declared_project_extension_is_part_of_identity():
    schema = {'version':SCHEMA['version'], 'fields':{**SCHEMA['fields'],
        'max_clips':{'type':'integer','default':2}}}
    assert StrategyDeclaration.declare({},schema=schema).fingerprint != StrategyDeclaration.declare(
        {'max_clips':3},schema=schema).fingerprint
    with pytest.raises(ValueError,match='METADATA'):
        StrategyDeclaration.declare({},schema=schema,metadata={'max_clips':3})


def test_experiment_binds_exact_inputs_strategy_and_checker():
    refs=[{'path':'a','sha256':'a'*64},{'path':'b','sha256':'b'*64}]
    assert input_set_identity(refs)==input_set_identity(list(reversed(refs)))
    binding=ExperimentBinding('e','strategy',input_set_identity(refs),'evaluator','checker','campaign')
    for field in ('strategy_identity','input_set_identity','evaluator_identity','checker_identity','campaign_id'):
        assert replace(binding,**{field:'changed'}).fingerprint!=binding.fingerprint
    with pytest.raises(ValueError,match='DUPLICATE'):
        input_set_identity([refs[0],refs[0]])


def test_direct_strategy_construction_cannot_bypass_schema():
    import json
    valid = StrategyDeclaration.declare({}, schema=SCHEMA)
    assert StrategyDeclaration(valid.canonical_json) == valid
    data = json.loads(valid.canonical_json)
    data['parameters']['max_clips'] = 9
    with pytest.raises(ValueError, match='UNDECLARED'):
        StrategyDeclaration(json.dumps(data, sort_keys=True, separators=(',', ':')))
