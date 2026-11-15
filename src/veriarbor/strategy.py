"""Canonical behavior declarations and immutable experiment identities.

No execution, storage or promotion policy lives in this contract module.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math
from .model import stable_hash


def _canonical(value):
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ValueError('strategy keys must be strings')
        return {k:_canonical(v) for k,v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('nonfinite strategy parameter')
        return int(value) if value.is_integer() else value
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError('strategy parameter must be JSON data')


@dataclass(frozen=True)
class StrategyDeclaration:
    canonical_json: str

    def __post_init__(self):
        document = json.loads(self.canonical_json)
        if not isinstance(document, dict) or set(document) != {'schema', 'parameters'}:
            raise ValueError('STRATEGY_CANONICAL_DOCUMENT_REQUIRED')
        normalized = self._document(document['parameters'], schema=document['schema'])
        if self.canonical_json != json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                                             separators=(',', ':'), allow_nan=False):
            raise ValueError('STRATEGY_CANONICAL_DOCUMENT_REQUIRED')

    @classmethod
    def declare(cls, parameters, *, schema, metadata=None):
        document = cls._document(parameters, schema=schema, metadata=metadata)
        return cls(json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(',',':'), allow_nan=False))

    @staticmethod
    def _document(parameters, *, schema, metadata=None):
        if (not isinstance(schema, dict) or set(schema) != {'version','fields'}
                or not isinstance(schema['version'], str) or not schema['version']
                or not isinstance(schema['fields'], dict) or not isinstance(parameters, dict)):
            raise ValueError('STRATEGY_SCHEMA_REQUIRED')
        if set(parameters)-set(schema['fields']):
            raise ValueError('UNDECLARED_EXECUTION_PARAMETER')
        values = {}
        types = {'string':(str,), 'integer':(int,), 'number':(int,float), 'boolean':(bool,),
                 'object':(dict,), 'array':(list,tuple)}
        for name, field in schema['fields'].items():
            if (not isinstance(field, dict) or set(field)-{'type','default','required'}
                    or field.get('type') not in types):
                raise ValueError('STRATEGY_FIELD_SCHEMA_INVALID')
            if name not in parameters and 'default' not in field:
                if field.get('required', True):
                    raise ValueError('STRATEGY_PARAMETER_MISSING:'+name)
                continue
            value = parameters[name] if name in parameters else deepcopy(field['default'])
            if type(value) not in types[field['type']]:
                raise ValueError('STRATEGY_PARAMETER_TYPE:'+name)
            values[name] = _canonical(value)
        if metadata is not None and (not isinstance(metadata, dict) or set(metadata)-{
                'timestamp','run_directory','log_filename','temporary_path'}):
            raise ValueError('UNKNOWN_OPERATIONAL_METADATA')
        return {'schema':_canonical(schema), 'parameters':values}

    @property
    def parameters(self):
        return json.loads(self.canonical_json)['parameters']

    @property
    def fingerprint(self):
        return stable_hash(json.loads(self.canonical_json))

    def as_dict(self):
        return {**json.loads(self.canonical_json), 'strategy_identity':self.fingerprint}


@dataclass(frozen=True)
class ExperimentBinding:
    experiment_id: str
    strategy_identity: str
    input_set_identity: str
    evaluator_identity: str
    checker_identity: str
    campaign_id: str

    def __post_init__(self):
        if any(not isinstance(v, str) or not v.strip() for v in vars(self).values()):
            raise ValueError('EXACT_EXPERIMENT_BINDING_REQUIRED')

    @property
    def fingerprint(self):
        return stable_hash(vars(self))

    def as_dict(self):
        return {**vars(self), 'experiment_identity':self.fingerprint}


def input_set_identity(references):
    if not isinstance(references, (list, tuple)) or not references:
        raise ValueError('EXPERIMENT_INPUT_SET_REQUIRED')
    if any(not isinstance(r, dict) or set(r) != {'path','sha256'}
           or not isinstance(r['path'], str) or not r['path']
           or not isinstance(r['sha256'], str) or len(r['sha256']) != 64 for r in references):
        raise ValueError('EXPERIMENT_INPUT_IDENTITY_REQUIRED')
    if len({r['path'] for r in references}) != len(references):
        raise ValueError('EXPERIMENT_DUPLICATE_INPUT')
    return stable_hash(sorted(references, key=lambda r:r['path']))
