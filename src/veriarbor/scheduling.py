"""Pure resource conflict graph and deterministic weighted greedy selection."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ResourceClaim:
    id: str
    reads: frozenset[str] = frozenset()
    writes: frozenset[str] = frozenset()
    side_effects: frozenset[str] = frozenset()
    contracts: frozenset[str] = frozenset()
    parallel_safe: bool = False
    weight: float = 1.0
    resource_class: str = 'default'

    def __post_init__(self):
        if not self.id or not isfinite(self.weight):
            raise ValueError('invalid resource identity/weight')
        for name in ('reads', 'writes', 'side_effects', 'contracts'):
            object.__setattr__(self, name, frozenset(getattr(self, name)))


def conflicts(a, b):
    return (not a.parallel_safe or not b.parallel_safe
            or bool(a.writes & (b.reads | b.writes))
            or bool(b.writes & a.reads)
            or bool(a.side_effects & b.side_effects)
            or bool(a.contracts & b.contracts))


def conflict_graph(claims):
    claims = tuple(claims)
    if len({c.id for c in claims}) != len(claims):
        raise ValueError('duplicate claim identity')
    return {c.id: tuple(sorted(d.id for d in claims if c.id != d.id and conflicts(c, d))) for c in claims}


def parallel_batch(claims, *, slots, running=(), class_limits=None):
    if type(slots) is not int or slots < 0:
        raise ValueError('invalid slots')
    claims, running = tuple(claims), tuple(running)
    conflict_graph(claims + running)
    selected, counts = [], {}
    for c in running:
        counts[c.resource_class] = counts.get(c.resource_class, 0) + 1
    for c in sorted(claims, key=lambda c: (-c.weight, c.id)):
        if len(selected) + len(running) >= slots:
            break
        limit = (class_limits or {}).get(c.resource_class, slots)
        if counts.get(c.resource_class, 0) >= limit or any(conflicts(c, d) for d in (*running, *selected)):
            continue
        selected.append(c)
        counts[c.resource_class] = counts.get(c.resource_class, 0) + 1
    return tuple(c.id for c in selected)
