"""Project-declared semantic context. No domain or selection policy."""
from dataclasses import dataclass
import json
from .strategy import StrategyDeclaration
from .model import stable_hash


@dataclass(frozen=True)
class ContextDescriptor:
    canonical_json: str

    def __post_init__(self):
        if len(self.canonical_json.encode('utf-8')) > 16384:
            raise ValueError('CONTEXT_SIZE_BOUND_EXCEEDED')
        value = json.loads(self.canonical_json)
        if not isinstance(value, dict) or set(value) != {'schema', 'features'}:
            raise ValueError('CONTEXT_CANONICAL_DOCUMENT_REQUIRED')
        schema = value['schema']
        if (not isinstance(schema, dict) or set(schema) != {'name', 'version', 'fields'}
                or not isinstance(schema['name'], str) or not schema['name'] or len(schema['fields'])>64):
            raise ValueError('CONTEXT_SCHEMA_REQUIRED')
        declared = StrategyDeclaration.declare(value['features'], schema={
            'version':schema['version'], 'fields':schema['fields']})
        canonical = json.dumps({'schema':schema, 'features':declared.parameters},
            sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        if canonical != self.canonical_json:
            raise ValueError('CONTEXT_CANONICAL_DOCUMENT_REQUIRED')

    @classmethod
    def declare(cls, features, *, schema, metadata=None):
        if not isinstance(schema, dict) or set(schema) != {'name', 'version', 'fields'}:
            raise ValueError('CONTEXT_SCHEMA_REQUIRED')
        declared = StrategyDeclaration.declare(features, schema={
            'version':schema['version'], 'fields':schema['fields']}, metadata=metadata)
        return cls(json.dumps({'schema':schema, 'features':declared.parameters},
            sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False))

    @property
    def fingerprint(self):
        return stable_hash(json.loads(self.canonical_json))

    def as_dict(self):
        return {**json.loads(self.canonical_json), 'context_identity':self.fingerprint}

    @classmethod
    def from_dict(cls, value):
        result = cls.declare(value['features'], schema=value['schema'])
        if value.get('context_identity', result.fingerprint) != result.fingerprint:
            raise ValueError('CONTEXT_IDENTITY_MISMATCH')
        return result
