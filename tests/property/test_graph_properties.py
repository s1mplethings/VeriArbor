import itertools
import unittest
from veriarbor.graph import evaluate_graph, validate_graph
from veriarbor.model import Node, NodeKind, Evidence


class GraphProperties(unittest.TestCase):
    def test_exhaustive_and_or_replay_and_missing_evidence(self):
        good = Evidence('VERIFIED', {'a': '1'}, {'c': '1'}, ('r',), True)
        bad = Evidence('FAILED', {'a': '1'}, {'c': '1'}, ('r',), True)
        for kind, states in itertools.product((NodeKind.OBLIGATION_AND, NodeKind.STRATEGY_OR), itertools.product((None, good, bad), repeat=3)):
            nodes = [Node('root', kind, ('a', 'b', 'c'))] + [Node(key, NodeKind.EXECUTION_LEAF) for key in 'abc']
            checks = {key: {'acceptance': evidence} for key, evidence in zip('abc', states)}
            checks['root'] = {'acceptance': good, 'integration': good}
            kwargs = dict(object_versions={'a': '1'}, checker_versions={'c': '1'})
            result = evaluate_graph(nodes, checks, **kwargs)
            self.assertEqual(result, evaluate_graph(reversed(nodes), checks, **kwargs))
            expected = all(e is good for e in states) if kind == NodeKind.OBLIGATION_AND else any(e is good for e in states)
            self.assertEqual(result['root'].status == 'VERIFIED', expected)
            self.assertFalse(any(r.status == 'VERIFIED' for r in evaluate_graph(nodes, checks, object_versions={'a': '2'}, checker_versions={'c': '1'}).values()))

    def test_cycles_unknowns_duplicate_ids_rejected(self):
        for nodes in ([Node('a', NodeKind.OBLIGATION_AND, ('b',))],
                      [Node('a', NodeKind.OBLIGATION_AND, ('b',)), Node('b', NodeKind.OBLIGATION_AND, ('a',))],
                      [Node('a', NodeKind.EXECUTION_LEAF), Node('a', NodeKind.EXECUTION_LEAF)]):
            with self.assertRaises(ValueError):
                validate_graph(nodes)

    def test_optional_child_does_not_block_required_obligation(self):
        good = Evidence('VERIFIED', {'a': '1'}, {'c': '1'}, ('r',), True)
        nodes = [Node('root', NodeKind.OBLIGATION_AND, ('required', 'optional')),
                 Node('required', NodeKind.EXECUTION_LEAF), Node('optional', NodeKind.EXECUTION_LEAF, required=False)]
        checks = {'root': {'acceptance': good, 'integration': good}, 'required': {'acceptance': good}}
        self.assertEqual(evaluate_graph(nodes, checks, object_versions={'a': '1'}, checker_versions={'c': '1'})['root'].status, 'VERIFIED')
