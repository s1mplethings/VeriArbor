from dataclasses import dataclass, asdict
from .port import Port
from .effects import EffectContract
from .variant import Variant
from .model import stable_hash


@dataclass(frozen=True)
class Block:
    block_id: str
    capability: str
    input_ports: tuple[Port, ...]
    output_ports: tuple[Port, ...]
    effect_contract: EffectContract
    variants: tuple[Variant, ...]
    active_variant: str
    certificate_ref: str | None = None

    def __post_init__(self):
        for key in ('input_ports', 'output_ports', 'variants'):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        if not self.block_id or not self.capability:
            raise ValueError('block identity required')
        ids = [v.variant_id for v in self.variants]
        if len(ids) != len(set(ids)) or self.active_variant not in ids:
            raise ValueError('active variant must identify one implementation')
        for direction in ('input', 'output'):
            ports = getattr(self, direction + '_ports')
            if len({p.port_id for p in ports}) != len(ports) or any(p.direction != direction for p in ports):
                raise ValueError('ambiguous port boundary')

    @property
    def variant(self):
        return next(v for v in self.variants if v.variant_id == self.active_variant)

    @property
    def boundary_hashes(self):
        return (stable_hash(sorted((p.port_id, p.fingerprint) for p in self.input_ports)),
                stable_hash(sorted((p.port_id, p.fingerprint) for p in self.output_ports)),
                self.effect_contract.fingerprint)

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, raw):
        from .contract import Contract
        def ports(rows):
            return tuple(Port(**{**p, 'contract': Contract(**p['contract'])}) for p in rows)
        return cls(**{**raw, 'input_ports': ports(raw['input_ports']),
                      'output_ports': ports(raw['output_ports']),
                      'effect_contract': EffectContract(**raw['effect_contract']),
                      'variants': tuple(Variant(**v) for v in raw['variants'])})
