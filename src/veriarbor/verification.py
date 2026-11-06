"""Evidence-qualified AND/OR reduction and dependency readiness."""
from dataclasses import dataclass
from .model import NodeKind, Status


@dataclass(frozen=True)
class VerificationRollup:
    node_id: str
    status: Status
    missing_checks: tuple[str, ...] = ()


def rollup(node, child_statuses, *, acceptance, handoffs, integration,
           object_versions, checker_versions):
    """Empty/missing acceptance never implies success, including leaf nodes.

    Handoff IDs must be explicitly supplied by the frozen host contract; an
    empty mapping means that contract declares none. Integration is mandatory
    for every composite. All children of an obligation are required.
    """
    checks = {'acceptance': acceptance, **{'handoff:' + k: v for k, v in handoffs.items()}}
    for key in node.required_handoffs:
        checks.setdefault('handoff:' + key, None)
    if node.kind in {NodeKind.OBLIGATION_AND, NodeKind.STRATEGY_OR}:
        checks['integration'] = integration
    missing = tuple(sorted(k for k, e in checks.items()
                           if e is None or not e.current(object_versions, checker_versions)
                           or e.verdict != 'VERIFIED'))
    failure = any(e is not None and e.current(object_versions, checker_versions)
                  and e.verdict == 'FAILED' for e in checks.values())
    values = [child_statuses.get(k, Status.UNPROVEN) for k in node.children]
    if node.kind == NodeKind.STRATEGY_OR:
        child_ok = bool(values) and Status.VERIFIED in values
        child_failed = bool(values) and all(v == Status.FAILED for v in values)
    else:
        child_ok = all(v == Status.VERIFIED for v in values)
        child_failed = Status.FAILED in values
    status = Status.FAILED if failure or child_failed else Status.VERIFIED if child_ok and not missing else Status.UNPROVEN
    return VerificationRollup(node.id, status, missing)


def verified_lineage(ids, statuses, dependencies, blocked=()):
    ids = tuple(ids)
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate node identity')
    known, blocked, memo = set(ids), set(blocked), {}

    def visit(key, active):
        if key in active or key not in known or key in blocked or statuses.get(key) != 'VERIFIED':
            return False
        if key not in memo:
            memo[key] = all(visit(dep, active | {key}) for dep in dependencies.get(key, ()))
        return memo[key]

    return {key: visit(key, set()) for key in ids}


def ready_frontier(ids, statuses, dependencies, blocked=()):
    ids, blocked = tuple(ids), set(blocked)
    lineage = verified_lineage(ids, statuses, dependencies, blocked)
    return tuple(key for key in ids if statuses.get(key) != 'VERIFIED' and key not in blocked
                 and all(lineage.get(dep, False) for dep in dependencies.get(key, ())))


def reduce_obligations(requirements, observations):
    """Compatibility reducer extracted from GoalAcceptance's pure rollup.

    Observations MUST already be authenticated/version-bound by the host.
    This compatibility API does not replace hierarchical integration checks.
    """
    obligations, visiting = {}, set()

    def verdict(ref):
        if ref in obligations:
            return obligations[ref]['verdict']
        if ref in visiting or ref not in requirements:
            raise ValueError('invalid requirement tree')
        visiting.add(ref)
        req = requirements[ref]
        children = [verdict(child) for child in req.get('children', [])]
        if req.get('operator', 'AND') == 'OR' and children:
            children = ['VERIFIED' if 'VERIFIED' in children else 'FAILED' if all(v == 'FAILED' for v in children) else 'INSUFFICIENT_EVIDENCE']
        values = list(observations.get(ref, ())) + children
        result = 'FAILED' if 'FAILED' in values else 'VERIFIED' if values and all(v == 'VERIFIED' for v in values) else 'INSUFFICIENT_EVIDENCE'
        obligations[ref] = {'verdict': result, 'weight': req.get('weight', 1), 'must': req['must']}
        visiting.remove(ref)
        return result

    for ref in requirements:
        verdict(ref)
    total = sum(r['weight'] for r in obligations.values())
    hard = [r['verdict'] for r in obligations.values() if r['must']]
    return {'obligations': obligations,
            'completion': sum(r['weight'] for r in obligations.values() if r['verdict'] == 'VERIFIED') / total if total else None,
            'evidence_coverage': sum(r['weight'] for r in obligations.values() if r['verdict'] in {'VERIFIED', 'FAILED'}) / total if total else None,
            'hard_verdict': 'FAILED' if 'FAILED' in hard else 'VERIFIED' if hard and all(v == 'VERIFIED' for v in hard) else 'INSUFFICIENT_EVIDENCE'}
