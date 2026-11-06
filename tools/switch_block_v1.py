"""One responsibility per rollback receipt; preserves evidence authentication."""
from migrate_next import edit


def local_impact(source):
    old = "        from cgkn.orchestration.invalidation import downstream_closure\n        affected = set(downstream_closure(dag, set(changed_nodes)))"
    new = "        from cgkn.adapters.veriarbor.block_adapter import local_scope\n        affected, bubbles = local_scope(dag, changed_nodes)\n        affected = set(affected)"
    assert old in source
    return source.replace(old, new, 1).replace(
        "'authority': 'impact evidence only; no automatic execution'",
        "'authority': 'one-hop impact inspection only; no automatic execution or certificate reuse',\n                'boundary_recheck_required': sorted(changed_nodes)", 1)


def simple_slots(source):
    return '''"""Deterministic admission order; experimental bandit/Pareto is opt-in only.

The runtime already owns capacity/budget admission. This adapter neither
escalates models nor allocates a second resource budget.
"""
def allocate_slots(configs):
    return [{'id': key, 'allocated': 1} for key in sorted(configs)]
'''


if __name__ == '__main__':
    edit('cgkn/state/acceptance.py', local_impact,
         'V1 progressive local impact replaces eager transitive revalidation advice; original authentication unchanged')
    edit('cgkn/adapters/veriarbor/allocation_adapter.py', simple_slots,
         'Remove experimental Pareto/bandit from default slot selection; deterministic bounded runtime admission')
