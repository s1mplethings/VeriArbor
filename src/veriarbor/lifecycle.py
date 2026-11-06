"""Certificates, branch vitality and bounded active-context selection."""
from dataclasses import asdict, dataclass
from enum import StrEnum
from .model import NodeKind, stable_hash


@dataclass(frozen=True)
class CapabilityCertificate:
    capability_id: str
    semantic_name: str
    input_contract: dict
    output_contract: dict
    preconditions: tuple[str, ...]
    effects: tuple[str, ...]
    acceptance_ids: tuple[str, ...]
    artifact_versions: dict[str, str]
    checker_versions: dict[str, str]
    known_limits: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    issued_at: float
    expires_at: float | None
    invalidation_triggers: tuple[str, ...]

    def valid(self, *, artifacts, checkers, now, triggers=()):
        return (bool(self.acceptance_ids) and bool(self.evidence_refs) and bool(self.provenance_refs)
                and bool(self.artifact_versions) and bool(self.checker_versions)
                and now >= self.issued_at and (self.expires_at is None or now < self.expires_at)
                and not set(triggers).intersection(self.invalidation_triggers)
                and all(artifacts.get(k) == v and bool(v) for k, v in self.artifact_versions.items())
                and all(checkers.get(k) == v and bool(v) for k, v in self.checker_versions.items()))

    def as_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return stable_hash(self.as_dict())


class BranchVitality(StrEnum):
    UNPROVEN = 'UNPROVEN'
    ACTIVE = 'ACTIVE'
    GROWING = 'GROWING'
    VERIFIED = 'VERIFIED'
    STALLED = 'STALLED'
    THROTTLED = 'THROTTLED'
    QUARANTINED = 'QUARANTINED'
    PRUNED = 'PRUNED'
    ARCHIVED = 'ARCHIVED'


def vitality(kind, *, verified=False, progress=False, regression=False,
             qualified_counterexample=False, no_progress_attempts=0):
    if verified:
        return BranchVitality.VERIFIED
    if regression:
        return BranchVitality.QUARANTINED
    if qualified_counterexample and kind == NodeKind.STRATEGY_OR:
        return BranchVitality.PRUNED
    if progress:
        return BranchVitality.GROWING
    return BranchVitality.THROTTLED if no_progress_attempts >= 2 else BranchVitality.STALLED if no_progress_attempts else BranchVitality.ACTIVE


@dataclass(frozen=True)
class ActiveCrown:
    active: tuple[str, ...]
    deferred: tuple[str, ...]
    truncated: bool


def active_crown(*, obligations, running, strategies, limit):
    """Mandatory obligations/running leaves never disappear to meet a budget.

    Overflow requires host expansion/backpressure; it is not silently pruned.
    Deferred strategies remain available in the host's archive/trunk.
    """
    mandatory = tuple(sorted(set(obligations) | set(running)))
    if type(limit) is not int or limit < len(mandatory):
        raise ValueError('crown budget cannot hide mandatory obligations/running leaves')
    alternatives = tuple(sorted(set(strategies) - set(mandatory)))
    slots = limit - len(mandatory)
    return ActiveCrown(mandatory + alternatives[:slots], alternatives[slots:], len(alternatives) > slots)


def hydrate_archive(archive, ref, expected_hash):
    payload = archive.read(ref)
    if stable_hash(payload) != expected_hash:
        raise ValueError('archive object identity mismatch')
    return payload
