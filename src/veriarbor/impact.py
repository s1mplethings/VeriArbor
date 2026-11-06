"""Change-impact planning over Block/Port boundaries.

This module composes the existing boundary comparison, one-hop expansion and
verification-key reuse policies.  It does not execute checks, authenticate
evidence or persist anything; the host retains those authorities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .adapter import Adapter
from .block import Block
from .compatibility import PortCompatibility as C, compare_blocks, compare_ports
from .dedup import VerificationKey, verification_disposition
from .expansion import next_hop, progressive_boundary_expansion


@dataclass(frozen=True)
class ImpactedNode:
    node_id: str
    relation: str
    checks: tuple[str, ...]
    adapter_ids: tuple[str, ...] = ()
    reason: str = ""
    reuse: str = "EXECUTE"

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ImpactPlan:
    changed: str
    block_relation: str
    impacted: tuple[ImpactedNode, ...]
    unaffected: tuple[str, ...]
    required_adapters: tuple[str, ...]
    expanded: tuple[str, ...]
    breaking: tuple[str, ...]
    reuse: tuple[tuple[str, str], ...]

    def retest(self):
        """Nodes with no reusable/current evidence disposition."""
        return tuple(node.node_id for node in self.impacted if node.reuse == "EXECUTE")

    def as_dict(self):
        return asdict(self)


def _checks(relation: C, node_id: str):
    # Reuse the existing one-hop policy mapping instead of duplicating it.
    return progressive_boundary_expansion(node_id, (), relation).verification


def _reuse(node_id, keys, observations, fallback, *, stale_key=None):
    key = keys.get(node_id)
    if key is None:
        return fallback
    # An affected node's key must change.  Reusing a stale key would let old
    # evidence cover a boundary/artifact delta, so fail closed instead.
    if stale_key is not None and stale_key.fingerprint == key.fingerprint:
        return "EXECUTE"
    return verification_disposition(key, observations.get(node_id, ()))


def plan_impact(
    changed: str,
    old_block: Block,
    new_block: Block,
    *,
    consumers: dict[str, tuple[str, ...]] | None = None,
    adapters: dict[str, tuple[Adapter, ...]] | None = None,
    adjacency: dict[str, tuple[str, ...]] | None = None,
    observations: dict[str, list[dict]] | None = None,
    old_keys: dict[str, VerificationKey] | None = None,
    new_keys: dict[str, VerificationKey] | None = None,
    expand_breaking: bool = True,
) -> ImpactPlan:
    """Compute the affected nodes, required checks and evidence reuse.

    ``consumers`` maps a consumer node to the output-port IDs it reads from the
    changed block.  ``adapters`` maps a consumer to explicit adapters.  A
    consumer is unaffected only when every consumed port is IDENTICAL.
    ``old_keys`` is used for unaffected consumers; ``new_keys`` is used for the
    changed block and affected consumers.  Missing keys never imply reuse.
    Input-side changes are covered by the changed block's own comparison; this
    planner models downstream consumers of the changed output boundary.

    Only direct BREAKING consumers expand one hop through ``adjacency``; the
    expansion never recurses.  Unauthenticated or mismatched observations are
    handled by the existing ``verification_disposition`` policy.
    """
    if old_block.block_id != changed or new_block.block_id != changed:
        raise ValueError("changed block identity mismatch")

    consumers = dict(consumers or {})
    adapters = {key: tuple(value) for key, value in (adapters or {}).items()}
    adjacency = {key: tuple(value) for key, value in (adjacency or {}).items()}
    observations = observations or {}
    old_keys = old_keys or {}
    new_keys = new_keys or {}

    block_relation = compare_blocks(old_block, new_block)
    changed_reuse = _reuse(
        changed, new_keys, observations, "EXECUTE",
        stale_key=old_keys.get(changed) if old_block != new_block else None,
    )
    impacted = [ImpactedNode(changed, block_relation.value,
                             _checks(block_relation, changed), (),
                             "changed block artifact/boundary", changed_reuse)]
    reuse = {changed: changed_reuse}
    unaffected: list[str] = []
    breaking: list[str] = []

    old_ports = {port.port_id: port for port in old_block.output_ports}
    new_ports = {port.port_id: port for port in new_block.output_ports}

    for consumer in sorted(consumers):
        worst = C.IDENTICAL
        changed_ports: list[str] = []
        used_adapters: list[str] = []
        for port_id in consumers[consumer]:
            old_port = old_ports.get(port_id)
            new_port = new_ports.get(port_id)
            if old_port is None or new_port is None:
                worst = C.BREAKING
                changed_ports.append(port_id)
                continue
            adapter = next((item for item in adapters.get(consumer, ())
                            if item.connects(old_port, new_port)), None)
            relation = compare_ports(old_port, new_port, adapter)
            if relation == C.IDENTICAL:
                continue
            changed_ports.append(port_id)
            if adapter is not None:
                used_adapters.append(adapter.adapter_id)
            if list(C).index(relation) > list(C).index(worst):
                worst = relation

        if not changed_ports:
            unaffected.append(consumer)
            reuse[consumer] = _reuse(consumer, old_keys, observations, "UNVERIFIED")
            continue

        node = ImpactedNode(
            consumer, worst.value, _checks(worst, consumer),
            tuple(sorted(set(used_adapters))),
            "dependency output changed: " + ",".join(sorted(set(changed_ports))),
            _reuse(consumer, new_keys, observations, "EXECUTE",
                   stale_key=old_keys.get(consumer)),
        )
        impacted.append(node)
        reuse[consumer] = node.reuse
        if worst == C.BREAKING:
            breaking.append(consumer)

    expanded: list[str] = []
    if expand_breaking and breaking:
        bubble = progressive_boundary_expansion(changed, breaking, C.BREAKING)
        next_nodes = next_hop(bubble, {item: C.BREAKING for item in breaking}, adjacency)
        for node_id in next_nodes:
            if node_id in reuse:
                continue
            node = ImpactedNode(
                node_id, C.BREAKING.value, _checks(C.BREAKING, node_id), (),
                "one-hop expansion from breaking boundary",
                _reuse(node_id, new_keys, observations, "EXECUTE",
                       stale_key=old_keys.get(node_id)),
            )
            impacted.append(node)
            reuse[node_id] = node.reuse
            expanded.append(node_id)

    required_adapters = tuple(sorted({adapter_id for node in impacted
                                      for adapter_id in node.adapter_ids}))
    return ImpactPlan(
        changed=changed,
        block_relation=block_relation.value,
        impacted=tuple(impacted),
        unaffected=tuple(sorted(unaffected)),
        required_adapters=required_adapters,
        expanded=tuple(sorted(expanded)),
        breaking=tuple(sorted(breaking)),
        reuse=tuple(sorted(reuse.items())),
    )
