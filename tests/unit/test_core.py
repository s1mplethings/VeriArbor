import itertools
import json
import math
import unittest
from dataclasses import replace

from veriarbor.model import Evidence, Node, NodeKind, Status, stable_hash
from veriarbor.verification import rollup, ready_frontier, verified_lineage, reduce_obligations
from veriarbor.lifecycle import CapabilityCertificate, vitality, BranchVitality, active_crown, hydrate_archive
from veriarbor.learning import LearnedNogood, DecisionCheckpoint, backtrack, minimize_conflict, strategy_fingerprint, repeated_no_progress
from veriarbor.search import Candidate, ProofCost, proof_cost, pareto, allocate
from veriarbor.scheduling import ResourceClaim, conflict_graph, parallel_batch
from veriarbor.review import review_kind, qualify_evaluator


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.evidence = Evidence('VERIFIED', {'artifact': 'v1'}, {'checker': 'c1'}, ('receipt',), True)
        self.bindings = dict(object_versions={'artifact': 'v1'}, checker_versions={'checker': 'c1'})

    def test_execution_success_cannot_verify_parent(self):
        node = Node('root', NodeKind.OBLIGATION_AND, ('leaf',))
        result = rollup(node, {'leaf': 'SUCCEEDED'}, acceptance=self.evidence,
                        handoffs={}, integration=self.evidence, **self.bindings)
        self.assertNotEqual(result.status, Status.VERIFIED)
        result = rollup(node, {'leaf': 'VERIFIED'}, acceptance=self.evidence,
                        handoffs={}, integration=None, **self.bindings)
        self.assertNotEqual(result.status, Status.VERIFIED)

    def test_stale_evidence_and_missing_handoff_fail_closed(self):
        node = Node('root', NodeKind.OBLIGATION_AND, ('leaf',))
        for evidence in (None, replace(self.evidence, qualified=False), replace(self.evidence, object_versions={'artifact': 'v0'})):
            result = rollup(node, {'leaf': 'VERIFIED'}, acceptance=self.evidence,
                            handoffs={'edge': evidence}, integration=self.evidence, **self.bindings)
            self.assertNotEqual(result.status, Status.VERIFIED)

    def test_omitted_declared_handoff_cannot_verify(self):
        node = Node('root', NodeKind.OBLIGATION_AND, ('leaf',), required_handoffs=('edge',))
        result = rollup(node, {'leaf': 'VERIFIED'}, acceptance=self.evidence, handoffs={},
                        integration=self.evidence, **self.bindings)
        self.assertNotEqual(result.status, Status.VERIFIED)
        self.assertIn('handoff:edge', result.missing_checks)

    def test_or_success_and_and_counterexample(self):
        for kind, expected in ((NodeKind.STRATEGY_OR, Status.VERIFIED), (NodeKind.OBLIGATION_AND, Status.FAILED)):
            result = rollup(Node('root', kind, ('a', 'b')), {'a': 'VERIFIED', 'b': 'FAILED'},
                            acceptance=self.evidence, handoffs={}, integration=self.evidence, **self.bindings)
            self.assertEqual(result.status, expected)

    def test_readiness_invalidated_ancestor_unknown_and_cycle(self):
        ids = ('a', 'b', 'c', 'sibling')
        deps = {'b': ('a',), 'c': ('b',)}
        statuses = {'a': 'FAILED', 'b': 'VERIFIED', 'c': 'FAILED', 'sibling': 'VERIFIED'}
        self.assertEqual(ready_frontier(ids, statuses, deps), ('a',))
        self.assertTrue(verified_lineage(ids, statuses, deps)['sibling'])
        statuses['a'] = 'VERIFIED'
        self.assertEqual(ready_frontier(ids, statuses, deps, blocked=('a',)), ())
        self.assertFalse(verified_lineage(('a', 'b'), {'a': 'VERIFIED', 'b': 'VERIFIED'}, {'a': ('b',), 'b': ('a',)})['a'])

    def test_certificate_roundtrip_and_binding(self):
        cert = CapabilityCertificate('cap', 'name', {}, {}, (), (), ('accept',), {'a': 'v1'}, {'c': 'v1'}, (), ('receipt',), ('provenance',), 10, 20, ('contract_changed',))
        restored = CapabilityCertificate(**json.loads(json.dumps(cert.as_dict())))
        self.assertEqual(cert.fingerprint, restored.fingerprint)
        args = dict(artifacts={'a': 'v1'}, checkers={'c': 'v1'}, now=15)
        self.assertTrue(restored.valid(**args))
        for delta in ({'now': 20}, {'now': 9}, {'artifacts': {'a': 'v2'}}, {'checkers': {}}, {'triggers': ('contract_changed',)}):
            self.assertFalse(restored.valid(**(args | delta)))

    def test_nogood_cannot_learn_from_invalid_evaluator(self):
        nogood = LearnedNogood('scope', ('shared', 'writer'), 'conflict', 'failure', 'family', {'object': 'v1'}, ('receipt',), 'VERIFIED_COUNTEREXAMPLE', 'QUALIFIED')
        args = dict(scope='scope', conditions=('shared', 'writer', 'other'), versions={'object': 'v1'}, strategy_family='family', now=1)
        self.assertTrue(nogood.matches(**args))
        self.assertFalse(replace(nogood, evaluator_status='INVALID_EVALUATOR').matches(**args))
        self.assertFalse(nogood.matches(**(args | {'versions': {'object': 'v2'}})))
        self.assertFalse(replace(nogood, expires_at=1).matches(**args))

    def test_conflict_minimization_backjumps_without_sibling_loss(self):
        minimal = minimize_conflict(['noise', 'shared', 'writer'], lambda xs: {'shared', 'writer'} <= set(xs))
        self.assertEqual(minimal, ('shared', 'writer'))
        checkpoints = [DecisionCheckpoint('first', 1, ('shared',), 'rollback-1', ('a',)), DecisionCheckpoint('sibling', 2, ('noise',), 'rollback-2', ('b',)), DecisionCheckpoint('last', 3, ('writer',), 'rollback-3', ('a',))]
        self.assertEqual(backtrack(minimal, checkpoints).id, 'first')
        self.assertEqual(checkpoints[1].affected_nodes, ('b',))

    def test_mechanism_hash_and_no_progress_rejection(self):
        strategy = {'problem': 'Shared FILE', 'writer': 'Atomic  commit', 'locking': True}
        fingerprint = strategy_fingerprint(strategy)
        self.assertEqual(fingerprint, strategy_fingerprint(dict(reversed(list(strategy.items())))))
        history = [{'strategy_fingerprint': fingerprint, 'failure_fingerprint': 'f', 'status': 'REPAIR_NO_PROGRESS', 'failure_evidence_hashes': ['e']}]
        self.assertTrue(repeated_no_progress(fingerprint, 'f', ['e'], history))
        self.assertFalse(repeated_no_progress(fingerprint, 'f', ['new'], history))

    def test_obligation_never_pruned(self):
        for progress, regression, verified, count in itertools.product((False, True), (False, True), (False, True), range(4)):
            self.assertNotEqual(vitality(NodeKind.OBLIGATION_AND, qualified_counterexample=True, progress=progress,
                                       regression=regression, verified=verified, no_progress_attempts=count), BranchVitality.PRUNED)
        self.assertEqual(vitality(NodeKind.STRATEGY_OR, qualified_counterexample=True), BranchVitality.PRUNED)

    def test_crown_bound_and_archive_integrity(self):
        crown = active_crown(obligations=('goal',), running=('running',), strategies=('a', 'b'), limit=3)
        self.assertEqual(len(crown.active), 3)
        self.assertEqual(crown.deferred, ('b',))
        with self.assertRaises(ValueError):
            active_crown(obligations=('a', 'b'), running=(), strategies=(), limit=1)
        class Archive:
            def read(self, ref):
                return b'history'
        self.assertEqual(hydrate_archive(Archive(), 'ref', stable_hash(b'history')), b'history')
        with self.assertRaises(ValueError):
            hydrate_archive(Archive(), 'ref', 'wrong')

    def test_proof_estimates_do_not_change_truth(self):
        values = (ProofCost(2, 4), ProofCost(3, 1))
        self.assertEqual(proof_cost('AND', values, integration_cost=2), ProofCost(7, 1))
        self.assertEqual(proof_cost('OR', values), ProofCost(2, 5))
        self.assertEqual(proof_cost('AND', (), verified=True), ProofCost(0, math.inf))
        self.assertEqual(proof_cost('OR', ()), ProofCost(math.inf, math.inf))

    def test_pareto_probe_and_unqualified_filter(self):
        best = Candidate('best', 2, 2, 1, 0, 0, 0)
        worse = Candidate('worse', 1, 1, 2, 1, 1, 1)
        unqualified = replace(best, id='invalid', qualified=False)
        self.assertEqual(pareto([worse, best]), (best,))
        self.assertEqual(allocate([worse, best, unqualified], budget=2), ({'id': 'best', 'units': 1, 'mode': 'PROBE'},))
        self.assertEqual(allocate([best], budget=2, blocked=['best']), ())

    def test_exhaustive_conflict_batches_are_independent(self):
        variants = [ResourceClaim(str(i), reads=frozenset(r), writes=frozenset(w), parallel_safe=True)
                    for i, (r, w) in enumerate(itertools.product(((), ('a',), ('b',)), repeat=2))]
        for subset in itertools.combinations(variants, 4):
            graph = conflict_graph(subset)
            for perm in (subset, tuple(reversed(subset))):
                chosen = parallel_batch(perm, slots=3)
                self.assertLessEqual(len(chosen), 3)
                self.assertTrue(all(b not in graph[a] for a, b in itertools.combinations(chosen, 2)))
                self.assertEqual(chosen, parallel_batch(subset, slots=3))

    def test_side_effect_and_contract_conflicts(self):
        for key in ('side_effects', 'contracts', 'writes'):
            a = ResourceClaim('a', parallel_safe=True, **{key: frozenset({'shared'})})
            b = replace(a, id='b')
            self.assertEqual(parallel_batch([a, b], slots=2), ('a',))

    def test_review_actual_model_and_evaluator_controls(self):
        self.assertEqual(review_kind('Model-X', ' model-x '), 'SELF_CRITIQUE')
        self.assertEqual(review_kind('UNKNOWN', 'model-x'), 'UNQUALIFIED_REVIEW')
        self.assertEqual(qualify_evaluator({'positive_control_passed': True}), 'INVALID_EVALUATOR')

    def test_reducer_empty_evidence_is_not_verified(self):
        requirements = {'root': {'must': True, 'children': ['leaf']}, 'leaf': {'must': True}}
        self.assertEqual(reduce_obligations(requirements, {})['hard_verdict'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(reduce_obligations(requirements, {'leaf': ['VERIFIED']})['hard_verdict'], 'VERIFIED')


if __name__ == '__main__':
    unittest.main()
