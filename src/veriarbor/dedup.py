"""Deterministic keys and decisions over host-owned observations, no database."""
from dataclasses import dataclass, asdict
from .model import stable_hash


@dataclass(frozen=True)
class VerificationKey:
    target_block: str
    active_variant: str
    input_contract_hash: str
    output_contract_hash: str
    effect_contract_hash: str
    acceptance_id: str
    checker_hash: str
    directly_relevant_neighbor_contract_hashes: tuple[tuple[str, str], ...]
    artifact_hashes: tuple[tuple[str, str], ...]
    checker_qualification_hash: str = ''

    def __post_init__(self):
        for key in ('directly_relevant_neighbor_contract_hashes', 'artifact_hashes'):
            object.__setattr__(self, key, tuple(sorted(tuple(p) for p in getattr(self, key))))
        if not self.artifact_hashes or any(not getattr(self, k) for k in
                ('target_block', 'active_variant', 'input_contract_hash', 'output_contract_hash',
                 'effect_contract_hash', 'acceptance_id', 'checker_hash')):
            raise ValueError('verification key must bind complete identities')

    @property
    def fingerprint(self):
        return stable_hash(asdict(self))


def verification_disposition(key, observations):
    rows = [r for r in observations if r.get('key') == key.fingerprint and r.get('authenticated') is True]
    if any(r.get('status') == 'RUNNING' for r in rows):
        return 'REUSE_RUNNING'
    # An outstanding counterexample cannot be outvoted by a PASS.
    if any(r.get('status') == 'FAIL' for r in rows):
        return 'NO_NOVEL_DELTA'
    if any(r.get('status') == 'PASS' for r in rows):
        return 'REUSE_PASS'
    return 'EXECUTE'


def provider_disposition(previous, candidate):
    dimensions = ('variant', 'artifacts', 'contracts', 'evidence', 'checker_qualification')
    if any(k not in candidate for k in dimensions):
        return 'NO_NOVEL_DELTA'
    if not previous:
        return 'EXECUTE'
    signature = tuple(candidate[k] for k in dimensions)
    return 'NO_NOVEL_DELTA' if any(tuple(row.get(k) for k in dimensions) == signature
                                     for row in previous) else 'EXECUTE'
