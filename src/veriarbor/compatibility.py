"""Directional substitution, never inferred from a module filename/hash."""
from enum import StrEnum
from .contract import schema_subset


class PortCompatibility(StrEnum):
    IDENTICAL = 'IDENTICAL'
    COMPATIBLE = 'COMPATIBLE'
    ADAPTABLE = 'ADAPTABLE'
    BREAKING = 'BREAKING'


def compare_ports(old_port, new_port, adapter=None):
    C = PortCompatibility
    if old_port == new_port:
        return C.IDENTICAL
    if (old_port.port_id == new_port.port_id and old_port.direction == new_port.direction
            and old_port.contract.semantic == new_port.contract.semantic
            and old_port.compatibility_policy == new_port.compatibility_policy == 'structural-v1'
            and old_port.default_json == new_port.default_json
            and old_port.evidence_policy == new_port.evidence_policy
            and (old_port.required == new_port.required or
                 (old_port.direction == 'input' and old_port.required and not new_port.required) or
                 (old_port.direction == 'output' and not old_port.required and new_port.required))):
        left, right = old_port.contract.schema, new_port.contract.schema
        if old_port.direction == 'output':
            left, right = right, left
        if schema_subset(left, right):
            return C.COMPATIBLE
    if adapter is not None and adapter.connects(old_port, new_port):
        return C.ADAPTABLE
    return C.BREAKING


def compare_effects(old_effect, new_effect):
    # No automatic semantic implication between persistence/ordering labels.
    return PortCompatibility.IDENTICAL if old_effect == new_effect else PortCompatibility.BREAKING


def compare_blocks(old, new, adapters=()):
    C = PortCompatibility
    if old.block_id != new.block_id or old.capability != new.capability:
        return C.BREAKING
    results = [compare_effects(old.effect_contract, new.effect_contract)]
    for direction in ('input_ports', 'output_ports'):
        before = {p.port_id: p for p in getattr(old, direction)}
        after = {p.port_id: p for p in getattr(new, direction)}
        if before.keys() != after.keys():
            return C.BREAKING
        for key, port in before.items():
            adapter = next((a for a in adapters if a.connects(port, after[key])), None)
            results.append(compare_ports(port, after[key], adapter))
    return max(results, key=lambda c: list(C).index(c))
