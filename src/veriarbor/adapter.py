"""Explicit, lossless field rename/default adapters. No inferred semantics."""
from dataclasses import dataclass
import json
from .port import Port
from .contract import schema_subset, canonical, accepts


@dataclass(frozen=True)
class Adapter:
    adapter_id: str
    source: Port
    target: Port
    renames: tuple[tuple[str, str], ...] = ()
    defaults_json: str = '{}'
    semantic_mapping: tuple[tuple[str, str], ...] = ()
    certificate_ref: str | None = None

    def __post_init__(self):
        object.__setattr__(self, 'renames', tuple(tuple(p) for p in self.renames))
        object.__setattr__(self, 'semantic_mapping', tuple(tuple(p) for p in self.semantic_mapping))
        defaults = json.loads(self.defaults_json)
        if not isinstance(defaults, dict):
            raise ValueError('AUTO_ADAPTER_DENIED: defaults must be fields')
        object.__setattr__(self, 'defaults_json', canonical(defaults))
        if not self._provable():
            raise ValueError('AUTO_ADAPTER_DENIED: mapping is ambiguous or loses information')

    def _provable(self):
        source, target = self.source.contract, self.target.contract
        if (not self.adapter_id or self.source.direction != self.target.direction or
                source.semantic != target.semantic):
            return False
        s, t = source.schema, target.schema
        if s.get('type') != 'object' or t.get('type') != 'object' or s.get('additionalProperties') is not False:
            return False
        mapping = dict(self.renames)
        if len(mapping) != len(self.renames) or set(self.renames) != set(self.semantic_mapping):
            return False
        props = s.get('properties', {})
        if not mapping.keys() <= props.keys():
            return False
        names = [mapping.get(k, k) for k in props]
        if len(names) != len(set(names)):
            return False
        converted = {**s, 'properties': {mapping.get(k, k): v for k, v in props.items()},
                     'required': [mapping.get(k, k) for k in s.get('required', [])]}
        for key, value in json.loads(self.defaults_json).items():
            if key in converted['properties'] or key not in t.get('properties', {}):
                return False
            # Only declared defaults may be synthesized; caller-owned mappings
            # are semantic declarations, never authority to invent required data.
            spec = t['properties'][key]
            if 'default' not in spec or spec['default'] != value or key in t.get('required', []) or not accepts(spec, value):
                return False
            converted['properties'][key] = {**spec, 'enum': [value]}
            converted['required'].append(key)
        return schema_subset(converted, t)

    def connects(self, old, new):
        return self.source == old and self.target == new and self._provable()

    def transform(self, value):
        if not accepts(self.source.contract.schema, value):
            raise ValueError('AUTO_ADAPTER_DENIED: unexpected input fields')
        mapping = dict(self.renames)
        result = {mapping.get(k, k): v for k, v in value.items()}
        for key, default in json.loads(self.defaults_json).items():
            result.setdefault(key, default)
        if not accepts(self.target.contract.schema, result):
            raise ValueError('AUTO_ADAPTER_DENIED: output contract violation')
        return result


def adapter_lifecycle(*, consumer_count, usage_count):
    if consumer_count < 0 or usage_count < 0:
        raise ValueError('negative usage')
    return 'ARCHIVE_REMOVE_FROM_PRODUCTION' if consumer_count == 0 else 'ACTIVE'
