"""Serializable generic inputs; no host imports or concrete persistence."""
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from hashlib import sha256
import json


def stable_hash(value):
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    return sha256(raw).hexdigest()


class NodeKind(StrEnum):
    OBLIGATION_AND = 'OBLIGATION_AND'
    STRATEGY_OR = 'STRATEGY_OR'
    EXECUTION_LEAF = 'EXECUTION_LEAF'
    CERTIFICATE_REF = 'CERTIFICATE_REF'
    NOGOOD_REF = 'NOGOOD_REF'


class Status(StrEnum):
    UNPROVEN = 'UNPROVEN'
    VERIFIED = 'VERIFIED'
    FAILED = 'FAILED'
    BLOCKED = 'BLOCKED'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True)
class Node:
    id: str
    kind: NodeKind
    children: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    required: bool = True
    required_handoffs: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'kind', NodeKind(self.kind))
        object.__setattr__(self, 'children', tuple(self.children))
        object.__setattr__(self, 'dependencies', tuple(self.dependencies))
        object.__setattr__(self, 'required_handoffs', tuple(self.required_handoffs))
        if not self.id or self.id in self.children or self.id in self.dependencies:
            raise ValueError('invalid node identity or self-reference')
        if len(set(self.children)) != len(self.children):
            raise ValueError('duplicate child')


@dataclass(frozen=True)
class Evidence:
    """Host-qualified receipt binding. The library cannot authenticate receipts."""
    verdict: str
    object_versions: dict[str, str]
    checker_versions: dict[str, str]
    evidence_refs: tuple[str, ...]
    qualified: bool = False
    source_type: str = ''
    confidence: float | None = None
    scope: dict[str, str] = field(default_factory=dict)
    usable_for: tuple[str, ...] = ()
    forbidden_for: tuple[str, ...] = ()
    producer: str = ''
    producer_version: str = ''
    context: dict[str, str] = field(default_factory=dict)

    def current(self, objects, checkers):
        return (self.qualified and bool(self.evidence_refs) and bool(self.object_versions)
                and bool(self.checker_versions)
                and all(objects.get(k) == v and bool(v) for k, v in self.object_versions.items())
                and all(checkers.get(k) == v and bool(v) for k, v in self.checker_versions.items()))


@dataclass(frozen=True)
class Event:
    node_id: str
    event_type: str
    evidence_refs: tuple[str, ...] = ()
    payload: dict = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return stable_hash(self.as_dict())


@dataclass(frozen=True)
class Receipt:
    node_id: str
    operation: str
    payload_hash: str
    evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def as_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return stable_hash(self.as_dict())
