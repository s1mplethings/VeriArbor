"""Small versioned governance protocols; no business algorithms or scheduler."""
from dataclasses import dataclass, field
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
import math

from .execution_authority import ImmutableRecord, utc_now


class GovernanceError(ValueError):
    def __init__(self, code, detail=''):
        self.code = str(code)
        super().__init__(self.code + (': ' + detail if detail else ''))


class ErrorCode(StrEnum):
    ADMISSION_REQUIRED='ADMISSION_REQUIRED'
    TREE_COMMIT_REQUIRED='TREE_COMMIT_REQUIRED'
    PERMIT_REQUIRED='PERMIT_REQUIRED'
    PERMIT_MISMATCH='PERMIT_MISMATCH'
    PERMIT_EXPIRED='PERMIT_EXPIRED'
    PERMIT_CONSUMED='PERMIT_CONSUMED'
    UNAUTHORIZED_EFFECT='UNAUTHORIZED_EFFECT'
    INPUT_BINDING_REJECT='INPUT_BINDING_REJECT'
    OUTPUT_BINDING_REJECT='OUTPUT_BINDING_REJECT'
    POST_HOC_OUTPUT_REJECT='POST_HOC_OUTPUT_REJECT'
    CRITICAL_CHECK_BLOCKED='CRITICAL_CHECK_BLOCKED'
    REQUIRED_CHECKER_MISSING='REQUIRED_CHECKER_MISSING'
    CHECKER_IDENTITY_MISMATCH='CHECKER_IDENTITY_MISMATCH'
    CLAIM_SUPPORT_REQUIRED='CLAIM_SUPPORT_REQUIRED'
    CLAIM_CONTRADICTED='CLAIM_CONTRADICTED'
    INDEPENDENCE_POLICY_VIOLATION='INDEPENDENCE_POLICY_VIOLATION'
    EVALUATION_SCOPE_VIOLATION='EVALUATION_SCOPE_VIOLATION'
    BUDGET_EXCEEDED='BUDGET_EXCEEDED'
    RESOURCE_DECISION_UNCLOSED='RESOURCE_DECISION_UNCLOSED'
    COMMIT_RECEIPT_REQUIRED='COMMIT_RECEIPT_REQUIRED'
    RECEIPT_INVALID='RECEIPT_INVALID'
    AUTHORITY_INTEGRITY_FAILURE='AUTHORITY_INTEGRITY_FAILURE'
    LEGACY_NOT_ALLOWED='LEGACY_NOT_ALLOWED'


@dataclass(frozen=True)
class ClaimEvidenceRelation(ImmutableRecord):
    relation_id: str
    claim_ref: str
    evidence_refs: tuple
    relation: str
    checker_identity: dict
    scope: dict
    reason_code: str
    confidence: float | None = None
    rationale_ref: str | None = None
    created_at: str = field(default_factory=utc_now)
    schema_version: str = '1'

    def __post_init__(self):
        super().__post_init__()
        if self.relation not in {'SUPPORTS','CONTRADICTS','INSUFFICIENT','UNKNOWN'}:
            raise GovernanceError('CLAIM_SUPPORT_REQUIRED','unknown relation')
        if not self.relation_id or not self.claim_ref or not self.reason_code:
            raise ValueError('relation identity/reason required')
        if self.confidence is not None and (not math.isfinite(self.confidence) or not 0<=self.confidence<=1):
            raise ValueError('invalid relation confidence')


@dataclass(frozen=True)
class EvidenceDerivation(ImmutableRecord):
    record_id: str
    source_record_ids: tuple = ()
    underlying_event_id: str | None = None
    independence_key: str | None = None
    derivation_type: str = 'DIRECT'
    scope: dict = field(default_factory=dict)
    schema_version: str = '1'

    def __post_init__(self):
        super().__post_init__()
        if not self.record_id or self.derivation_type not in {'DIRECT','DERIVED','DUPLICATE','FUSED','AGGREGATED'}:
            raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','invalid derivation')


def independence_summary(records, policy=None):
    policy=policy or {};records=tuple(EvidenceDerivation(**r) if isinstance(r,dict) else r for r in records)
    by_id={r.record_id:r for r in records}
    if len(by_id)!=len(records):raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','duplicate record_id')
    groups={};pending=set()
    def keys(record):
        if record.record_id in pending:raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','cyclic derivation')
        if any(record.scope.get(k)!=v for k,v in policy.get('required_scope',{}).items()):
            raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','scope mismatch')
        if record.source_record_ids and record.derivation_type!='DIRECT':
            pending.add(record.record_id)
            result=set()
            for ref in record.source_record_ids:
                if ref not in by_id:raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','missing source identity')
                result.update(keys(by_id[ref]))
            pending.remove(record.record_id)
            return result
        if record.underlying_event_id:return {'event:'+record.underlying_event_id}
        if record.independence_key:return {'key:'+record.independence_key}
        raise GovernanceError('INDEPENDENCE_POLICY_VIOLATION','missing independence identity')
    for record in records:
        for key in keys(record):groups.setdefault(key,[]).append(record.record_id)
    return dict(record_count=len(records),independent_count=len(groups),groups=groups,schema_version='1')


def count_independent(records, policy=None):
    return independence_summary(records,policy)['independent_count']


@dataclass(frozen=True)
class InputBinding(ImmutableRecord):
    """Entry in existing Permit.input_bindings; not another input store."""
    artifact_ref: str
    path: str
    sha256: str
    consumer: str
    context: dict = field(default_factory=dict)
    producer_receipt_id: str | None = None
    execution_mode: str = 'GOVERNED'
    requirements: dict = field(default_factory=dict)
    schema_version: str = '1'

    def __post_init__(self):
        super().__post_init__()
        if not self.artifact_ref or not self.path or not self.sha256 or not self.consumer:
            raise GovernanceError('INPUT_BINDING_REJECT','incomplete input manifest entry')
        if self.execution_mode not in {'GOVERNED','IMPORTED_UNMANAGED'}:
            raise GovernanceError('INPUT_BINDING_REJECT','invalid input scope')
        if self.execution_mode=='GOVERNED' and not self.producer_receipt_id:
            raise GovernanceError('COMMIT_RECEIPT_REQUIRED')
        if self.execution_mode=='IMPORTED_UNMANAGED' and self.producer_receipt_id:
            raise GovernanceError('INPUT_BINDING_REJECT','import cannot claim a producer receipt')


@dataclass(frozen=True)
class EvaluationScope(ImmutableRecord):
    evaluation_id: str
    population_ref: str
    sample_ref: str
    sample_hash: str
    sampling_strategy: str
    selection_mechanism: str
    selection_bias: str
    metric_scope: str
    allowed_conclusion_scope: tuple
    evaluator_identity: dict
    population_hash: str | None = None
    generalization_target: str | None = None
    created_at: str = field(default_factory=utc_now)
    schema_version: str = '1'

    def __post_init__(self):
        super().__post_init__()
        if self.sampling_strategy not in {'FULL_POPULATION','RANDOM_SAMPLE','STRATIFIED_SAMPLE','TOP_K_BIASED','DIAGNOSTIC','HUMAN_SELECTED','UNKNOWN'}:
            raise GovernanceError('EVALUATION_SCOPE_VIOLATION','unknown sampling strategy')
        if not all((self.evaluation_id,self.population_ref,self.sample_ref,self.sample_hash,self.selection_mechanism,self.metric_scope)):
            raise GovernanceError('EVALUATION_SCOPE_VIOLATION','missing scope identity')
        if isinstance(self.allowed_conclusion_scope,str):
            object.__setattr__(self,'allowed_conclusion_scope',(self.allowed_conclusion_scope,))

    def allows(self, stage, conclusion_scope):
        if conclusion_scope not in self.allowed_conclusion_scope:return False
        biased=self.sampling_strategy in {'TOP_K_BIASED','DIAGNOSTIC','HUMAN_SELECTED','UNKNOWN'}
        if biased and (stage=='GENERALIZATION_VERIFIED' or conclusion_scope not in {'DIAGNOSTIC','SAMPLE'}):return False
        if stage=='GENERALIZATION_VERIFIED' and (not self.generalization_target or not self.population_hash or self.selection_bias=='UNKNOWN'):return False
        if self.sampling_strategy=='FULL_POPULATION' and self.population_hash!=self.sample_hash:return False
        return True


@dataclass(frozen=True)
class LegacyPolicy(ImmutableRecord):
    allow_legacy_new_runs: bool = False
    allowed_callers: tuple = ()
    schema_version: str = '1'


_legacy=ContextVar('veriarbor_legacy_authorization',default=None)


@contextmanager
def legacy_scope(policy, *, caller, reason, event_sink):
    if (not policy.allow_legacy_new_runs or caller not in policy.allowed_callers
            or not reason.strip() or not callable(event_sink)):
        raise GovernanceError('LEGACY_NOT_ALLOWED')
    token=_legacy.set(dict(caller=caller,reason=reason,event_sink=event_sink))
    try:yield
    finally:_legacy.reset(token)


def require_legacy(*, project_id='NOT_APPLICABLE',run_id='NOT_APPLICABLE'):
    context=_legacy.get()
    if not context:raise GovernanceError('LEGACY_NOT_ALLOWED','explicit allowlist/reason scope required')
    event=dict(event_type='LEGACY_EXECUTION',caller=context['caller'],reason=context['reason'],
               project_id=project_id,run_id=run_id,timestamp=utc_now())
    context['event_sink'](event)
    return event
