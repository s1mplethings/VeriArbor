from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from veriarbor.capability import (AcceptanceMetric, CapabilityContract, CapabilityGateState,
    GoalGap, Observation, admit_capability, close_feedback, evaluate_capability, validate_evidence)
from veriarbor.model import Evidence
from veriarbor.port import Port
from veriarbor.compatibility import compare_ports
from veriarbor.contract import Contract
from veriarbor.skills import (SkillCandidateGenerator, SkillManifest, SkillMatcher, SkillRegistry,
                             SkillValidation, promotion_check)


def contract():
    return CapabilityContract('specialization', 'Improve held-out ranking for the parent goal',
        parent_goal='clip_quality', forbidden_substitutes=('transcript.vocabulary_correction',),
        acceptance_metrics=(AcceptanceMetric('human_quality_delta', '>=', 0.0),),
        semantic_invariants=('profile_influence',), positive_controls=('target',),
        negative_controls=('tts_rejected',), failure_conditions=('wrong_speaker',))


def observations(c, delta=-0.2):
    evidence = Evidence('VERIFIED', {'artifact': 'v1'}, {'checker': 'v1'}, ('fixture:anny',), True,
        source_type='synthetic_replay', confidence=1.0,
        scope={'PROJECT': 'p', 'CAPABILITY': c.capability_id},
        producer='offline-checker', producer_version='v1', context={'contract_hash': c.fingerprint})
    values = {'implemented': True, 'executed': True, 'profile_influence': True,
              'target': True, 'tts_rejected': True, 'wrong_speaker': False,
              'human_quality_delta': delta}
    return {key: Observation(value, evidence) for key, value in values.items()}


def evaluate(c, obs):
    return evaluate_capability(c, obs, project_id='p', object_versions={'artifact': 'v1'},
                               checker_versions={'checker': 'v1'}, strategy_capabilities=('profile.ranking',))


def manifest(index=0, family='media_ingest'):
    return SkillManifest(f'ingest-{index:02}', '1', family, 'Ingest media with validated boundaries', 'p',
        inputs=('media',), outputs=('segments',),
        strategy_steps=({'operation': 'add_node', 'node_id': 'ingest',
                         'payload': {'capability_ref': 'ingest@1', 'config': {}}},),
        block_refs=('ingest@1',), port_contract_refs=('media.port',),
        capability_contract_refs=('ingest',), acceptance_refs=('ingest.acceptance',),
        dependency_versions={'ingest@1': '1'},
        dependency_contract_hashes={'media.port': 'A', 'ingest': 'A'},
        created_from_tree_branch='branch:ingest')


def validations(m, gates=None):
    return [SkillValidation(str(i), 'p', f'context-{i}', m.strategy_hash,
             gates or CapabilityGateState('PASS', 'PASS', 'PASS', 'PASS', 'PASS'),
             (f'receipt:{i}',), True, True) for i in range(2)]


class CapabilityTests(unittest.TestCase):
    def test_port_policy_preserves_legacy_hash_and_rejects_incompatible_scope(self):
        from veriarbor.model import stable_hash
        old = Port('profile', '1', 'input', Contract.create({'type': 'object'}, 'profile evidence'))
        legacy = asdict(old)
        legacy.pop('evidence_policy')
        self.assertEqual(old.fingerprint, stable_hash(legacy))
        bound = replace(old, evidence_policy={'required_scope': {'PROJECT': 'p'}, 'required_context_hash': 'A'})
        self.assertEqual(compare_ports(old, bound), 'BREAKING')
        e = Evidence('VERIFIED', {}, {}, (), scope={'PROJECT': 'p'}, context={'artifact_hash': 'B'})
        self.assertEqual(bound.validate_evidence(e), 'CONTEXT_BINDING_REJECT')
        self.assertEqual(bound.validate_evidence(replace(e, scope={'PROJECT': 'other'})), 'PORT_EVIDENCE_SCOPE_REJECT')

    def test_nonfinite_and_boolean_metrics_fail_closed(self):
        metric = AcceptanceMetric('score', '>=', 0.5)
        self.assertEqual(metric.compare(float('nan')), 'UNKNOWN')
        self.assertEqual(metric.compare(float('inf')), 'UNKNOWN')
        self.assertEqual(metric.compare(True), 'UNKNOWN')
        self.assertEqual(AcceptanceMetric('invariant', '==', True).compare(False), 'FAIL')

    def test_anti_substitution(self):
        c = replace(contract(), capability_id='speaker.identification')
        code = admit_capability({'target_capability_id': c.capability_id,
            'strategy_capabilities': ['transcript.vocabulary_correction']}, {c.capability_id: c}, {}, budget_allowed=True)
        self.assertEqual(code, 'ANTI_SUBSTITUTION_REJECT')

    def test_multi_stage_utility_failure_and_parent(self):
        c = contract()
        gates = evaluate(c, observations(c))
        self.assertEqual(gates, CapabilityGateState('PASS', 'PASS', 'PASS', 'FAIL'))
        parent = replace(c, capability_id='clip_quality')
        # Even a child's qualified success cannot establish a parent's outcome.
        self.assertEqual(evaluate(parent, observations(c, 0.2)).utility_status, 'UNKNOWN')

    def test_negative_control_failure(self):
        c = contract()
        obs = observations(c, 0.2)
        obs['tts_rejected'] = replace(obs['tts_rejected'], actual=False)
        gates = evaluate(c, obs)
        self.assertEqual(gates.semantic_status, 'FAIL')
        self.assertEqual(gates.utility_status, 'BLOCKED')

    def test_evidence_scope(self):
        e = Evidence('VERIFIED', {}, {}, (), forbidden_for=('stable_creator_profile',),
                     usable_for=('search_candidate',), context={'speaker_role': 'UNKNOWN'})
        self.assertEqual(validate_evidence(e, consumer='stable_creator_profile'), 'PORT_EVIDENCE_SCOPE_REJECT')
        self.assertEqual(validate_evidence(e, consumer='search_candidate'), 'VALID')
        self.assertEqual(validate_evidence(e, consumer='other'), 'PORT_EVIDENCE_SCOPE_REJECT')
        self.assertEqual(validate_evidence(e, consumer='search_candidate', required_metadata=('producer',)),
                         'PORT_EVIDENCE_SCOPE_REJECT')

    def test_frozen_context_binding(self):
        e = Evidence('VERIFIED', {}, {}, (), context={'artifact_hash': 'B'})
        self.assertEqual(validate_evidence(e, consumer='moment', required_context_hash='A'), 'CONTEXT_BINDING_REJECT')

    def test_goal_gap_and_exploration(self):
        c = contract()
        gap = GoalGap('quality', 'clip_quality', 'quality', 1, 0.5, capability_ids=(c.capability_id,))
        p = {'target_capability_id': c.capability_id, 'strategy_capabilities': ['profile.ranking']}
        check = lambda value: admit_capability(value, {c.capability_id: c}, {'quality': gap}, budget_allowed=True)
        self.assertEqual(check(p), 'REJECT_NO_GOAL_LINK')
        self.assertEqual(check(dict(p, target_gap_id='gui')), 'REJECT_NO_GOAL_LINK')
        self.assertEqual(check(dict(p, target_gap_id='quality')), 'ADMITTED')
        self.assertEqual(check(dict(p, exploration_reason='investigate')), 'REJECT_NO_GOAL_LINK')
        self.assertEqual(check(dict(p, exploration_reason='investigate', exploration_budget=2,
                                    exploration_measure='human_quality_delta')), 'ADMITTED')
        self.assertEqual(gap.priority, 0.5)
        self.assertEqual(replace(gap, comparison='<=', current=1.5).priority, 0.5)

    def test_unmeasurable_and_nonfalsifiable(self):
        c = CapabilityContract('c', 'goal')
        p = {'target_capability_id': 'c'}
        self.assertEqual(admit_capability(p, {'c': c}, {}, budget_allowed=True), 'REJECT_UNMEASURABLE_CAPABILITY')
        self.assertEqual(admit_capability(p, {'c': replace(c, positive_controls=('yes',))}, {}, budget_allowed=True),
                         'REJECT_NON_FALSIFIABLE')

    def test_legacy_compatibility(self):
        for old in ('ACCEPTED', {'status': 'ACCEPTED'}):
            gates = CapabilityGateState.from_dict(old)
            self.assertTrue(gates.legacy_imported)
            self.assertEqual(gates.utility_status, 'NOT_TESTED')
            self.assertEqual(gates.generalization_status, 'NOT_TESTED')

    def test_resource_and_repair_closure(self):
        c = contract()
        rows = [{'capability_id': c.capability_id, 'acceptance_result': 'PENDING'}, {'capability_id': 'other'}]
        repairs = [{'capability_id': c.capability_id, 'final_result': 'pending'}]
        resources, traces = close_feedback(rows, repairs, capability_id=c.capability_id,
            gates=evaluate(c, observations(c)), artifact_after='sha:after', acceptance_delta={'quality': -0.2})
        self.assertEqual(resources[0]['acceptance_result'], 'FAILED')
        self.assertEqual(resources[0]['utility_result'], 'FAIL')
        self.assertEqual(resources[1], rows[1])
        self.assertEqual(traces[0]['final_result'], 'FAILED')
        self.assertEqual(traces[0]['artifact_after'], 'sha:after')
        self.assertEqual(rows[0]['acceptance_result'], 'PENDING')

    def test_anny_synthetic_replay(self):
        fixture = json.loads((Path(__file__).parents[1] / 'fixtures/anny_ranking_replay.json').read_text())
        c = contract()
        obs = observations(c, fixture['specialized_metric'] - fixture['generic_metric'])
        self.assertTrue(fixture['profile_influence'])
        self.assertEqual(evaluate(c, obs).semantic_status, 'PASS')
        self.assertEqual(evaluate(c, obs).utility_status, 'FAIL')

    def test_evidence_current_and_contract_bound(self):
        c = contract()
        for evidence_change in ({'qualified': False}, {'object_versions': {'artifact': 'old'}},
                                {'scope': {'PROJECT': 'another', 'CAPABILITY': c.capability_id}},
                                {'context': {'contract_hash': 'old'}}):
            obs = {k: replace(v, evidence=replace(v.evidence, **evidence_change)) for k, v in observations(c).items()}
            self.assertEqual(evaluate(c, obs).semantic_status, 'UNKNOWN')

    def test_generalization_requires_bound_context(self):
        c = replace(contract(), acceptance_metrics=(AcceptanceMetric('human_quality_delta', '>=', 0.0),
            AcceptanceMetric('heldout', '>=', 0.8, 'GENERALIZATION_VERIFIED')),
            generalization_requirement={'heldout_hash': 'A'})
        obs = observations(c, 0.1)
        obs['heldout'] = Observation(0.9, obs['executed'].evidence)
        self.assertEqual(evaluate(c, obs).generalization_status, 'UNKNOWN')
        obs['heldout'] = replace(obs['heldout'], evidence=replace(obs['heldout'].evidence,
            context={'contract_hash': c.fingerprint, 'heldout_hash': 'A'}))
        self.assertEqual(evaluate(c, obs).generalization_status, 'PASS')


class SkillTests(unittest.TestCase):
    def test_candidate_generation(self):
        m = manifest()
        with tempfile.TemporaryDirectory() as folder:
            result = SkillCandidateGenerator(execution_mode='LEGACY').generate(m, validations(m), folder)
            self.assertEqual(result.status, 'CANDIDATE')
            self.assertEqual(SkillManifest(**json.loads((Path(folder) / 'skill.json').read_text())).status, 'CANDIDATE')
            self.assertIn('historical success grants no PASS', (Path(folder) / 'SKILL.md').read_text())
            self.assertIsNone(result.token_metrics.planning_tokens_with_skill)

    def test_immature_single_and_duplicate_success_rejected(self):
        m = manifest()
        for receipts in (validations(m, CapabilityGateState('PASS', 'PASS')),
                         validations(m)[:1], [validations(m)[0]] * 3):
            with tempfile.TemporaryDirectory() as folder:
                with self.assertRaisesRegex(ValueError, 'SKILL_PROMOTION_REJECT'):
                    SkillCandidateGenerator(execution_mode='LEGACY').generate(m, receipts, folder)
        self.assertFalse(promotion_check(m, [replace(v, evidence_refs=('same-receipt',)) for v in validations(m)], execution_mode='LEGACY'))

    def test_lazy_load_and_invalidation(self):
        with tempfile.TemporaryDirectory() as folder:
            registry = SkillRegistry(folder, execution_mode='LEGACY')
            for i in range(20):
                m = manifest(i, 'media_ingest' if i < 5 else 'other')
                registry.register(replace(m, status='VERIFIED'), validations(m))
            matcher = SkillMatcher(registry)
            task = dict(project_id='p', task_family='media_ingest', capability_id='ingest',
                        inputs=('media',), outputs=('segments',), dependency_versions={'ingest@1': '1'},
                        dependency_contract_hashes={'media.port': 'A', 'ingest': 'A'})
            with patch.object(registry, 'lookup', wraps=registry.lookup) as lookup:
                loaded = matcher.load(**task)
                self.assertEqual(len(loaded), 3)
                self.assertEqual(lookup.call_count, 3)
            self.assertEqual(matcher.load(**dict(task, project_id='other')), [])
            self.assertEqual(matcher.load(**dict(task, dependency_contract_hashes={'media.port': 'B', 'ingest': 'A'})), [])
            self.assertTrue(all(row['status'] == 'NEEDS_REVALIDATION' for row in registry.index()
                                if row['task_family'] == 'media_ingest'))
            self.assertTrue(all(row['status'] == 'VERIFIED' for row in registry.index()
                                if row['task_family'] == 'other'))
            registry.invalidate({'ingest@1': '1'}, {'media.port': 'B', 'ingest': 'A'})
            self.assertTrue(all(row['status'] == 'NEEDS_REVALIDATION' for row in registry.index()))

    def test_promotion_and_shared_isolation(self):
        m = manifest()
        with tempfile.TemporaryDirectory() as folder:
            registry = SkillRegistry(folder, execution_mode='LEGACY')
            registry.register(m)
            with self.assertRaisesRegex(ValueError, 'SKILL_PROMOTION_REJECT'):
                registry.update_status(m.skill_id, m.version, 'VERIFIED')
            registry.update_status(m.skill_id, m.version, 'VERIFIED', validations(m))
            self.assertEqual(registry.lookup(m.skill_id, m.version).status, 'VERIFIED')
        shared = replace(m, scope='SHARED', project_id='')
        self.assertTrue(promotion_check(shared, validations(shared), execution_mode='LEGACY'))
        same_context = [replace(v, context_id='same') for v in validations(shared)]
        self.assertFalse(promotion_check(shared, same_context, execution_mode='LEGACY'))
        with self.assertRaises(ValueError):
            replace(shared, private_assumptions=('local path',))

    def test_dependency_and_strategy_changes_prevent_promotion(self):
        m = manifest()
        self.assertFalse(promotion_check(replace(m, dependency_versions={}), validations(m), execution_mode='LEGACY'))
        self.assertFalse(promotion_check(replace(m, strategy_steps=({'operation': 'retry_node', 'node_id': 'x'},)), validations(m), execution_mode='LEGACY'))


if __name__ == '__main__':
    unittest.main()
