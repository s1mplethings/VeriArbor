from dataclasses import dataclass
from enum import StrEnum
from .model import stable_hash


class VariantStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    VERIFIED = 'VERIFIED'
    STALLED = 'STALLED'
    QUARANTINED = 'QUARANTINED'
    PRUNED = 'PRUNED'
    ARCHIVED = 'ARCHIVED'


@dataclass(frozen=True)
class Variant:
    variant_id: str
    artifacts: tuple[tuple[str, str], ...]
    status: VariantStatus = VariantStatus.ACTIVE

    def __post_init__(self):
        pairs = tuple(sorted(tuple(p) for p in self.artifacts))
        if not self.variant_id or not pairs or len(dict(pairs)) != len(pairs) or any(not k or not v for k, v in pairs):
            raise ValueError('variant requires unique content-bound artifacts')
        object.__setattr__(self, 'artifacts', pairs)
        object.__setattr__(self, 'status', VariantStatus(self.status))

    @property
    def fingerprint(self):
        return stable_hash({'variant_id': self.variant_id, 'artifacts': self.artifacts})
