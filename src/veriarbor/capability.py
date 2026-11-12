"""Deterministic capability policy over host-authenticated, versioned Evidence.

No planner, executor, project store or implicit child-to-parent quality promotion.
"""
from dataclasses import asdict, dataclass, field
from enum import StrEnum
import math
import operator

from .model import Evidence, stable_hash
from .execution_authority import CriticalCheckSpec


class GateStatus(StrEnum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    UNKNOWN = 'UNKNOWN'
    NOT_TESTED = 'NOT_TESTED'
    BLOCKED = 'BLOCKED'


STAGES = ('IMPLEMENTED', 'EXECUTED', 'SEMANTIC_VERIFIED',
          'UTILITY_VERIFIED', 'GENERALIZATION_VERIFIED')
RUNTIME_STATES = ('PROPOSED', 'ADMITTED', 'EXECUTING', 'EXECUTED', 'GATED')


@dataclass(frozen=True)
class CapabilityGateState:
    implemented_status: str = 'NOT_TESTED'
    execution_status: str = 'NOT_TESTED'
    semantic_status: str = 'NOT_TESTED'
    utility_status: str = 'NOT_TESTED'
    generalization_status: str = 'NOT_TESTED'
    legacy_imported: bool = False

    def __post_init__(self):
        for name in ('implemented', 'execution', 'semantic', 'utility', 'generalization'):
            GateStatus(getattr(self, name + '_status'))

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        if value == 'ACCEPTED' or (isinstance(value, dict) and value.get('status') == 'ACCEPTED' and not value.get('gates')):
            return cls(legacy_imported=True)
        return cls(**value.get('gates', value))


@dataclass(frozen=True)
class AcceptanceMetric:
    metric_id: str
    comparison: str
    target: float | bool
    stage: str = 'UTILITY_VERIFIED'

    def __post_init__(self):
        if not self.metric_id or self.comparison not in {'>=', '<=', '=='} or self.stage not in STAGES:
            raise ValueError('invalid acceptance metric')
        if not isinstance(self.target, (int, float)) or not math.isfinite(self.target):
            raise ValueError('metric target must be finite')

    def compare(self, actual):
        if (not isinstance(actual, (int, float)) or not math.isfinite(actual)
                or isinstance(actual, bool) != isinstance(self.target, bool)):
            return 'UNKNOWN'
        return 'PASS' if {'>=': operator.ge, '<=': operator.le, '==': operator.eq}[self.comparison](actual, self.target) else 'FAIL'


@dataclass(frozen=True)
class CapabilityContract:
    capability_id: str
    semantic_goal: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    parent_goal: str = ''
    forbidden_substitutes: tuple[str, ...] = ()
    acceptance_metrics: tuple[AcceptanceMetric, ...] = ()
    semantic_invariants: tuple[str, ...] = ()
    positive_controls: tuple[str, ...] = ()
    negative_controls: tuple[str, ...] = ()
    failure_conditions: tuple[str, ...] = ()
    evidence_requirements: dict = field(default_factory=dict)
    generalization_requirement: dict = field(default_factory=dict)
    critical: bool = True
    critical_checks: tuple[CriticalCheckSpec, ...] = ()
    requires_claim_support: bool = False
    conflict_collection: bool = False
    claim_unknown_policy: str = 'BLOCK'
    independence_policy: dict = field(default_factory=dict)

    def __post_init__(self):
        for key in ('inputs','outputs','forbidden_substitutes','semantic_invariants',
                    'positive_controls','negative_controls','failure_conditions'):
            object.__setattr__(self,key,tuple(getattr(self,key)))
        object.__setattr__(self, 'critical_checks', tuple(
            CriticalCheckSpec(**c) if isinstance(c, dict) else c for c in self.critical_checks))
        if len({c.check_id for c in self.critical_checks}) != len(self.critical_checks):
            raise ValueError('duplicate critical check id')
        if self.claim_unknown_policy not in {'BLOCK','ALLOW_WITH_WARNING'}:
            raise ValueError('invalid claim unknown policy')
        object.__setattr__(self, 'acceptance_metrics', tuple(
            AcceptanceMetric(**m) if isinstance(m, dict) else m for m in self.acceptance_metrics))
        ids = [m.metric_id for m in self.acceptance_metrics]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate metric id')

    @property
    def fingerprint(self):
        value = asdict(self)
        if not self.critical_checks:
            value.pop('critical_checks')  # Preserve old serialized contract identity.
        else:
            for spec in value['critical_checks']:
                for key,default in [('expected_version',None),('minimum_version',None),('policy_hash',None),('schema_version','1')]:
                    if spec[key]==default:spec.pop(key)
        for key,default in [('requires_claim_support',False),('conflict_collection',False),
                            ('claim_unknown_policy','BLOCK'),('independence_policy',{})]:
            if value[key]==default:value.pop(key)
        return stable_hash(value)

    @property
    def measurable(self):
        return bool(self.critical_checks or self.acceptance_metrics or self.semantic_invariants or self.positive_controls or self.negative_controls)


def validate_evidence(evidence, *, consumer, required_scope=None, required_context=None,
                      required_metadata=(), required_context_hash=None):
    """An allow-list is restrictive when present; an explicit deny always wins."""
    if consumer in evidence.forbidden_for or (evidence.usable_for and consumer not in evidence.usable_for):
        return 'PORT_EVIDENCE_SCOPE_REJECT'
    if any(not getattr(evidence, key, None) for key in required_metadata):
        return 'PORT_EVIDENCE_SCOPE_REJECT'
    if any(evidence.scope.get(k) != v for k, v in (required_scope or {}).items()):
        return 'PORT_EVIDENCE_SCOPE_REJECT'
    if required_context_hash is not None and evidence.context.get('artifact_hash') != required_context_hash:
        return 'CONTEXT_BINDING_REJECT'
    if any(evidence.context.get(k) != v for k, v in (required_context or {}).items()):
        return 'CONTEXT_BINDING_REJECT'
    return 'VALID'


@dataclass(frozen=True)
class Observation:
    actual: float | bool
    evidence: Evidence


def evaluate_capability(contract, observations, *, project_id, object_versions,
                        checker_versions, strategy_capabilities=(), critical_check_results=()):
    """Observation keys: implemented, executed, metric IDs and control IDs.

    Control observations mean 'control behaved as specified', including rejection
    of negative controls. Failure-condition observations mean the failure occurred.
    Each observation is bound to this project, capability and contract revision.
    """
    def read(key, stage):
        obs = observations.get(key)
        if obs is None:
            return None, 'NOT_TESTED'
        e = obs.evidence
        requirements = dict(contract.evidence_requirements)
        requirements.pop('allow_imported_unmanaged', None)
        scope = {**requirements.pop('required_scope', {}), 'PROJECT': project_id,
                 'CAPABILITY': contract.capability_id}
        context = {**requirements.pop('required_context', {}), 'contract_hash': contract.fingerprint}
        if stage == 'GENERALIZATION_VERIFIED':
            context.update(contract.generalization_requirement)
        if (not e.current(object_versions, checker_versions)
                or e.verdict not in {'VERIFIED', 'FAILED'}
                or validate_evidence(e, consumer=stage, required_scope=scope,
                                     required_context=context, **requirements) != 'VALID'):
            return None, 'UNKNOWN'
        if e.verdict == 'FAILED':
            return obs.actual, 'FAIL'
        return obs.actual, 'PASS'

    def boolean(key, stage, expected=True):
        value, status = read(key, stage)
        return status if status != 'PASS' else ('PASS' if value is expected else 'FAIL')

    def combine(values):
        if not values:
            return 'NOT_TESTED'
        for status in ('FAIL', 'BLOCKED', 'UNKNOWN', 'NOT_TESTED'):
            if status in values:
                return status
        return 'PASS'

    stages = {s: [] for s in STAGES}
    stages['IMPLEMENTED'].append(boolean('implemented', 'IMPLEMENTED'))
    stages['EXECUTED'].append(boolean('executed', 'EXECUTED'))
    for m in contract.acceptance_metrics:
        value, status = read(m.metric_id, m.stage)
        stages[m.stage].append(m.compare(value) if status == 'PASS' else status)
    for key in (*contract.semantic_invariants, *contract.positive_controls, *contract.negative_controls):
        stages['SEMANTIC_VERIFIED'].append(boolean(key, 'SEMANTIC_VERIFIED'))
    for key in contract.failure_conditions:
        stages['SEMANTIC_VERIFIED'].append(boolean(key, 'SEMANTIC_VERIFIED', False))
    checked = {r['check_id']: r for r in critical_check_results}
    for spec in contract.critical_checks:
        result = checked.get(spec.check_id)
        status = result.get('status') if result and result.get('checker_id') == spec.checker_id else 'NOT_TESTED'
        stages['SEMANTIC_VERIFIED'].append(status if status in {'PASS','FAIL','UNKNOWN','NOT_TESTED'} else 'UNKNOWN')
    if not strategy_capabilities:
        stages['SEMANTIC_VERIFIED'].append('UNKNOWN')
    elif set(strategy_capabilities) & set(contract.forbidden_substitutes):
        stages['SEMANTIC_VERIFIED'].append('FAIL')
    # Generalization must have a frozen context specification, never just a score.
    if not contract.generalization_requirement and stages['GENERALIZATION_VERIFIED']:
        stages['GENERALIZATION_VERIFIED'].append('UNKNOWN')
    statuses = [combine(stages[s]) for s in STAGES]
    for i in range(1, len(statuses)):
        if statuses[i] == 'PASS' and statuses[i - 1] != 'PASS':
            statuses[i] = 'BLOCKED'
    return CapabilityGateState(*statuses)


@dataclass(frozen=True)
class GoalGap:
    gap_id: str
    goal_id: str
    metric_id: str
    target: float
    current: float | None
    status: str = 'OPEN'
    root_impact: float = 1.0
    evidence_confidence: float = 1.0
    severity: float = 1.0
    comparison: str = '>='
    capability_ids: tuple[str, ...] = ()

    def __post_init__(self):
        AcceptanceMetric(self.metric_id, self.comparison, self.target)
        for number in (self.root_impact, self.evidence_confidence, self.severity):
            if not math.isfinite(number) or not 0 <= number <= 1:
                raise ValueError('gap weights must be in [0, 1]')
        if self.current is not None and not math.isfinite(self.current):
            raise ValueError('non-finite gap')

    @property
    def priority(self):
        if self.status != 'OPEN' or self.current is None:
            return 0.0
        delta = (self.target - self.current if self.comparison == '>=' else
                 self.current - self.target if self.comparison == '<=' else abs(self.target - self.current))
        return max(0, delta) / max(abs(self.target), 1e-9) * self.root_impact * self.evidence_confidence * self.severity


def admit_capability(proposal, contracts, gaps, *, budget_allowed, evidence_inputs=()):
    """Structured policy used by the existing host Proposal Admission."""
    target = proposal.get('target_capability_id') or proposal.get('satisfies_capability')
    if not target or target not in contracts:
        return 'REJECT_UNKNOWN_CAPABILITY_CONTRACT'
    c = contracts[target]
    if c.capability_id != target:
        return 'REJECT_UNKNOWN_CAPABILITY_CONTRACT'
    if not c.semantic_goal.strip() or not c.measurable:
        return 'REJECT_UNMEASURABLE_CAPABILITY'
    if c.critical and not (c.critical_checks or c.failure_conditions or c.acceptance_metrics or c.negative_controls):
        return 'REJECT_NON_FALSIFIABLE'
    strategies = set(proposal.get('strategy_capabilities', ()))
    if strategies & set(c.forbidden_substitutes):
        return 'ANTI_SUBSTITUTION_REJECT'
    if not strategies:
        return 'REJECT_UNDECLARED_STRATEGY'
    gap = gaps.get(proposal.get('target_gap_id'))
    linked = gap is not None and gap.status == 'OPEN' and target in gap.capability_ids
    exploration = proposal.get('exploration_reason', '').strip()
    bounded = proposal.get('exploration_budget')
    if not linked and not (not proposal.get('target_gap_id') and exploration and
                           type(bounded) in (int, float) and math.isfinite(bounded) and bounded > 0
                           and proposal.get('exploration_measure')):
        return 'REJECT_NO_GOAL_LINK'
    if not budget_allowed:
        return 'BUDGET_BLOCKED'
    for evidence, requirements in evidence_inputs:
        result = validate_evidence(evidence, **requirements)
        if result != 'VALID':
            return result
    return 'ADMITTED'


def close_feedback(resource_decisions, repair_traces, *, capability_id, gates,
                   artifact_after=None, acceptance_delta=None, permit_id=None):
    """Pure closure; the host persists both updated collections in one snapshot."""
    failed = 'FAIL' in (gates.implemented_status, gates.execution_status, gates.semantic_status, gates.utility_status,
                       gates.generalization_status)
    accepted = gates.semantic_status == gates.utility_status == 'PASS'
    if not failed and not accepted:
        return list(resource_decisions), list(repair_traces)
    result = 'FAILED' if failed else 'ACCEPTED'
    attribution = ('UTILITY_FAILED' if gates.utility_status == 'FAIL' else
                   'CAPABILITY_FAILED' if failed else None)
    resources = [dict(row, acceptance_result=result, utility_result=gates.utility_status,
                      failure_attribution=attribution) if row.get('capability_id') == capability_id
                      and (permit_id is None or row.get('permit_id')==permit_id) else dict(row)
                 for row in resource_decisions]
    repairs = [dict(row, artifact_after=artifact_after, acceptance_delta=acceptance_delta,
                    final_result=result) if row.get('capability_id') == capability_id
                    and (permit_id is None or row.get('new_permit')==permit_id) else dict(row)
               for row in repair_traces]
    return resources, repairs
