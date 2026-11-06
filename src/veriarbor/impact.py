"""Change-impact planning over Block/Port boundaries.

This module composes the existing boundary comparison, one-hop expansion and
verification-key reuse policies.  It does not execute checks, authenticate
evidence or persist anything; the host retains those authorities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .adapter import Adapter
from .block import Block
from .compatibility import (PortCompatibility as C, compare_blocks,
                            compare_effects, compare_ports)
from .contract import schema_subset
from .dedup import VerificationKey, verification_disposition
from .expansion import next_hop, progressive_boundary_expansion
from .port import Port


@dataclass(frozen=True)
class ImpactedNode:
    node_id: str
    relation: str
    checks: tuple[str, ...]
    adapter_ids: tuple[str, ...] = ()
    reason: str = ""
    reuse: str = "EXECUTE"
    unresolved_ports: tuple[str, ...] = ()

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
    unresolved: tuple[str, ...] = ()
    unmapped_inputs: tuple[str, ...] = ()
    unmapped_consumers: tuple[str, ...] = ()
    consumer_reuse_allowed: bool = False
    reuse_gate: str = "BLOCKED_UNPROVEN_UPSTREAM"
    consumer_reuse_proofs: tuple[tuple[str, str], ...] = ()

    def retest(self):
        """Nodes with no reusable/current evidence disposition."""
        return tuple(node for node, value in self.reuse
                     if value in {"EXECUTE", "UNVERIFIED"})

    def as_dict(self):
        return asdict(self)


def _checks(relation: C, node_id: str):
    # Reuse the existing one-hop policy mapping instead of duplicating it.
    return progressive_boundary_expansion(node_id, (), relation).verification


def _reuse(node_id, keys, observations, fallback, *, authenticated_keys, stale_key=None):
    key = keys.get(node_id)
    if key is None:
        return fallback
    # The host must explicitly authenticate the exact key identity.  An
    # observation flag alone is not enough to authorize skipping a test.
    if authenticated_keys.get(node_id) != key.fingerprint:
        return fallback
    # An affected node's key must change.  Reusing a stale key would let old
    # evidence cover a boundary/artifact delta, so fail closed instead.
    if stale_key is not None and stale_key.fingerprint == key.fingerprint:
        return "EXECUTE"
    return verification_disposition(key, observations.get(node_id, ()))


def _supply_relation(producer_port: Port, consumer_port: Port):
    """Directional producer-output -> consumer-input compatibility."""
    if producer_port.direction != "output" or consumer_port.direction != "input":
        return C.BREAKING
    if producer_port.contract.semantic != consumer_port.contract.semantic:
        return C.BREAKING
    if producer_port.contract.schema == consumer_port.contract.schema:
        return C.IDENTICAL
    if schema_subset(producer_port.contract.schema, consumer_port.contract.schema):
        return C.COMPATIBLE
    return C.BREAKING


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
    authenticated_keys: dict[str, str] | None = None,
    input_producers: dict[str, str] | None = None,
    producer_ports: dict[str, dict[str, Port]] | None = None,
    unmapped_consumers: tuple[str, ...] | list[str] | None = None,
    consumer_reuse_proofs: dict[str, str] | None = None,
    external_context_unchanged: bool = False,
    expand_breaking: bool = True,
) -> ImpactPlan:
    """Compute the affected nodes, required checks and evidence reuse.

    ``consumers`` maps a consumer node to the output-port IDs it reads from the
    changed block.  ``adapters`` maps a consumer to explicit adapters.  A
    consumer is unaffected only when every consumed port is IDENTICAL.
    ``input_producers`` maps a changed input-port ID to its upstream producer;
    ``producer_ports`` maps that producer to its output-port IDs.  Only
    incompatible upstream supplies are marked affected; a compatible supply is
    reused when the host authenticates its key.

    ``old_keys`` is used for unaffected consumers; ``new_keys`` is used for the
    changed block and affected consumers.  ``authenticated_keys`` maps a node to
    the exact key fingerprint the host has authenticated; without it no key is
    eligible for reuse.  Missing/stale keys never imply reuse.

    Consumer reuse on an IDENTICAL boundary additionally requires the changed
    block to have a current authenticated PASS key,
    ``external_context_unchanged=True`` and a per-consumer
    ``consumer_reuse_proofs`` reference covering that consumer's relevant
    behavior.  Structural port identity or the changed block's own PASS never
    authorizes skipping downstream business acceptance.  ``unmapped_consumers``
    keeps missing port-level edges in the retest scope.

    Only direct BREAKING consumers expand one hop through ``adjacency``; the
    expansion never recurses.  The returned ``expanded`` set is the next
    frontier if the caller wants another explicit round.
    """
    if old_block.block_id != changed or new_block.block_id != changed:
        raise ValueError("changed block identity mismatch")

    consumers = dict(consumers or {})
    adapters = {key: tuple(value) for key, value in (adapters or {}).items()}
    adjacency = {key: tuple(value) for key, value in (adjacency or {}).items()}
    observations = observations or {}
    old_keys = old_keys or {}
    new_keys = new_keys or {}
    authenticated_keys = authenticated_keys or {}
    input_producers = input_producers or {}
    producer_ports = producer_ports or {}
    unmapped_consumers = tuple(sorted(set(unmapped_consumers or ())))
    consumer_reuse_proofs = {str(key): str(value).strip()
                             for key, value in (consumer_reuse_proofs or {}).items()
                             if str(value).strip()}

    block_relation = compare_blocks(old_block, new_block)
    block_level_break = (compare_effects(old_block.effect_contract,
                                         new_block.effect_contract) == C.BREAKING
                         or old_block.capability != new_block.capability)
    changed_reuse = _reuse(
        changed, new_keys, observations, "EXECUTE",
        authenticated_keys=authenticated_keys,
        stale_key=old_keys.get(changed) if old_block != new_block else None,
    )
    changed_is_current = changed_reuse == "REUSE_PASS"
    if old_block == new_block:
        base_consumer_reuse_allowed = True
        reuse_gate = "NO_BOUNDARY_CHANGE"
    elif changed_is_current and external_context_unchanged and not unmapped_consumers:
        base_consumer_reuse_allowed = True
        reuse_gate = "CURRENT_CHANGED_KEY_AND_CONTEXT"
    else:
        base_consumer_reuse_allowed = False
        reuse_gate = ("BLOCKED_UNMAPPED_CONSUMERS" if unmapped_consumers
                      else "BLOCKED_UNPROVEN_UPSTREAM")
    impacted = [ImpactedNode(changed, block_relation.value,
                             _checks(block_relation, changed), (),
                             "changed block artifact/boundary", changed_reuse)]
    reuse = {changed: changed_reuse}
    for node_id in unmapped_consumers:
        reuse.setdefault(node_id, "EXECUTE")
    unaffected: list[str] = []
    breaking: list[str] = []
    unmapped_inputs: list[str] = []
    proof_required = set(consumers)

    old_ports = {port.port_id: port for port in old_block.output_ports}
    new_ports = {port.port_id: port for port in new_block.output_ports}

    for consumer in sorted(consumers):
        worst = C.IDENTICAL
        changed_ports: list[str] = []
        unresolved_ports: list[str] = []
        used_adapters: list[str] = []
        for port_id in consumers[consumer]:
            old_port = old_ports.get(port_id)
            new_port = new_ports.get(port_id)
            if old_port is None or new_port is None:
                worst = C.BREAKING
                changed_ports.append(port_id)
                unresolved_ports.append(port_id)
                continue
            adapter = next((item for item in adapters.get(consumer, ())
                            if item.connects(old_port, new_port)), None)
            relation = compare_ports(old_port, new_port, adapter)
            if relation == C.IDENTICAL:
                continue
            changed_ports.append(port_id)
            if adapter is not None:
                used_adapters.append(adapter.adapter_id)
            if relation == C.BREAKING:
                unresolved_ports.append(port_id)
            if list(C).index(relation) > list(C).index(worst):
                worst = relation

        if not changed_ports and block_level_break:
            worst = C.BREAKING
            changed_ports.append("<effect>")
        if not changed_ports:
            unaffected.append(consumer)
            if base_consumer_reuse_allowed and consumer_reuse_proofs.get(consumer):
                reuse[consumer] = _reuse(
                    consumer, old_keys, observations, "UNVERIFIED",
                    authenticated_keys=authenticated_keys,
                )
            else:
                reuse[consumer] = "EXECUTE"
            continue

        node_reuse = _reuse(consumer, new_keys, observations, "EXECUTE",
                            authenticated_keys=authenticated_keys,
                            stale_key=old_keys.get(consumer))
        if (not (base_consumer_reuse_allowed and consumer_reuse_proofs.get(consumer))
                and node_reuse in {"REUSE_PASS", "REUSE_RUNNING"}):
            node_reuse = "EXECUTE"
        node = ImpactedNode(
            consumer, worst.value, _checks(worst, consumer),
            tuple(sorted(set(used_adapters))),
            "dependency output changed: " + ",".join(sorted(set(changed_ports))),
            node_reuse,
            tuple(sorted(set(unresolved_ports))),
        )
        impacted.append(node)
        reuse[consumer] = node.reuse
        if worst == C.BREAKING:
            breaking.append(consumer)

    old_inputs = {port.port_id: port for port in old_block.input_ports}
    new_inputs = {port.port_id: port for port in new_block.input_ports}
    for port_id in sorted(set(old_inputs) | set(new_inputs)):
        old_port = old_inputs.get(port_id)
        new_port = new_inputs.get(port_id)
        relation = (C.BREAKING if old_port is None or new_port is None
                    else compare_ports(old_port, new_port))
        if relation == C.IDENTICAL or new_port is None:
            continue
        producer = input_producers.get(port_id)
        producer_port = producer_ports.get(producer, {}).get(port_id) if producer else None
        if producer is None or producer_port is None:
            unmapped_inputs.append(port_id)
            continue
        proof_required.add(producer)
        supply = _supply_relation(producer_port, new_port)
        if supply in (C.IDENTICAL, C.COMPATIBLE):
            if producer not in reuse:
                unaffected.append(producer)
                if base_consumer_reuse_allowed and consumer_reuse_proofs.get(producer):
                    reuse[producer] = _reuse(
                        producer, old_keys, observations, "UNVERIFIED",
                        authenticated_keys=authenticated_keys,
                    )
                else:
                    reuse[producer] = "EXECUTE"
            continue
        if producer in reuse:
            continue
        node_reuse = _reuse(producer, new_keys, observations, "EXECUTE",
                            authenticated_keys=authenticated_keys,
                            stale_key=old_keys.get(producer))
        if (not (base_consumer_reuse_allowed and consumer_reuse_proofs.get(producer))
                and node_reuse in {"REUSE_PASS", "REUSE_RUNNING"}):
            node_reuse = "EXECUTE"
        node = ImpactedNode(
            producer, supply.value, _checks(supply, producer), (),
            "upstream supply incompatible for input " + port_id,
            node_reuse,
            (port_id,),
        )
        impacted.append(node)
        reuse[producer] = node.reuse

    expanded: list[str] = []
    if expand_breaking and breaking:
        bubble = progressive_boundary_expansion(changed, breaking, C.BREAKING)
        next_nodes = next_hop(bubble, {item: C.BREAKING for item in breaking}, adjacency)
        for node_id in next_nodes:
            if node_id in reuse:
                continue
            proof_required.add(node_id)
            node_reuse = _reuse(node_id, new_keys, observations, "EXECUTE",
                                authenticated_keys=authenticated_keys,
                                stale_key=old_keys.get(node_id))
            if (not (base_consumer_reuse_allowed and consumer_reuse_proofs.get(node_id))
                    and node_reuse in {"REUSE_PASS", "REUSE_RUNNING"}):
                node_reuse = "EXECUTE"
            node = ImpactedNode(
                node_id, C.BREAKING.value, _checks(C.BREAKING, node_id), (),
                "one-hop expansion from breaking boundary",
                node_reuse,
            )
            impacted.append(node)
            reuse[node_id] = node.reuse
            expanded.append(node_id)

    missing_proofs = tuple(sorted(node for node in proof_required
                                  if not consumer_reuse_proofs.get(node)))
    consumer_reuse_allowed = base_consumer_reuse_allowed and not missing_proofs
    if base_consumer_reuse_allowed:
        reuse_gate = ("CONSUMER_SCOPE_PROVEN" if not missing_proofs
                      else "BLOCKED_CONSUMER_SCOPE_UNPROVEN")
    required_adapters = tuple(sorted({adapter_id for node in impacted
                                      for adapter_id in node.adapter_ids}))
    unresolved = tuple(sorted(f"{node.node_id}:{port_id}" for node in impacted
                              for port_id in node.unresolved_ports))
    return ImpactPlan(
        changed=changed,
        block_relation=block_relation.value,
        impacted=tuple(impacted),
        unaffected=tuple(sorted(unaffected)),
        required_adapters=required_adapters,
        expanded=tuple(sorted(expanded)),
        breaking=tuple(sorted(breaking)),
        reuse=tuple(sorted(reuse.items())),
        unresolved=unresolved,
        unmapped_inputs=tuple(sorted(unmapped_inputs)),
        unmapped_consumers=unmapped_consumers,
        consumer_reuse_allowed=consumer_reuse_allowed,
        reuse_gate=reuse_gate,
        consumer_reuse_proofs=tuple(sorted(consumer_reuse_proofs.items())),
    )
