from dataclasses import dataclass, asdict
from .model import stable_hash


@dataclass(frozen=True)
class EffectContract:
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    external_effects: tuple[str, ...] = ()
    persistence: str = 'none'
    idempotency: str = 'none'
    concurrency: str = 'serial'
    ordering: str = 'declared'
    rollback: str = 'none'

    def __post_init__(self):
        for key in ('reads', 'writes', 'external_effects'):
            object.__setattr__(self, key, tuple(sorted(set(getattr(self, key)))))
        if any(not getattr(self, key) for key in
               ('persistence', 'idempotency', 'concurrency', 'ordering', 'rollback')):
            raise ValueError('effect guarantees must be explicit')

    @property
    def fingerprint(self):
        return stable_hash(asdict(self))
