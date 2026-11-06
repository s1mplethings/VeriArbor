"""One-hop repair scope; the host owns execution, evidence and persistence."""
from dataclasses import dataclass
from .compatibility import PortCompatibility as C


@dataclass(frozen=True)
class RepairBubble:
    changed_blocks: tuple[str, ...]
    direct_neighbors: tuple[str, ...]
    required_adapters: tuple[str, ...]
    verification: tuple[str, ...]
    expand: bool


def progressive_boundary_expansion(changed, neighbors, compatibility, *, adapters=()):
    relation = C(compatibility)
    checks = {C.IDENTICAL: ('block',), C.COMPATIBLE: ('block', 'edge'),
              C.ADAPTABLE: ('block', 'adapter', 'left_edge', 'right_edge', 'local_composition'),
              C.BREAKING: ('block', 'edge', 'local_composition')}[relation]
    return RepairBubble((changed,), tuple(sorted(set(neighbors))) if relation != C.IDENTICAL else (),
                        tuple(sorted(set(adapters))), checks, relation == C.BREAKING)


def next_hop(bubble, boundary_results, adjacency):
    """Only explicitly still-breaking frontier nodes may expand, once per call."""
    frontier = set(bubble.direct_neighbors)
    if not set(boundary_results) <= frontier:
        raise ValueError('boundary result outside current bubble')
    broken = {n for n, result in boundary_results.items() if C(result) == C.BREAKING}
    seen = set(bubble.changed_blocks) | frontier
    return tuple(sorted({m for n in broken for m in adjacency.get(n, ())} - seen))
