import pytest
from veriarbor.context import ContextDescriptor


def test_declared_context_identity_excludes_operational_metadata():
    schema = {'name':'fixture','version':'1','fields':{
        'x':{'type':'integer'}, 'y':{'type':'array'}}}
    a = ContextDescriptor.declare({'x':1,'y':['a','b']},schema=schema,metadata={'timestamp':'one'})
    b = ContextDescriptor.declare({'y':['a','b'],'x':1},schema=schema,metadata={'timestamp':'two'})
    assert a.fingerprint==b.fingerprint
    assert ContextDescriptor.from_dict(a.as_dict())==a
    assert ContextDescriptor.declare({'x':2,'y':['a','b']},schema=schema).fingerprint!=a.fingerprint
    with pytest.raises(ValueError): ContextDescriptor.from_dict({**a.as_dict(),'context_identity':'wrong'})
    with pytest.raises(ValueError): ContextDescriptor.declare({'x':1,'y':[],'extra':1},schema=schema)
    with pytest.raises(ValueError): ContextDescriptor.declare({'x':True,'y':[]},schema=schema)
