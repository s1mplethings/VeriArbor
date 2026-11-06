"""Semantic obligation graph validation/reduction, never an execution graph."""
from dataclasses import replace
from .model import NodeKind, Status
from .verification import rollup


def validate_graph(nodes):
    nodes = tuple(nodes)
    by_id = {node.id: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('duplicate graph identity')
    active, seen = set(), set()

    def visit(key):
        if key not in by_id:
            raise ValueError('unknown graph reference: ' + key)
        if key in active:
            raise ValueError('cyclic obligation/dependency graph')
        if key in seen:
            return
        active.add(key)
        for ref in (*by_id[key].children, *by_id[key].dependencies):
            visit(ref)
        active.remove(key)
        seen.add(key)

    for key in sorted(by_id):
        visit(key)
    return by_id


def evaluate_graph(nodes, checks, *, object_versions, checker_versions):
    """Bottom-up frozen snapshot reduction with mandatory dependency lineage.

    checks[id] contains acceptance, integration and explicit handoffs. The host
    must include every frozen contract's required check (None when unavailable).
    """
    by_id = validate_graph(nodes)
    results = {}

    def visit(key):
        if key in results:
            return results[key]
        node = by_id[key]
        for ref in (*node.children, *node.dependencies):
            visit(ref)
        required = tuple(ref for ref in node.children if by_id[ref].required)
        reduced = replace(node, children=required) if node.kind == NodeKind.OBLIGATION_AND else node
        evidence = checks.get(key, {})
        result = rollup(reduced, {ref: results[ref].status for ref in node.children},
                        acceptance=evidence.get('acceptance'), integration=evidence.get('integration'),
                        handoffs=evidence.get('handoffs', {}), object_versions=object_versions,
                        checker_versions=checker_versions)
        if result.status == Status.VERIFIED and any(results[ref].status != Status.VERIFIED for ref in node.dependencies):
            result = replace(result, status=Status.BLOCKED)
        results[key] = result
        return result

    for key in sorted(by_id):
        visit(key)
    return results
