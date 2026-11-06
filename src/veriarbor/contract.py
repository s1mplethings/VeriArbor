"""Canonical, immutable boundary contracts; unsupported schemas fail closed."""
from dataclasses import dataclass
import json
from .model import stable_hash


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False)


@dataclass(frozen=True)
class Contract:
    schema_json: str
    semantic: str

    def __post_init__(self):
        schema = json.loads(self.schema_json)
        if not isinstance(schema, dict) or not self.semantic:
            raise ValueError('contract requires schema and explicit semantics')
        object.__setattr__(self, 'schema_json', canonical(schema))

    @classmethod
    def create(cls, schema, semantic):
        return cls(canonical(schema), semantic)

    @property
    def schema(self):
        return json.loads(self.schema_json)

    @property
    def fingerprint(self):
        return stable_hash({'schema': self.schema, 'semantic': self.semantic})


def schema_subset(left, right):
    """Prove every left value is accepted by right for the supported subset.

    Unknown keywords are opaque: equality is safe, inferred compatibility is
    denied. This is intentionally not a complete JSON Schema implementation.
    """
    if left == right:
        return True
    if left.get('default') != right.get('default'):
        return False
    allowed = {'type', 'properties', 'required', 'additionalProperties',
               'items', 'enum', 'minimum', 'maximum', 'default'}
    if set(left) - allowed or set(right) - allowed:
        return False
    if left.get('type') != right.get('type'):
        return False
    if left.get('type') not in {'object', 'array', 'string', 'integer', 'number', 'boolean', 'null'}:
        return False
    if 'enum' in right and ('enum' not in left or
            any(v not in right['enum'] for v in left['enum'])):
        return False
    if left.get('minimum', float('-inf')) < right.get('minimum', float('-inf')):
        return False
    if left.get('maximum', float('inf')) > right.get('maximum', float('inf')):
        return False
    if left['type'] == 'object':
        lp, rp = left.get('properties', {}), right.get('properties', {})
        if not set(right.get('required', ())) <= set(left.get('required', ())):
            return False
        la, ra = left.get('additionalProperties', True), right.get('additionalProperties', True)
        if not isinstance(la, bool) or not isinstance(ra, bool):
            return False
        if not ra and (la or set(lp) - set(rp)):
            return False
        for key, spec in rp.items():
            if key in lp and not schema_subset(lp[key], spec):
                return False
            if key not in lp and la:  # old arbitrary property may violate new type
                return False
    if left['type'] == 'array':
        if 'items' in right and ('items' not in left or
                not schema_subset(left['items'], right['items'])):
            return False
    return True


def accepts(schema, value):
    """Validate the same deliberately bounded schema vocabulary for adapters."""
    types = {'object': dict, 'array': list, 'string': str, 'integer': int,
             'number': (int, float), 'boolean': bool, 'null': type(None)}
    kind = schema.get('type')
    if kind not in types or not isinstance(value, types[kind]):
        return False
    if kind in {'integer', 'number'} and isinstance(value, bool):
        return False
    if set(schema) - {'type', 'properties', 'required', 'additionalProperties', 'items', 'enum', 'minimum', 'maximum', 'default'}:
        return False
    if 'enum' in schema and value not in schema['enum']:
        return False
    if kind in {'integer', 'number'} and not (schema.get('minimum', float('-inf')) <= value <= schema.get('maximum', float('inf'))):
        return False
    if kind == 'object':
        props = schema.get('properties', {})
        if not set(schema.get('required', ())) <= value.keys():
            return False
        if schema.get('additionalProperties', True) is False and not value.keys() <= props.keys():
            return False
        if any(not accepts(props[k], v) for k, v in value.items() if k in props):
            return False
    if kind == 'array' and 'items' in schema and any(not accepts(schema['items'], v) for v in value):
        return False
    return True
