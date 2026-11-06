"""Host-authenticated local certificates, never an independent evidence store."""
from dataclasses import dataclass, asdict
from .model import stable_hash


@dataclass(frozen=True)
class Certificate:
    block_id: str
    variant_id: str
    input_contract_hash: str
    output_contract_hash: str
    effect_contract_hash: str
    acceptance_ids: tuple[str, ...]
    artifact_hashes: tuple[tuple[str, str], ...]
    checker_hashes: tuple[tuple[str, str], ...]
    known_limits: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    created_at: str
    invalidated: bool = False

    def __post_init__(self):
        for key in ('acceptance_ids', 'known_limits', 'evidence_refs'):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        for key in ('artifact_hashes', 'checker_hashes'):
            object.__setattr__(self, key, tuple(sorted(tuple(p) for p in getattr(self, key))))
        if (not self.block_id or not self.variant_id or not self.acceptance_ids or
                not self.artifact_hashes or not self.checker_hashes or not self.evidence_refs or
                not self.created_at):
            raise ValueError('incomplete certificate')

    @property
    def fingerprint(self):
        return stable_hash(asdict(self))

    def matches(self, block, checkers, *, evidence_authenticated):
        return (evidence_authenticated is True and not self.invalidated
                and self.block_id == block.block_id and self.variant_id == block.active_variant
                and (self.input_contract_hash, self.output_contract_hash, self.effect_contract_hash) == block.boundary_hashes
                and self.artifact_hashes == block.variant.artifacts
                and all(checkers.get(k) == v for k, v in self.checker_hashes))


def can_substitute(old_certificate, candidate, *, replacement_certificate,
                   checkers, evidence_authenticated):
    """IDENTICAL boundary shortcut only after independently certified new bytes.

    Other boundary changes require edge/adapter evidence via expansion policy.
    Old historical evidence stays at its original artifact identity.
    """
    return (not old_certificate.invalidated
            and old_certificate.block_id == candidate.block_id
            and set(old_certificate.acceptance_ids) <= set(replacement_certificate.acceptance_ids)
            and (old_certificate.input_contract_hash, old_certificate.output_contract_hash,
                 old_certificate.effect_contract_hash) == candidate.boundary_hashes
            and replacement_certificate.matches(candidate, checkers,
                                                 evidence_authenticated=evidence_authenticated))
