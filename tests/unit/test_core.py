import itertools
import json
import math
import unittest
from dataclasses import replace

from veriarbor.model import Evidence, Node, NodeKind, Status, stable_hash
from veriarbor.verification import rollup, ready_frontier, verified_lineage, reduce_obligations
from veriarbor.lifecycle import CapabilityCertificate, vitality, BranchVitality, active_crown, hydrate_archive
from veriarbor.learning import (LearnedNogood, DecisionCheckpoint, backtrack, minimize_conflict,
    strategy_fingerprint, repeated_no_progress, ProgressGuidedBacktracking, repair_progress)
from veriarbor.capability import GoalGap, CapabilityContract, AcceptanceMetric, Observation, evaluate_capability
from veriarbor.graph import evaluate_graph
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
        self.assertEqual(reduce_obligations(requirements, {'leaf': ['VERIFIED']})['hard_verdict'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(reduce_obligations(requirements, {'root': ['VERIFIED'], 'leaf': ['VERIFIED']})['hard_verdict'], 'VERIFIED')

    def test_information_and_removed_failures_are_not_goal_progress(self):
        before = {'failed':['check'], 'acceptance':[], 'verified':[]}
        after = {'failed':[], 'acceptance':[], 'verified':['check'],
                 'evidence':['new'], 'artifact_delta_validated':True}
        first = ProgressGuidedBacktracking.assess(before, after)
        self.assertEqual(first['status'], 'INFORMATION_GAIN')
        self.assertFalse(first['goal_progress'])
        second = ProgressGuidedBacktracking.assess(after, {**after,'evidence':['new','more']}, [first])
        self.assertEqual(second['next_operation'], 'AFFECTED_SUBGRAPH_REPLAN')
        self.assertEqual(ProgressGuidedBacktracking.assess(after, after)['status'], 'NO_PROGRESS')
        self.assertTrue(ProgressGuidedBacktracking.assess(after, {**after,'acceptance':['root']})['goal_progress'])
        repair = repair_progress(['check'], [], 's')
        self.assertEqual(repair['newly_verified_ids'], [])
        self.assertEqual(repair['status'], 'REPAIR_INFORMATION_GAIN')
        self.assertEqual(repair['next_operation'], 'INSPECT')
        self.assertEqual(repair_progress(['check'], [], 'different', [repair])['code'], 'REPEATED_REPAIR_NO_PROGRESS')
        self.assertEqual(repair_progress(['check'], [], 's', verified=['check'])['status'], 'REPAIR_PROGRESS')

    def test_qualified_utility_regression_dominates_technical_and_proxy_gain(self):
        c = CapabilityContract('A', 'Supply a useful result', parent_goal='root',
            semantic_invariants=('valid',), acceptance_metrics=(AcceptanceMetric('quality', '>=', .9),))
        evidence = replace(self.evidence, scope={'PROJECT':'p','CAPABILITY':'A'},
                           context={'contract_hash':c.fingerprint})
        observations = {k:Observation(True,evidence) for k in ('implemented','executed','valid')}
        observations['quality'] = Observation(.3,evidence)
        gates = evaluate_capability(c, observations, project_id='p', strategy_capabilities=('method',), **self.bindings)
        self.assertEqual(gates.semantic_status, 'PASS')
        self.assertEqual(gates.utility_status, 'FAIL')
        gap = GoalGap('quality-gap','root','quality',.9,.7,capability_ids=('A',))
        before = {'gaps':{'quality-gap':gap},'verified':[]}
        after = {'gaps':{'quality-gap':replace(gap,current=observations['quality'].actual)},
                 'verified':['technical','proxy'], 'evidence':['more']}
        advice = ProgressGuidedBacktracking.assess(before, after)
        self.assertEqual(advice['status'], 'REGRESSION')
        self.assertEqual(advice['regressed_gap_ids'], ['quality-gap'])
        self.assertFalse(advice['goal_progress'])
        self.assertEqual(ProgressGuidedBacktracking.assess(after, before)['status'], 'PROGRESS')
        # A shifted target is not a matched utility improvement.
        changed = {'gaps':{'quality-gap':replace(gap,current=.8,target=.1)}}
        self.assertFalse(ProgressGuidedBacktracking.assess(before,changed)['goal_progress'])
        # A utility decline remains a decline even when both values meet the threshold.
        self.assertEqual(ProgressGuidedBacktracking.assess(
            {'gaps':{'quality-gap':replace(gap,current=1.0)}},
            {'gaps':{'quality-gap':replace(gap,current=.95)}})['status'], 'REGRESSION')
        cost = replace(gap, comparison='<=', target=.5, current=.8)
        self.assertEqual(ProgressGuidedBacktracking.assess({'gaps':{'cost':cost}},
            {'gaps':{'cost':replace(cost,current=.6)}})['status'], 'PROGRESS')

    def test_upstream_gap_survives_downstream_pass_and_backtracks(self):
        nodes = [Node('input',NodeKind.EXECUTION_LEAF),
                 Node('A',NodeKind.EXECUTION_LEAF,dependencies=('input',)),
                 Node('B',NodeKind.EXECUTION_LEAF,dependencies=('A',)),
                 Node('root',NodeKind.OBLIGATION_AND,children=('B',))]
        checks = {n.id:{'acceptance':self.evidence,'integration':self.evidence} for n in nodes}
        checks['root']['acceptance'] = None
        checks['A']['acceptance'] = replace(self.evidence,verdict='FAILED')
        results = evaluate_graph(nodes,checks,**self.bindings)
        self.assertEqual(results['A'].status,Status.FAILED)
        self.assertEqual(results['B'].status,Status.BLOCKED)
        self.assertNotEqual(results['root'].status,Status.VERIFIED)
        dependencies = {n.id:n.dependencies for n in nodes}
        statuses = {k:r.status for k,r in results.items()}
        self.assertIn('A',ready_frontier(statuses,statuses,dependencies))
        checkpoints = [DecisionCheckpoint('supply',1,('A',),'before-A'),
                       DecisionCheckpoint('polish',2,('B',),'before-B')]
        self.assertEqual(backtrack([k for k,r in results.items() if r.status==Status.FAILED],checkpoints).id,'supply')
        checks['A']['acceptance'] = None
        results = evaluate_graph(nodes,checks,**self.bindings)
        self.assertEqual(results['A'].status,Status.UNPROVEN)
        self.assertIsNone(backtrack([k for k,r in results.items() if r.status==Status.FAILED],checkpoints))
        gap = GoalGap('unknown-A','root','quality',1,None,capability_ids=('A',))
        self.assertEqual(ProgressGuidedBacktracking.assess({}, {'gaps':{'unknown-A':gap}})['diagnostic_gap_ids'], ['unknown-A'])


if __name__ == '__main__':
    unittest.main()
